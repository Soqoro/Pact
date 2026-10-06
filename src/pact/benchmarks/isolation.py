"""Fail-closed bubblewrap scorer boundary. Never falls back to ordinary execution."""
import os
from pathlib import Path
import shutil
import signal
import socket
import subprocess
import tempfile
import time
from .scoring import LIMITS
from ..util import digest, file_hash, read_json, write_json

class IsolationUnavailable(RuntimeError):pass

class Bubblewrap:
    def __init__(self,python):
        self.python=Path(python).absolute();self.prefix=self.python.parent.parent
        self.bwrap=shutil.which('bwrap');self.prlimit=shutil.which('prlimit')
        if not self.bwrap or not self.prlimit or not self.python.is_file():raise IsolationUnavailable('safe_execution_unavailable')
        # Dedicated evaluator venv only; never bind a workspace/home/Drive subtree.
        if not (self.prefix/'pyvenv.cfg').is_file() or any((p/'.git').exists() for p in (self.prefix,*self.prefix.parents)):
            raise IsolationUnavailable('Dedicated evaluator venv outside Git required')
        if str(self.prefix).startswith(('/content/drive','/root/.','/home/')):raise IsolationUnavailable('Runtime must be a dedicated non-home evaluator prefix')
        self.receipt=None

    def command(self,work,script,*args):
        cmd=[self.prlimit,'--as='+str(LIMITS['memory_bytes']),'--cpu='+str(LIMITS['cpu_seconds']),
             '--nproc='+str(LIMITS['processes']),'--fsize='+str(LIMITS['output_bytes']),
             self.bwrap,'--unshare-all','--die-with-parent','--new-session','--cap-drop','ALL',
             '--uid','65534','--gid','65534','--clearenv','--ro-bind','/usr','/usr']
        for p in ('/lib','/lib64'):
            if Path(p).exists():cmd+=['--ro-bind',p,p]
        cmd+=['--ro-bind',str(self.prefix),str(self.prefix),'--proc','/proc','--dev','/dev',
              '--tmpfs','/tmp','--tmpfs','/dev/shm','--bind',str(work),'/work','--chdir','/work',
              '--setenv','PATH',str(self.python.parent)+':/usr/bin',
              '--setenv','HOME','/tmp','--setenv','OMP_NUM_THREADS','1',
              '--setenv','PACT_ISOLATED_WORKER','1',str(self.python),'-I','/work/'+script,*args]
        return cmd

    def invoke(self,work,script,args=(),wall=None):
        with (work/'worker.log').open('wb') as log:
            proc=subprocess.Popen(self.command(work,script,*args),stdin=subprocess.DEVNULL,stdout=log,stderr=log,
                                  env={'PATH':os.defpath},start_new_session=True)
            timed_out=False
            try:proc.wait(timeout=wall or LIMITS['wall_seconds'])
            except subprocess.TimeoutExpired:timed_out=True
            finally:
                try:os.killpg(proc.pid,signal.SIGKILL)
                except ProcessLookupError:pass
                proc.wait()
        return proc.returncode,timed_out

    def probe(self):
        with tempfile.TemporaryDirectory(prefix='pact-sandbox-probe-') as temp:
            outer=Path(temp);work=outer/'job';work.mkdir();work.chmod(0o777)
            sentinel=outer/'host-sentinel';sentinel.write_text('harmless-probe')
            listener=socket.socket();listener.bind(('127.0.0.1',0));listener.listen(1);port=listener.getsockname()[1]
            try:
                script='''import os,json,socket,resource
from pathlib import Path
blocked=not Path(SENTINEL).exists() and not Path('/content/drive').exists() and not Path('/home').exists()
s=socket.socket();s.settimeout(1)
try:s.connect(('127.0.0.1',PORT));network=False
except OSError:network=True
try:os.setuid(0);nonprivileged=False
except OSError:nonprivileged=os.getuid()!=0
try:Path('/usr/pact-write-probe').write_text('x');readonly=False
except OSError:readonly=True
Path('/work/probe.json').write_text(json.dumps({'files':blocked,'network':network,'nonprivileged':nonprivileged,'readonly':readonly,'secrets':'HF_TOKEN' not in os.environ,'process_limit':resource.getrlimit(resource.RLIMIT_NPROC)[0]<=64,'memory_limit':resource.getrlimit(resource.RLIMIT_AS)[0]<=4*1024**3}))
'''.replace('SENTINEL',repr(str(sentinel))).replace('PORT',str(port))
                (work/'probe.py').write_text(script)
                code,timeout=self.invoke(work,'probe.py',wall=10)
                if code or timeout or not (work/'probe.json').exists():raise IsolationUnavailable('safe_execution_unavailable')
                checks=read_json(work/'probe.json')
                if not all(checks.values()):raise IsolationUnavailable('sandbox_capability_check_failed')
                self.receipt={'enforced':True,'backend':'bubblewrap_namespaces_v1','checks':checks,'limits':LIMITS,
                              'runtime_python':str(self.python),'bwrap_hash':file_hash(Path(self.bwrap)),
                              'probe_hash':digest(script)}
                return self.receipt
            finally:listener.close()

    def run(self,job):
        self.probe() # never trust a stale receipt from another runtime
        with tempfile.TemporaryDirectory(prefix='pact-score-') as temp:
            work=Path(temp)/'job';work.mkdir();work.chmod(0o777);write_json(work/'job.json',job)
            shutil.copyfile(Path(__file__).with_name('score_worker.py'),work/'score_worker.py')
            started=time.monotonic();code,timeout=self.invoke(work,'score_worker.py',('/work/job.json','/work/result.json'))
            if code or timeout or not (work/'result.json').is_file():
                score={'availability':'scorer_timeout' if timeout else 'scorer_crashed','native_score':None,'full_success':None,'syntactic_valid':None}
            else:score=read_json(work/'result.json')
            return {'job_hash':job['job_hash'],'identity':job['identity'],'sandbox':self.receipt,
                    'score':score,'wall_seconds':time.monotonic()-started}
