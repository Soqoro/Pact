"""Small locally initialized evidence fixtures, never downloaded models."""
from pathlib import Path
from dataclasses import asdict
import zipfile
import json
from ...util import write_json,read_json,digest,file_hash,canonical
from .. import contracts as c,data,mock,neural,study,runtime,continuation
from . import evidence


class Backend(mock.Backend):
    def generation_parameters(self,req):return {'max_new_tokens':512,'do_sample':not req.deterministic}
    def generate(self,req):
        import torch
        with torch.inference_mode():return super().generate(req)


def build(base):
    import torch
    from safetensors.torch import save_file
    from ...training.checkpoints import encode_state
    base.mkdir(parents=True,exist_ok=True);parent=base/'parent'
    source=data.fixture();study.plan(parent,source);pp=read_json(parent/'plan.json')
    # No inherited attempts in this fixture; real evidence has the closed acquisition bank.
    pb=base/'parent.zip';runtime.package(parent,pb)
    root=base/'training';root.mkdir();write_json(root/'parent_plan.json',pp)
    (root/'parent-private.zip').write_bytes(pb.read_bytes())
    write_json(root/'parent_replacement_plan.json',{'historical_accounting':{}})
    p={'source':source,'amendment':continuation.AMENDMENT,'review_hash':continuation.REVIEW_HASH,'inherited_files':{}}
    mapping={};summary={'training_complete':True,'recovery_safe':True,'combined_committed_updates':768,'unknown_parent_update':continuation.AMENDMENT['unknown_parent_step']}
    for arm in c.ARMS[1:]:
        for family in c.FAMILIES:
            b=Backend(family);shapes=neural.attach(b.model)
            with torch.no_grad():
                for name,param in neural.parameters(b.model).items():
                    if name.endswith('lora_B'):param.fill_(.01 if arm==c.ARMS[1] else .02)
            values={n:v.detach().clone() for n,v in neural.parameters(b.model).items()}
            contract={'identity':{'family':family,'arm':arm,'native':b.identity,'shapes':shapes},'lora':c.LORA,'schedule':[{'epoch':1 if i<64 else 2} for i in range(128)]}
            folder=root/'training'/arm/family;cp=folder/'checkpoints/step-000128';cp.mkdir(parents=True)
            write_json(folder/'contract.json',contract)
            write_json(folder/'status.json',{'complete':True,'completed_steps':128,'planned_steps':128,'adapter_hash':neural._weights_hash(values)})
            tree,ts=encode_state({'adapters':values},torch.is_tensor)
            write_json(cp/'state.json',{'step':128,'identity':contract,'tree':tree})
            tensor_path=base/'tensors'/arm/family/'tensors.safetensors';tensor_path.parent.mkdir(parents=True);save_file(ts,str(tensor_path))
            checks={'state.json':file_hash(cp/'state.json'),'tensors.safetensors':file_hash(tensor_path)};write_json(cp/'checksums.json',checks)
            p['inherited_files'][f'training/{arm}/{family}/checkpoints/step-000128/tensors.safetensors']=checks['tensors.safetensors']
            mapping[arm+'/'+family]=str(tensor_path.absolute());b.close()
    write_json(root/'plan.json',p);write_json(root/'summary.json',summary)
    write_json(root/'access.json',{f:{'runtime_fingerprint':'fixture'} for f in 'QLMR'})
    private=base/'private.zip';sanitized=base/'sanitized.zip'
    runtime.package(root,private);runtime.package(root,sanitized,sanitized=True)
    write_json(base/'checkpoint-map.json',mapping);write_json(base/'exposure.json',{})
    return private,sanitized,mapping
