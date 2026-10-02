"""Native family inference, reusing TransformersBackend generation and token slicing."""
import dataclasses as dc
import gc
import time
from pathlib import Path
from types import SimpleNamespace
from .registry import REGISTRY, render_native, generation_parameters
from .transformers import TransformersBackend
from ..config import Limits, ModelConfig, Sampling
from ..environment import runtime_fingerprint
from ..util import digest, file_hash

METADATA = ['config.json','generation_config.json','tokenizer*','special_tokens_map.json',
            'chat_template.jinja','vocab.json','merges.txt','model.safetensors.index.json']


def metadata(key, cache, *, token=None):
    """Called only by explicit Colab preflight. No model weights fetched here."""
    from huggingface_hub import HfApi, snapshot_download, get_hf_file_metadata, hf_hub_url
    from transformers import AutoTokenizer
    import json
    spec = REGISTRY[key]
    try:
        info = HfApi().model_info(spec.repository, revision=spec.revision, token=token)
        if info.sha != spec.revision: raise ValueError('Revision mismatch')
        path = Path(snapshot_download(spec.repository, revision=spec.revision, cache_dir=str(cache),
                                     allow_patterns=METADATA, token=token))
        index = json.loads((path/'model.safetensors.index.json').read_text())
        weights = sorted(set(index['weight_map'].values()))
        # HEAD each required weight, proving gated authorization before any benchmark dispatch.
        weight_metadata = {}
        for name in weights:
            info_file = get_hf_file_metadata(hf_hub_url(spec.repository, name, revision=spec.revision), token=token)
            if info_file.commit_hash != spec.revision: raise ValueError('Weight revision changed')
            weight_metadata[name] = {'etag':info_file.etag, 'bytes':info_file.size}
        tokenizer = AutoTokenizer.from_pretrained(path, trust_remote_code=False, local_files_only=True)
        native = json.loads((path/'generation_config.json').read_text())
        from ..schemas import Message
        probe = render_native(tokenizer, (Message('system','Follow the task instructions.'),Message('user','Template preflight.')), spec)
        if not tokenizer.chat_template or not probe: raise ValueError('Missing native template')
        from transformers import GenerationConfig
        resolved = {kind:GenerationConfig(**generation_parameters(tokenizer,native,final=kind=='final')).to_dict() for kind in ('packet','final')}
        files = {p.name:file_hash(p) for p in path.iterdir() if p.is_file() and not p.name.endswith('.safetensors')}
        return {'spec':dc.asdict(spec), 'metadata_hashes':files, 'weight_files':weights,
            'weight_metadata':weight_metadata, 'template_hash':digest(tokenizer.chat_template), 'tokenizer_revision':spec.revision,
            'resolved_generation_configs':resolved,
            'parameters':{'packet':generation_parameters(tokenizer,native),
                          'final':generation_parameters(tokenizer,native,final=True)},
            'runtime_fingerprint':runtime_fingerprint(), 'access_verified':True,
            'adapters':[], 'precision':'bfloat16', 'attention':'sdpa',
            'template_probe_hash':digest(probe)}
    except Exception:
        raise RuntimeError(f'Official model access/template preflight failed for {key}; verify authorization and pinned files. No fallback.') from None


class NativeBackend(TransformersBackend):
    _resident = False

    def __init__(self, key, receipt, cache, *, token=None):
        if NativeBackend._resident: raise RuntimeError('Only one native model may be resident')
        NativeBackend._resident = True
        self.model = None
        self.tokenizer = None
        try:
            self._load(key, receipt, cache, token=token)
        except BaseException:
            self.close()
            raise

    def _load(self, key, receipt, cache, *, token=None):
        import torch
        from huggingface_hub import snapshot_download
        from transformers import AutoModelForCausalLM, AutoTokenizer, GenerationConfig
        self.spec=REGISTRY[key];self.receipt=receipt;self.torch=torch
        if receipt['spec']!=dc.asdict(self.spec) or receipt['runtime_fingerprint']!=runtime_fingerprint():
            raise ValueError('Native preflight identity/runtime changed')
        if not torch.cuda.is_available() or torch.cuda.device_count()!=1 or not torch.cuda.is_bf16_supported():
            raise RuntimeError('One BF16 CUDA GPU required; no offload/quantization fallback')
        torch.cuda.reset_peak_memory_stats();started=time.monotonic()
        path=Path(snapshot_download(self.spec.repository,revision=self.spec.revision,cache_dir=str(cache),
            allow_patterns=[*receipt['metadata_hashes'],*receipt['weight_files']],token=token))
        self.download_seconds=time.monotonic()-started
        hash_started=time.monotonic()
        hashes={name:file_hash(path/name) for name in [*receipt['metadata_hashes'],*receipt['weight_files']]}
        if any(hashes[n]!=sha for n,sha in receipt['metadata_hashes'].items()):raise ValueError('Metadata changed')
        for name, expected in receipt['weight_metadata'].items():
            if (len(expected['etag']) == 64 and hashes[name] != expected['etag']) or (path/name).stat().st_size != expected['bytes']:
                raise ValueError('Official weight file hash/size mismatch')
        self.hash_seconds=time.monotonic()-hash_started
        materialize_started=time.monotonic()
        self.tokenizer=AutoTokenizer.from_pretrained(path,trust_remote_code=False,local_files_only=True)
        if digest(self.tokenizer.chat_template)!=receipt['template_hash']:raise ValueError('Template changed')
        self.model=AutoModelForCausalLM.from_pretrained(path,trust_remote_code=False,local_files_only=True,
            torch_dtype=torch.bfloat16,attn_implementation='sdpa',device_map={'':0})
        if getattr(self.model,'peft_config',None):raise ValueError('Pristine models require no adapters')
        if getattr(self.model,'is_quantized',False) or self.model.config._attn_implementation!='sdpa':raise ValueError('Quantization/attention mismatch')
        if any(v.dtype!=torch.bfloat16 or v.device.type!='cuda' for v in self.model.parameters()):
            raise ValueError('Model dtype/device mismatch')
        for v in self.model.parameters():v.requires_grad_(False)
        self.model.eval()
        # A fresh explicit config prevents checkpoint-specific suppression/forced tokens.
        self.model.generation_config=GenerationConfig(**receipt['resolved_generation_configs']['final' if key=='R' else 'packet'])
        self.config=SimpleNamespace(model=ModelConfig(name=self.spec.repository,revision=self.spec.revision),
                                    limits=Limits(),sampling=Sampling())
        identity={**receipt,'file_hashes':hashes,'backend':'transformers_native','adapter_state':'absent'}
        self.identity={**identity,'snapshot':digest(identity)}
        self.calls=[];self.pending_call=None
        self.materialize_seconds=time.monotonic()-materialize_started
        self.load_seconds=time.monotonic()-started;self.load_allocated=torch.cuda.memory_allocated()

    def render_messages(self,messages):return render_native(self.tokenizer,messages,self.spec)
    def generation_parameters(self,request):
        return dict(self.receipt['parameters']['final' if request.deterministic else 'packet'])
    def generation_kwargs(self):return {'generation_config':self.model.generation_config}
    def resource_usage(self):
        return {**super().resource_usage(),'download_seconds':self.download_seconds,
                'file_hash_seconds':self.hash_seconds,'materialization_seconds':self.materialize_seconds}

    def close(self):
        self.model=None;self.tokenizer=None;gc.collect()
        if hasattr(self, 'torch') and self.torch.cuda.is_available(): self.torch.cuda.empty_cache()
        NativeBackend._resident = False
