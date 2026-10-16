"""Locally initialized tiny causal neural fixture; never a pretrained model."""
import json
from types import SimpleNamespace
from dataclasses import asdict
from ..util import digest,canonical
from ..schemas import CallRecord
from . import neural,contracts as c

class Tokenizer:
    eos_token_id=2
    def encode(self,text,add_special_tokens=False):return [ord(x)+3 for x in text]
    def decode(self,ids,**kwargs):return ''.join(chr(i-3) for i in ids)
    def __call__(self,text,**kwargs):return {'input_ids':self.encode(text),'offset_mapping':[(i,i+1) for i in range(len(text))]}


def model():
    import torch
    from torch import nn
    class Tiny(nn.Module):
        def __init__(self):
            super().__init__();self.embed=nn.Embedding(2048,8)
            self.q_proj=nn.Linear(8,8);self.k_proj=nn.Linear(8,8);self.v_proj=nn.Linear(8,8);self.o_proj=nn.Linear(8,8);self.head=nn.Linear(8,2048)
        def forward(self,input_ids,**kwargs):
            x=self.embed(input_ids);x=x.cumsum(1)/torch.arange(1,x.shape[1]+1,device=x.device)[None,:,None]
            x=self.o_proj(torch.tanh(self.q_proj(x)+self.k_proj(x)+self.v_proj(x)))
            return SimpleNamespace(logits=self.head(x))
    with torch.random.fork_rng():torch.manual_seed(100);return Tiny()

class Backend:
    def __init__(self,key,checkpoint=None):
        self.key=key;self.tokenizer=Tokenizer();self.model=model();self.calls=[]
        self.identity={'fixture':True,'family':key,'snapshot':digest(['tiny',key]),'template_hash':digest(['tiny-template',key])}
        if checkpoint:
            neural.attach(self.model,c.SEED+c.FAMILIES.index(key));neural.load(checkpoint/'checkpoints',__import__('pact.util',fromlist=['read_json']).read_json(checkpoint/'contract.json'),self.model)
            self.identity['adapter_hash']=neural._weights_hash(neural.parameters(self.model));self.identity['snapshot']=digest(self.identity)
    def render_messages(self,messages):return '\n'.join(m.content for m in messages)+'\nassistant:'
    def count_tokens(self,text):return len(self.tokenizer.encode(text))
    def generate(self,req):
        body=json.loads(req.messages[1].content)
        answer=body.get('assigned_option',{'Q':'A','L':'B','M':'C','R':'A'}[self.key])
        raw=json.dumps({'answer':answer,'justification':'Invented fixture output, not scientific evidence.'})
        rendered=self.render_messages(req.messages);ids=self.tokenizer.encode(raw)+[2]
        call=CallRecord('base',req.phase,self.identity['snapshot'],req.seed,req.messages,rendered,digest(rendered),self.identity['template_hash'],canonical({'max_new_tokens':512,'do_sample':not req.deterministic}),self.count_tokens(rendered),len(ids),'eos',.001)
        self.last_generation={'prompt_ids':self.tokenizer.encode(rendered),'completion_ids':ids,'raw':raw,'context_hash':digest(rendered)}
        self.calls.append(call);return raw,call
    def resource_usage(self):return {'fixture':True,'calls':len(self.calls),'compute_units':None}
    def close(self):self.model=None
