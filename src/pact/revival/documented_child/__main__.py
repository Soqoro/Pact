"""CPU-only child stages. No acquisition, model execution or wallet activation."""
import argparse
from pathlib import Path
from ...util import canonical, read_json
from . import audit, review


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('stage',choices=['audit','validate','report','export','restore','execution-check'])
    p.add_argument('--config',type=Path,required=True)
    p.add_argument('--bundle',type=Path);p.add_argument('--sha256')
    p.add_argument('--method-hash');p.add_argument('--execution-stage')
    a=p.parse_args(argv)
    try:
        config=read_json(a.config);root=Path(config['output'])
        if a.stage=='audit':out=review.save(root,*audit.run(config))
        elif a.stage in ('validate','report'):out=review.validate(root)
        elif a.stage=='export':out=review.export(root)
        elif a.stage=='restore':out=review.restore(a.bundle,a.sha256,root)
        else:out=review.execution_guard(root,a.execution_stage,a.method_hash)
        print(canonical(out));return 0
    except Exception as error:
        # Source content, paths, token strings and candidate IDs never reach logs.
        print(canonical({'status':'stopped','exception_type':type(error).__name__,
            'model_calls':0,'action':'preserve_inputs_and_output; inspect_privately; no_automatic_retry'}))
        return 1

if __name__=='__main__':raise SystemExit(main())
