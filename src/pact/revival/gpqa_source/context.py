"""Offline native tokenizer checks. No pretrained model or hub access."""
from pathlib import Path
from ...util import read_json,file_hash,digest
from ...backends.registry import REGISTRY
from ...backends.native import render_native
from .. import contracts as c
from . import review,contracts


def check(root,assets):
    review.validate(root)
    candidate=read_json(Path(root)/'candidate.private.json')
    lineage=read_json(Path(root)/'lineage.private.json')
    if file_hash(Path(assets['access_file']))!=lineage.get('access_hash'):raise ValueError('audited_parent_access_required')
    access=read_json(assets['access_file'])
    from transformers import AutoTokenizer
    maxima={}
    for family in 'QLMR':
        path=Path(assets['directories'][family]);receipt=access[family]
        if receipt['tokenizer_revision']!=REGISTRY[family].revision:raise ValueError('tokenizer_revision_conflict')
        for name,expected in receipt['metadata_hashes'].items():
            if Path(name).name!=name or file_hash(path/name)!=expected:raise ValueError('tokenizer_asset_conflict')
        tokenizer=AutoTokenizer.from_pretrained(path,local_files_only=True,trust_remote_code=False)
        if digest(tokenizer.chat_template)!=receipt['template_hash']:raise ValueError('template_conflict')
        class Backend:
            def render_messages(self,messages):return render_native(tokenizer,messages,REGISTRY[family])
        backend=Backend();backend.tokenizer=tokenizer
        maximum=0
        # Check fixed scaffolding, not a claim about generated peer-message lengths.
        empty=[{'status':'ok','answer':'A','justification':''} for _ in range(3)]
        for r in candidate['records']:
            requests=[c.prompt(r['task']),c.prompt(r['task'],c.envelope(empty[0],0),c.delivered(empty,0,None)),
                      c.prompt(r['task'],revised=[c.envelope(p,i) for i,p in enumerate(empty)])]
            maximum=max(maximum,max(contracts.context_check(m,backend)['input_tokens'] for m in requests))
        maxima[family]=maximum
    return {'static_tokenizer_check':'passed','max_input_tokens':maxima,'output_reservation':512,
            'context_cap':8192,'dynamic_runtime_check_required':True,'model_forwards':0}
