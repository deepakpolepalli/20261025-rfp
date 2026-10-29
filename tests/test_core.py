from copy import deepcopy
from decimal import Decimal as D
from pathlib import Path
import json
import pytest
from rfp.contracts import validate_criteria
from rfp.tools.scoring import absolute_scores,peer_metrics,industry_metrics,rank_suppliers,score_and_rank
from rfp.tools.validation import normalize,InvalidModelJSON
from rfp.tools.documents import extract_document
from rfp.persistence.db import Repository
from rfp.services.runs import prepare_run,execute_run
from rfp.clients.llm import ProviderFailure

ROOT=Path(__file__).resolve().parents[1]
PROVIDER={'provider':'openai','model':'gpt-4o-mini'}


def card(name,scores,date='2026-10-12',experience='8'):
    return {'supplier_id':name,'supplier_name':name,'submission_date':date,'experience_rating':experience,'warnings':[],
            'criteria':[{'criterion_id':i+1,'name':f'Criterion {i+1}','score':str(x),'max_score':'10','weight':str(w),'warnings':[]} for i,(x,w) in enumerate(zip(scores,[60,40]))]}


def test_hand_calculated_scores_and_ppi():
    values=peer_metrics(absolute_scores([card('A',[8,5]),card('B',[6,10])]))
    assert [(D(s['absolute_score']),D(s['ppi'])) for s in values]==[(D(68),D(80)),(D(76),D(85))]
    assert rank_suppliers(values)[0]['supplier_name']=='B'


def test_tie_breaks_and_full_precision():
    rows=[{**card(n,[1,1],d,e),'ppi':p} for n,d,e,p in [
        ('Z','2026-10-10','1','80.00001'),('B','2026-10-09','9','80'),
        ('A','2026-10-09','9','80'),('Early','2026-10-08','1','80'),('Low','2026-10-09','2','80')]]
    ranked=rank_suppliers(rows)
    assert [s['supplier_name'] for s in ranked]==['Z','Early','A','B','Low']
    assert [s['final_rank'] for s in ranked]==list(range(1,6))


def test_zero_benchmark_and_industry_do_not_change_ranking():
    rows=peer_metrics(absolute_scores([card('A',[0,0]),card('B',[0,0])]))
    assert all(D(s['ppi'])==0 for s in rows)
    first=industry_metrics(rows,{'label':'Illustrative','targets':{'1':{'score':'7','max_score':'10'}}})
    assert all(s['industry_index'] is None for s in first)
    assert [s['supplier_name'] for s in rank_suppliers(first)]==['A','B']


def test_seed_preserves_changes_and_invalid_weights_block(tmp_path):
    repo=Repository(tmp_path)
    rows=repo.criteria();rows[0]['weight']='29'
    with pytest.raises(ValueError,match='100'):repo.update_criteria(rows)
    rows[0]['weight']='25';rows[1]['weight']='25';repo.update_criteria(rows)
    assert Repository(tmp_path).criteria()[0]['weight']=='25'


def test_normalization_and_evidence_matching(tmp_path):
    criteria=validate_criteria(Repository(tmp_path).criteria())
    raw={'supplier_name':'wrong','criteria':[
        {'criterion_id':1,'score':99,'max_score':10,'evidence':'Verified quotation.','justification':'supported'},
        {'criterion_id':2,'score':8,'max_score':10,'evidence':'Fabricated quotation.','justification':'unsupported'},
        {'criterion_id':3,'score':8},{'criterion_id':3,'score':9},
        {'criterion_id':4,'score':True},{'criterion_id':999,'score':10}]}
    result=normalize(json.dumps(raw),criteria,[{'page':2,'text':'Verified quotation.'}],'Apex')
    assert [D(c['score']) for c in result['criteria']]==[D(10),D(0),D(0),D(0),D(0)]
    assert result['criteria'][0]['evidence_pages']==[2]
    assert len(result['warnings'])>0
    with pytest.raises(InvalidModelJSON):normalize('broken',criteria,[],'Apex')


class FakeClient:
    def __init__(self,bad_json_once=False,fail=False,secret=''):
        self.calls=0;self.bad_json_once=bad_json_once;self.fail=fail;self.secret=secret
    def evaluate(self,prompt):
        self.calls+=1
        if self.fail:raise ProviderFailure('Provider unavailable.',retryable=False)
        if self.bad_json_once and self.calls==1:
            return {'text':'bad JSON',**PROVIDER,'requested_model':PROVIDER['model']}
        name=prompt.split('SUPPLIER: ')[1].split('\nACTIVE CRITERIA:')[0]
        evidence=prompt.split('--- PAGE 1 ---\n')[1].split('\n')[0]
        active=json.loads(prompt.split('ACTIVE CRITERIA: ')[1].split('\n')[0])
        payload={'supplier_name':name,'criteria':[{'criterion_id':c['criterion_id'],'score':7,'max_score':10,'evidence':evidence,'justification':'Synthetic test assessment.'} for c in active], 'risks':[],'overall_summary':'Test fixture, not live model evidence.'}
        return {'text':json.dumps(payload),'provider':'openai','requested_model':PROVIDER['model'],'returned_model':PROVIDER['model'],'usage':{}}


def prepared(repo):
    files=[(p.name,p.read_bytes()) for p in sorted((ROOT/'fixtures/proposals').glob('*.pdf'))]
    metadata=[{'supplier_name':p[0],'submission_date':'2026-10-12','experience_rating':'8'} for p in files]
    return prepare_run(repo,'owner',files,metadata,PROVIDER)


def test_complete_graph_atomic_export_and_secret_isolation(tmp_path):
    repo=Repository(tmp_path);run_id=prepared(repo);client=FakeClient(secret='CANARY-DO-NOT-PERSIST')
    result=execute_run(repo,run_id,'owner',client)
    assert result['status']=='completed' and len(result['suppliers'])==4 and client.calls==4
    assert {'F01','F02','F03','F04','F05','F06','F07','F08','F09','F10','F11','F12','F13'}<={x['node_id'] for x in result['events']}
    assert json.loads(repo.run(run_id,'owner')['export_json'])==result
    assert execute_run(repo,run_id,'owner',FakeClient(fail=True))==result
    for path in tmp_path.glob('*.sqlite'):
        assert b'CANARY-DO-NOT-PERSIST' not in path.read_bytes()
    with repo.connect() as c:assert c.execute('SELECT COUNT(*) FROM supplier_results').fetchone()[0]==4
    with pytest.raises(PermissionError):repo.run(run_id,'another-owner')


def test_json_repair_routes_through_f14(tmp_path):
    repo=Repository(tmp_path);run_id=prepared(repo);client=FakeClient(bad_json_once=True)
    result=execute_run(repo,run_id,'owner',client)
    assert client.calls==5
    assert 'F14' in [x['node_id'] for x in result['events']]


def test_failed_provider_never_persists_partial_leaderboard(tmp_path):
    repo=Repository(tmp_path);run_id=prepared(repo)
    with pytest.raises(ValueError):execute_run(repo,run_id,'owner',FakeClient(fail=True))
    assert repo.run(run_id,'owner')['status']=='failed'
    with repo.connect() as c:assert c.execute('SELECT COUNT(*) FROM supplier_results').fetchone()[0]==0
    assert repo.events(run_id,'owner')[-1]['node_id']=='F15'


def test_pdf_validation_and_sample_pages():
    for path in (ROOT/'fixtures/proposals').glob('*.pdf'):
        assert len(extract_document(path.read_bytes()))==3
    with pytest.raises(ValueError):extract_document(b'not a pdf')


def test_invalid_batch_has_no_run(tmp_path):
    repo=Repository(tmp_path)
    with pytest.raises(ValueError):prepare_run(repo,'owner',[],[],PROVIDER)
    with repo.connect() as c:assert c.execute('SELECT COUNT(*) FROM rfp_runs').fetchone()[0]==0


def test_resume_reuses_staged_supplier_and_frozen_criteria(tmp_path):
    repo=Repository(tmp_path);run_id=prepared(repo);client=FakeClient()
    def interrupt(node,values):
        if node=='stage_validated_scorecard':
            raise RuntimeError('Simulated process interruption after supplier staging')
    with pytest.raises(RuntimeError):execute_run(repo,run_id,'owner',client,interrupt)
    assert repo.run(run_id,'owner')['status']=='running'
    changed=repo.criteria();changed[0]['weight']='25';changed[1]['weight']='25';repo.update_criteria(changed)
    result=execute_run(repo,run_id,'owner',client)
    assert client.calls==4
    assert result['criteria'][0]['weight']=='30'
    assert repo.criteria()[0]['weight']=='25'


def test_failed_transaction_rolls_back_all_supplier_rows(tmp_path):
    repo=Repository(tmp_path);run_id=prepared(repo)
    suppliers=[{**card(str(i),[1,1]),'absolute_score':'10','ppi':'100','final_rank':1} for i in range(4)]
    with pytest.raises(Exception):repo.complete(run_id,'owner',{'suppliers':suppliers})
    with repo.connect() as c:assert c.execute('SELECT COUNT(*) FROM supplier_results').fetchone()[0]==0
    assert repo.run(run_id,'owner')['status']=='running'


def test_run_claim_blocks_concurrent_execution(tmp_path):
    repo=Repository(tmp_path);run_id=prepared(repo)
    repo.claim(run_id,'owner','worker-one')
    with pytest.raises(ValueError,match='already executing'):repo.claim(run_id,'owner','worker-two')
    repo.release(run_id,'worker-one')
    repo.claim(run_id,'owner','worker-two')


def test_unreadable_pdf_stops_before_model_call(tmp_path):
    repo=Repository(tmp_path);run_id=prepared(repo);client=FakeClient()
    with repo.connect() as c:
        original=json.loads(c.execute('SELECT input_json FROM run_suppliers WHERE rfp_run_id=? ORDER BY rowid LIMIT 1',(run_id,)).fetchone()[0])
    (repo.directory/original['artifact_ref']).write_bytes(b'%PDF- broken input')
    with pytest.raises(ValueError):execute_run(repo,run_id,'owner',client)
    assert client.calls==0
    assert repo.events(run_id,'owner')[-1]['node_id']=='F15'


def test_openai_adapter_contract_without_a_real_key(monkeypatch):
    from types import SimpleNamespace
    import openai
    from rfp.clients.llm import OpenAIClient
    received={}
    class FakeOpenAI:
        def __init__(self,**kwargs):
            received['initial']=kwargs
            self.responses=SimpleNamespace(create=self.create)
        def create(self,**kwargs):
            received['request']=kwargs
            return SimpleNamespace(status='completed',output_text='{"ok":true}',model='gpt-4.1-mini',usage=None,id='test-response')
    monkeypatch.setattr(openai,'OpenAI',FakeOpenAI)
    result=OpenAIClient('CANARY-KEY-NOT-REAL','gpt-4.1-mini').evaluate('test prompt')
    assert result['provider']=='openai' and result['text']=='{"ok":true}'
    assert received['request']['store'] is False and received['initial']['max_retries']==0
    assert 'CANARY-KEY-NOT-REAL' not in json.dumps(result)


def test_hosted_oci_signer_is_runtime_only(monkeypatch):
    oci=pytest.importorskip('oci',reason='Optional historical transport checks')
    OciGenAI=pytest.importorskip('rfp.clients.oci_genai',reason='Historical helper not included in release').OciGenAI
    captured={}
    def signer(**kwargs):
        captured['signer']=kwargs
        return object()
    def client(config,**kwargs):
        captured['client']=kwargs
        return object()
    monkeypatch.setattr(oci.signer,'Signer',signer)
    monkeypatch.setattr(oci.generative_ai_inference,'GenerativeAiInferenceClient',client)
    adapter=OciGenAI(config_override={'tenancy':'test-tenancy','user':'test-user','fingerprint':'test-fingerprint','key_content':'CANARY-SIGNING-KEY'})
    assert captured['signer']['private_key_content']=='CANARY-SIGNING-KEY'
    assert captured['signer']['private_key_file_location'] is None
    assert 'key_content' not in vars(adapter)
