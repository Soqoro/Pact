"""Reuse the evaluated frozen-preparation actors, including disclosed load precision."""
import dataclasses as dc
from pathlib import Path
from types import SimpleNamespace

from ..util import digest, read_json
from ..training.receiver_study import read_receiver_supervision_review, initial_recipe
from ..training.receiver_recovery import verify_loaded
from ..training.collection_config import CollectionRuntime
from ..training.scoring import CollectionBackend

SOURCE_SHA='ba84d5a85d4dd8d301ad9bcef2d6fba7f64547a19ec3b261cf45973ede9202ea'


def source_contract(bundle):
    c=read_receiver_supervision_review(Path(bundle),SOURCE_SHA)
    receipt=c['evaluation_recovery.json']; checkpoint=c['evaluation/frozen/status.json']['checkpoint']
    if (not c['evaluation/frozen/status.json']['complete'] or
        checkpoint['recovery_receipt_hash']!=digest(receipt) or
        checkpoint['effective_actor_tensor_hashes']!=receipt['effective_tensor_hashes']['frozen']):
        raise ValueError('Completed frozen-arm recovery provenance mismatch')
    parameters={}
    for row in c['report.json']['arms']['frozen']['per_task']:
        calls=[row['packet']['call']] if 'packet' in row else row['trajectory']['calls']
        for call in calls:
            import json
            params=json.loads(call['parameters_json'])
            phase='final' if call['phase']=='final' else 'packet'
            if phase in parameters and parameters[phase]!=params:raise ValueError('Historical decoding varies unexpectedly')
            parameters[phase]=params
    if set(parameters)!= {'packet','final'}:raise ValueError('Missing frozen decoding evidence')
    return {'source_bundle_sha256':SOURCE_SHA,'arm':'frozen','checkpoint':checkpoint,'recovery_receipt':receipt,
        'parameters':parameters,'initialization_design':c['plan.json']['initialization_design'],
        'initialization_references':c['plan.json']['initialization_references'],'model':c['plan.json']['model']}


def check_loaded(backend, contract):
    verify_loaded(backend,'frozen',contract['recovery_receipt'])
    want=contract['checkpoint']
    for key in ('snapshot','template_hash','runtime_fingerprint','model','revision','tokenizer_revision',
                'precision','attention','enable_thinking','generation_defaults','effective_actor_tensor_hashes'):
        if backend.identity.get(key)!=want.get(key):raise ValueError('GPQA frozen effective model identity mismatch: '+key)
    backend.assert_unchanged()


def load(plan, initialization_root, cache):
    contract=plan['frozen_arm']
    recipe=initial_recipe(contract,Path(initialization_root)) # real stored files, step90, config/weight hashes
    runtime=CollectionRuntime(digest(plan),plan['seed'])
    from ..environment import runtime_fingerprint
    if runtime_fingerprint()!=contract['checkpoint']['runtime_fingerprint']:
        raise ValueError('GPQA runtime mismatch before model loading')
    backend=CollectionBackend(runtime,Path(cache),Path(initialization_root)/'references',recipe)
    check_loaded(backend,contract)
    from safetensors.torch import load_file
    from peft import get_peft_model_state_dict
    dtypes={'backbone':str(backend.model.get_input_embeddings().weight.dtype),'actors':[]}
    for i in range(3):
        stored=load_file(str(Path(initialization_root)/'references'/f'agent{i}'/'adapter_model.safetensors'),device='cpu')
        effective=get_peft_model_state_dict(backend.model,adapter_name=f'agent{i}')
        dtypes['actors'].append({'agent':i,'stored':sorted({str(v.dtype) for v in stored.values()}),
            'loaded_effective':sorted({str(v.dtype) for v in effective.values()}),
            'load_policy':'legacy PEFT load; agent0 exact FP32; agents1/2 FP32->BF16->FP32; no correction'})
    return runtime,backend,dtypes
