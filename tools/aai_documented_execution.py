"""Single-stage Slurm entry; configuration and approval are private inputs."""
import argparse
import json
import os
from pathlib import Path
from pact.revival.documented_execution import guard
from pact.revival.documented_execution.__main__ import main


def arguments(config):
    allowed={'stage','run_dir','plan_hash','approval','approval_sha256','cache_dir','persistent',
             'block','family','policy','seed','resume'}
    if set(config)-allowed or config.get('stage') not in guard.STAGES:
        raise ValueError('one_known_scientific_stage_required')
    for key in ('run_dir','cache_dir'):
        if not Path(config[key]).is_absolute() or not Path(config[key]).is_relative_to('/local'):
            raise ValueError('hot_files_require_local_scratch')
    if not Path(config['persistent']).is_relative_to(Path('/dataset')/os.environ['USER']/'PACT'):
        raise ValueError('private_dataset_persistence_required')
    argv=[config['stage'],'--execute']
    for key,value in config.items():
        if key=='stage':continue
        if key=='resume':
            if type(value) is not bool:raise ValueError('resume_must_be_boolean')
            if value:argv.append('--resume')
        else:argv.extend(['--'+key.replace('_','-'),str(value)])
    return argv


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--config',type=Path,required=True)
    p.add_argument('--token-file',type=Path,required=True);a=p.parse_args()
    try:
        argv=arguments(json.loads(a.config.read_text()))
        os.environ['HF_TOKEN']=a.token_file.read_text().strip()
        if not os.environ['HF_TOKEN']:raise ValueError('token_missing')
    except Exception as e:
        print(json.dumps({'status':'stopped','exception_type':type(e).__name__}));raise SystemExit(1)
    raise SystemExit(main(argv))
