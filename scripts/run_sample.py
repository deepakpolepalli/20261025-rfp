"""Run all four fictional proposals against OpenAI using a key entered interactively and save a real example."""
from pathlib import Path
from hashlib import sha256
import json
import argparse
from getpass import getpass
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from rfp.persistence.db import Repository
from rfp.clients.llm import make_client
from rfp.services.runs import prepare_run,execute_run
root=Path(__file__).resolve().parents[1]
repo=Repository(root/'data')
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--model',default='gpt-4o-mini')
args=parser.parse_args()
provider={'provider':'openai','model':args.model}
key=getpass('OpenAI API key (not saved): ')
client=make_client(provider,key)
owner=sha256(b'fictional-recorded-openai-example').hexdigest()
profiles=[('apex_systems.pdf','Apex Systems','8'),('brightpath_tech.pdf','BrightPath Tech','3'),('nexaworks.pdf','NexaWorks','8'),('orbit_digital.pdf','Orbit Digital','9')]
files=[(f,(root/'fixtures/proposals'/f).read_bytes()) for f,_,_ in profiles]
metadata=[{'supplier_name':n,'submission_date':f'2026-10-{12+i}','experience_rating':e} for i,(_,n,e) in enumerate(profiles)]
run_id=prepare_run(repo,owner,files,metadata,provider)
print('Run created',run_id,flush=True)
result=execute_run(repo,run_id,owner,client,lambda n,v:print(n,v.get('next_action'),flush=True))
(root/'sample_output').mkdir(exist_ok=True)
(root/'sample_output/completed_run.json').write_text(json.dumps(result,indent=2,ensure_ascii=False))
print(json.dumps({'status':result['status'],'suppliers':[(s['supplier_name'],s['absolute_score'],s['ppi']) for s in result['suppliers']],'warnings':len(result['warnings'])}),flush=True)
