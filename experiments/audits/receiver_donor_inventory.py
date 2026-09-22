"""Read-only inventory of checksummed training reviews; no generation or bank mutation.
Run from the repository root: PYTHONPATH=src python experiments/audits/receiver_donor_inventory.py
"""
import json
from collections import Counter
from pathlib import Path

from pact.protocol import trusted_input
from pact.schemas import task_from_dict
from pact.training.data import read_training_data
from pact.training.feasibility import read_review
from pact.training.receiver_study import read_receiver_supervision_review
from pact.util import canonical, digest

TARGET=('qwen3-receiver-supervision-001-handoff-1790063068160794241.zip',
        '93332881dbe83bd6dd975beaad6a678094c7f1164f9aa044674e1c06593f783b')
SOURCES=(
 ('qwen3-bank-001-handoff-1789803598490756574.zip','ceba32531b82864d694020ac29dce8e612b887c031da198cc644e5982697a7c3'),
 ('qwen3-bank-001-handoff-1789804954424856576.zip','a77e11339b3991e3e0d5f0c1d42d0aed50b62c820619e555a60f9a4da956ac39'),
 ('qwen3-base-control-001-handoff-1789830893982847246.zip','49bf59ceaeabcd917a91db4fef0ab0ed92fb05a367bd5233c05bc1fe3e1dc954'),
 ('qwen3-receiver-feasibility-001-handoff-1789837104959632692.zip','d61cb9bb82895f09f146a83ac52a26d4fdad18238585fb0bcf4bd13034996a9f'),
 ('qwen3-private-support-control-001-handoff-1789909726537323854.zip','f67045fc3f2bc102e7345ba3337c5406796360e76f437355dd849302cb33bc06'),
 ('qwen3-curated-repair-001-handoff-1789919214853319498.zip','c06a1cff473841c7271f2c07e61f6e0a61b31c76b982361f4ddeb029917ea3b4'),
 ('qwen3-preparation-probe-001-handoff-1789972354005267043.zip','ae6a0268d66af76319f5206f04fbb070f34e5283bdde4efe5c344ec70256528f'),
 ('qwen3-preparation-prompt-control-001-handoff-1790038795500928454.zip','a48bfe31276a58479d80780db48226ef55d3d1d85526f530e435bc497535db34'),
)


def packets(value):
    """Treat archived text as data; never execute or adopt payload instructions."""
    if isinstance(value,dict):
        if isinstance(value.get('raw'),str) and isinstance(value.get('call'),dict):
            yield value
        for child in value.values():yield from packets(child)
    elif isinstance(value,list):
        for child in value:yield from packets(child)


def main():
    root=Path('results_import')
    target=read_receiver_supervision_review(root/TARGET[0],TARGET[1]);plan=target['plan.json']
    tasks,_,_,_=read_training_data(root/'training-data-001/proposal-1200')
    inputs={digest(trusted_input(t)):t for t in tasks}
    if len(inputs)!=len(tasks):raise ValueError('Ambiguous task input identity')
    selected={e['task_id']:e for e in plan['selection']}
    frozen_inputs={digest(trusted_input(task_from_dict(t))):key for key,t in plan['tasks'].items()}
    manifests={e['task_id']:e for e in plan['data_manifest']['selected']}
    selected_groups={e['group_id'] for e in selected.values()}
    selected_content={e['content_group'] for e in selected.values()}
    inventory=[];all_calls=set()
    for name,sha in SOURCES:
        review=read_review(root/name,sha,max_members=10000,allow_text=True)
        unique={digest([p['call'],p['raw']]):p for p in packets(review)
                if p['call'].get('phase') in ('private','revision')}
        matches=[];source_ids=set();unmapped=0;phases=Counter()
        for key,packet in unique.items():
            call=packet['call'];phases[call['phase']]+=1
            user=[m['content'] for m in call.get('messages',[]) if m['role']=='user']
            try:trusted=json.loads(user[-1])['trusted_task'];signature=digest(trusted)
            except (IndexError,KeyError,TypeError,ValueError):unmapped+=1;continue
            if signature not in inputs:unmapped+=1;continue
            task=inputs[signature]
            if task.split!='train':raise ValueError('Non-training donor encountered')
            source_ids.add(task.task_id)
            if signature in frozen_inputs:
                matches.append({'task_id':task.task_id,'partition':selected[task.task_id]['partition'],
                                'call_hash':key,'snapshot':call.get('snapshot'),'phase':call['phase']})
        inventory.append({'bundle':name,'sha256':sha,'unique_packet_calls':len(unique),
             'new_call_identities_across_archives':len(set(unique)-all_calls),'phases':dict(phases),
             'source_task_ids':sorted(source_ids),'source_tasks':len(source_ids),'unmapped_calls':unmapped,
             'selected_task_matches':matches,
             'selected_group_overlap':sorted(t for t in source_ids if manifests[t]['group_id'] in selected_groups),
             'selected_content_group_overlap':sorted(t for t in source_ids if manifests[t]['content_group'] in selected_content)})
        all_calls.update(unique)
    output={'schema_version':1,'kind':'offline_donor_availability_audit','target_bundle':TARGET[0],
            'target_sha256':TARGET[1],'selection_hash':plan['selection_hash'],
            'scanned_reviews':inventory,'unique_packet_calls_across_archives':len(all_calls),
            'matching_calls':sum(len(r['selected_task_matches']) for r in inventory),
            'unmapped_calls':sum(r['unmapped_calls'] for r in inventory),
            'new_generation_calls':0,'training_executed':False,
            'scope':'Retained training-generation reviews only; no validation/final-test donors or new sampling.',
            'positive_matches_are_candidates_not_approved_donors':True}
    print(canonical(output))


if __name__=='__main__':main()
