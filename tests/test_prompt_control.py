"""Synthetic CPU control-path checks; no pretrained model or GPU performance claims."""
import contextlib,copy,dataclasses as dc,io,json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from pact.backends import Request
from pact.schemas import Message,task_from_dict
from pact.util import canonical,digest,read_json,write_json,file_hash
from pact.training.prompt_control import build_prompt_plan,prompt_report,load_prompt_config
from pact.training.prompt_control_runner import run_prompt_control,restore_prompt_control
from pact.training.preparation_probe import probe_plan
from pact.training.curated_repair import curated_requests
from pact.training.collection_config import CollectionRuntime
from pact.cli import main
from test_preparation_execution import probe_fixture
from test_receiver import FixtureBackend


def fixture():
    _,design,parent=probe_fixture();base=probe_plan(design,parent)
    backend=FixtureBackend(CollectionRuntime('a'*64,20260920),parent)
    backend.identity['snapshot']=base['models']['actors']['snapshot']
    records=[]
    for item in curated_requests(base):
        c=item['context'];raw,call=backend.generate(Request(task_from_dict(base['tasks'][c['task_id']]),
            tuple(Message(m['role'],m['content']) for m in c['messages']),f"agent-{c['recipient']}",c.get('phase','revision'),item['seed'],256,False))
        records.append({'work_id':item['work_id'],'context_id':c['context_id'],'raw':raw,'call':dc.asdict(call),'tokens':backend.last_generation})
    config={'fixture':True}
    return config,build_prompt_plan(config,design,base,records),parent


@contextlib.contextmanager
def execution(parent,backends,mode='answer'):
    def create(runtime,*unused):
        b=FixtureBackend(runtime,parent,mode='crash' if mode=='crash' else 'mixed')
        b.identity['snapshot']=digest({'base':parent.base_snapshot,'actors':parent.reference_hashes})
        b.identity['adapters']=[{'identity':f'agent{i}','sha256':h} for i,h in enumerate(parent.reference_hashes)]
        b.tokenizer.apply_chat_template=lambda messages,**kw:canonical([{'schema_version':1,**m} for m in messages])
        b.tokenizer.encode=lambda text,**kw:[ord(c)+1 for c in text]
        original=b.generate
        def generate(request):
            raw,call=original(request)
            if mode=='answer':raw=canonical({'answer':json.loads(raw)['answer']})
            elif mode=='malformed':raw='not json'
            ids=[ord(c)+1 for c in raw]+[0]
            call=dc.replace(call,output_tokens=len(ids));b.calls[-1]=call
            b.last_generation.update(raw=raw,completion_ids=ids)
            return raw,call
        b.generate=generate;backends.append(b);return b
    with patch('pact.training.prompt_control_runner.preparation_references',return_value=parent), \
         patch('pact.training.prompt_control_runner.runtime_fingerprint',return_value=parent.runtime_fingerprint), \
         patch('pact.training.prompt_control_runner.verify_references'), \
         patch('pact.training.prompt_control_runner.CollectionBackend',side_effect=create),contextlib.redirect_stdout(io.StringIO()):yield


def run(config,plan,tmp,**kw):
    tmp=Path(tmp);training=tmp/'training';training.mkdir(exist_ok=True)
    write_json(training/'INFERENCE_ONLY.json',{'synthetic_fixture':True})
    return run_prompt_control(config,plan,training,tmp/'run','cache',persistent=tmp/'drive/control',**kw)


class PromptControlTests(unittest.TestCase):
    def test_frozen_config_and_label_free_messages(self):
        config=load_prompt_config('experiments/preparation_prompt_control.json')
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'bad.json';config['budget']['generation_calls']=73;write_json(path,config)
            with self.assertRaises(ValueError):load_prompt_config(path)
        cfg,plan,parent=fixture()
        self.assertEqual(len(plan['contexts']),72)
        self.assertEqual(len(plan['tasks']),24)
        self.assertTrue(all('gold' not in r and 'labels' not in r for r in plan['requests']))
        for c in plan['contexts']:
            self.assertIn('sole key "answer"',c['messages'][0]['content'])
            self.assertNotEqual(c['messages'],plan['baseline_records'][c['context_id']]['call']['messages'])
        self.assertEqual(plan['budget']['generation_calls_upper_bound'],72)

    def test_pause_resume_restore_repeat_and_no_extra_calls(self):
        cfg,plan,parent=fixture();backends=[]
        with tempfile.TemporaryDirectory() as tmp,execution(parent,backends):
            first=run(cfg,plan,tmp,stop_after=5);self.assertEqual(first['committed_calls'],5)
            root=Path(tmp)/'run';old={p.name:file_hash(p) for p in (root/'calls/shards').iterdir()}
            partial=read_json(root/'partial_report.json');self.assertEqual(partial['missing_records'],67)
            final=run(cfg,plan,tmp,resume=True);self.assertEqual(final['status'],'prompt_control_complete_local',final)
            self.assertTrue(final['persistent_copy_verified']);self.assertEqual(sum(len(b.calls) for b in backends),72)
            for n,h in old.items():self.assertEqual(file_hash(root/'calls/shards'/n),h)
            report=read_json(root/'report.json');self.assertEqual(report['summary']['paired_responses'],72)
            self.assertEqual(report['summary']['parser_counts'],{'ok':72});self.assertTrue(all(t['complete'] for t in report['teams']))
            self.assertTrue(all(c.phase=='private' and c.actor!='base' for b in backends for c in b.calls))
            repeat=run(cfg,plan,tmp,resume=True);self.assertEqual(repeat['exit_code'],0);self.assertEqual(len(backends[-1].calls),0)
            self.assertEqual(read_json(root/'resources.json')['cache_hits'],72)
            restore_prompt_control(repeat['persistent_snapshot'],Path(tmp)/'restored')
            with self.assertRaisesRegex(ValueError,'latest snapshot'):restore_prompt_control(first['persistent_snapshot'],Path(tmp)/'stale')
            changed=copy.deepcopy(plan);changed['scope']='changed'
            with self.assertRaisesRegex(ValueError,'source/recipe'):run(cfg,changed,tmp,resume=True)

    def test_invalid_contract_counts_failure_and_wrong_seed_rejected(self):
        cfg,plan,parent=fixture();backends=[]
        with tempfile.TemporaryDirectory() as tmp,execution(parent,backends,mode='packet'):
            done=run(cfg,plan,tmp);self.assertEqual(done['exit_code'],0)
            root=Path(tmp)/'run';report=read_json(root/'report.json')
            self.assertEqual(report['summary']['correct'],0)
            self.assertEqual(report['summary']['parser_counts'],{'malformed':72})
            from pact.artifacts import ShardStore
            records=ShardStore(root).records();records[0]['call']['seed']+=1
            with self.assertRaisesRegex(ValueError,'provenance'):prompt_report(plan,records)
            records=ShardStore(root).records();records[0]['raw']='{"answer":"A"}';records[0]['call']['stop_reason']='length'
            self.assertEqual(prompt_report(plan,records)['summary']['parser_counts']['length'],1)

    def test_ambiguous_call_and_overflow_cannot_regenerate(self):
        cfg,plan,parent=fixture();backends=[]
        with tempfile.TemporaryDirectory() as tmp,execution(parent,backends,mode='crash'):
            failed=run(cfg,plan,tmp);self.assertEqual(failed['exit_code'],2);self.assertTrue(Path(failed['path']).exists())
            with self.assertRaisesRegex(ValueError,'Ambiguous attempted call'):run(cfg,plan,tmp,resume=True)
        with tempfile.TemporaryDirectory() as tmp,execution(parent,backends):
            changed=copy.deepcopy(plan);changed['contexts'][0]['messages'][0]['content']='x'*5000
            failed=run(cfg,changed,tmp);self.assertEqual(failed['exit_code'],2);self.assertEqual(len(backends[-1].calls),0)

    def test_persistence_failure_retains_local_zip_and_cli_default_is_plan(self):
        cfg,plan,parent=fixture();backends=[]
        with tempfile.TemporaryDirectory() as tmp,execution(parent,backends),patch('pact.training.prompt_control_runner.persist_bundle',side_effect=TimeoutError('fixture')):
            failed=run(cfg,plan,tmp,stop_after=1);self.assertEqual(failed['exit_code'],2);self.assertTrue(Path(failed['path']).exists())
        with tempfile.TemporaryDirectory() as tmp,contextlib.redirect_stdout(io.StringIO()),patch('pact.training.prompt_control.prompt_plan',return_value=plan),patch('pact.training.prompt_control_runner.CollectionBackend',side_effect=AssertionError('must not load')):
            args=['preparation-prompt-control','--config','experiments/preparation_prompt_control.json']
            for key in ('training-bundle','probe-bundle','training-root','run-dir','persistent'):args+=['--'+key,str(Path(tmp)/key)]
            self.assertEqual(main(args),0);self.assertFalse((Path(tmp)/'run-dir').exists())

    def test_colab_cells_compile_and_imports_exist(self):
        import ast,re,importlib
        cells=re.findall(r'```python\n(.*?)```',Path('docs/preparation_prompt_control_colab.md').read_text(),re.S)
        self.assertEqual(len(cells),6)
        for cell in cells:
            tree=ast.parse(cell)
            for node in ast.walk(tree):
                if isinstance(node,ast.ImportFrom) and node.module and node.module.startswith('pact.'):
                    module=importlib.import_module(node.module)
                    for item in node.names:self.assertTrue(hasattr(module,item.name))
