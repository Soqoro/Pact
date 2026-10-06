"""Reviewed official source pins and bounded breadth profiles (not GPU evidence)."""
from dataclasses import dataclass, asdict
from ..util import digest

SEED = 20261006
VARIANT = 'heterogeneous_breadth_v1'
PARENT_MODEL_HASH = '9f1213cbdcaf76bbf5169b5dd7740662993affaed751d11360af27dbb4311795'
MATH_REV = 'ba3d3aaff23b3f4cac7a14672b4f6e293d97c98b'
EVALPLUS_REV = '26d6d00bb1fd0fa37f39c99d5290da67891d1c5e'
LIVEBENCH_REV = '8f8e5c381a16e3f24257776edd53471fe86f8091'
LIVE_RELEASE = '2026-06-25'
CATEGORIES = ('biology','business','chemistry','computer science','economics','engineering',
              'health','history','law','math','other','philosophy','physics','psychology')
DOMAINS = ('murder_mysteries','object_placements','team_allocation')

@dataclass(frozen=True)
class BenchmarkSpec:
    name: str
    kind: str
    repository: str
    revision: str
    files: tuple[str, ...]
    n: int
    packet: int
    final: int
    context: int
    core: bool
    scorer: str

REGISTRY = {
 'mmlu-pro': BenchmarkSpec('mmlu-pro','mcq','TIGER-Lab/MMLU-Pro','b189ec765aa7ed75c8acfea42df31fdae71f97be',('data/test-00000-of-00001.parquet',),140,512,64,8192,True,'strict_mcq_v1'),
 'musr': BenchmarkSpec('musr','mcq','TAUR-Lab/MuSR','7c365b439a222150f317764d4f16ae6c96d7d94a',('murder_mystery.csv','object_placements.csv','team_allocation.csv'),90,512,64,8192,True,'strict_mcq_v1'),
 'math-500': BenchmarkSpec('math-500','math_free_response','HuggingFaceH4/MATH-500','6e4ed1a2a79af7d8630a6b768ec859cb5af4d3be',('test.jsonl',),100,1024,1024,8192,True,'math_verify:'+MATH_REV),
 'mbpp-plus': BenchmarkSpec('mbpp-plus','python_program','evalplus/mbppplus','b2d74c91837c3f2a20c1299ae98133cbe7cfa077',('data/test-00000-of-00001-d5781c9c51e02795.parquet',),100,1024,1024,8192,True,'evalplus:'+EVALPLUS_REV),
 'gpqa': BenchmarkSpec('gpqa','mcq','Idavidrein/gpqa','83022cefff930aea54f654c0b282e74b9eeda5c6',('gpqa_diamond.csv',),32,256,64,4096,False,'strict_mcq_v1'),
 'livebench': BenchmarkSpec('livebench','native_livebench','LiveBench/LiveBench',LIVEBENCH_REV,(),100,1024,1024,16384,False,'livebench:'+LIVEBENCH_REV),
}
LIVE_SOURCES = dict(zip(('reasoning','math','data_analysis','language','coding'),(
 '6fc6498a5dfba553f69f4413feabade1f1a2d384','bb66571c8ccf32d3df9e6f48b920d3770ff4aacb',
 '31b9661ff678df9958e2f7fa228427f4c858c1a1','3ada32a2e53d5e04e57fa503384cb85ce9116c40','a958549fdd8aa57be0a3fafe7b205ffc160ed5f4')))

def budget(name, n=None):
    s=REGISTRY[name];n=s.n if n is None else n
    return {'A':{'calls':9*n,'tokens':9*n*s.packet},
            'B':{'calls':21*n if s.core else 0,'tokens':n*(12*s.packet+9*s.final) if s.core else 0}}

def registry():return {k:asdict(v) for k,v in REGISTRY.items()}


def live_registered(row):
    """Allowed dispatches in the pinned official play_a_match_gt, no generic fallback."""
    task=row.get('task','');sub=row.get('subtask') or task;parts=sub.split('_')
    if row.get('category') not in LIVE_SOURCES or task=='agentic_coding':return False
    return (parts[0] in ('amc','smc','aime','imo','usamo') or len(parts)>1 and parts[1]=='amc'
        or 'amps_hard' in sub or 'amps_hard' in task or 'zebra_puzzle' in sub
        or sub in ('cta','tablereformat','tablejoin','consecutive_events','integrals_with_game',
                   'web_of_lies_v2','web_of_lies_v3','house_traversal','spatial','theory_of_mind',
                   'logic_with_navigation','sudoku','typos','connections','plot_unscrambling',
                   'LCB_generation','coding_completion','code_generation','code_completion'))
