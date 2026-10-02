"""Official frozen model contracts for the inference-only heterogeneous diagnostic."""
from dataclasses import dataclass, asdict
from ..config import ModelConfig

@dataclass(frozen=True)
class ModelSpec:
    key: str
    repository: str
    revision: str
    thinking: bool | None = None
    template_policy: str = 'native_system_user_v1'

REGISTRY = {
    'Q': ModelSpec('Q', 'Qwen/Qwen2.5-7B-Instruct', 'a09a35458c702b33eeacc393d103063234e8bc28'),
    'L': ModelSpec('L', 'meta-llama/Llama-3.1-8B-Instruct', '0e9e39f249a16976918f6564b8830bc894c89659'),
    'M': ModelSpec('M', 'mistralai/Mistral-7B-Instruct-v0.3', 'c170c708c41dac9275d15a8fff4eca08d52bab71'),
    'R': ModelSpec('R', ModelConfig().name, ModelConfig().revision, False),
}

def registry():
    return {k: asdict(v) for k, v in REGISTRY.items()}


def render_native(tokenizer, messages, spec):
    """Use native system handling, including Mistral's system-in-first-user rule."""
    kwargs = {'enable_thinking': False} if spec.key == 'R' else {}
    # Native Llama template otherwise embeds a default date; make it explicit.
    if spec.key == 'L': kwargs['date_string'] = '02 Oct 2026'
    return tokenizer.apply_chat_template([{'role':m.role, 'content':m.content} for m in messages],
        tokenize=False, add_generation_prompt=True, **kwargs)


def generation_parameters(tokenizer, native_config, *, final=False):
    eos = native_config.get('eos_token_id', tokenizer.eos_token_id)
    ids = eos if isinstance(eos, list) else [eos]
    if not ids or any(type(i) is not int or i < 0 for i in ids):
        raise ValueError('Native EOS/end-of-turn IDs required')
    pad = tokenizer.pad_token_id
    if pad is None: pad = ids[0]  # explicit batch-one no-padding policy
    return {'max_new_tokens':64 if final else 256, 'do_sample':not final,
        'temperature':1.0 if final else .7, 'top_p':1.0 if final else .8,
        'top_k':50 if final else 20, 'min_p':None, 'typical_p':1.0,
        'epsilon_cutoff':0.0, 'eta_cutoff':0.0, 'repetition_penalty':1.0,
        'num_beams':1, 'num_return_sequences':1, 'use_cache':True,
        'bos_token_id':tokenizer.bos_token_id, 'eos_token_id':eos, 'pad_token_id':pad}
