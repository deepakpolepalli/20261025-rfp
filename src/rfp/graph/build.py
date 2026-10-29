"""F01-F15: one explicitly bounded LLM node, deterministic graph routing."""
import json
from time import sleep
from langgraph.graph import StateGraph, START, END
from langgraph.runtime import Runtime
from rfp.graph.state import BatchState, RunContext
from rfp.contracts import digest
from rfp.prompts.evaluation import build_prompt
from rfp.tools.documents import extract_document as extract_pdf,read_artifact
from rfp.tools.validation import normalize,InvalidModelJSON
from rfp.tools.scoring import absolute_scores,peer_metrics,industry_metrics,rank_suppliers as deterministic_rank
from rfp.clients.llm import ProviderFailure
from rfp.persistence.db import now

EVENT_IDS={'load_and_freeze_inputs':'F01','select_supplier':'F02','extract_document':'F03',
           'evaluate_supplier':'F04','validate_scorecard':'F05','stage_validated_scorecard':'F06',
           'advance_supplier':'F07','calculate_absolute_scores':'F08','calculate_peer_metrics':'F09',
           'calculate_industry_metrics':'F10','rank_suppliers':'F11','persist_complete_result':'F12',
           'finalize_run':'F13','prepare_retry':'F14','fail_run':'F15'}


def supplier(state):
    return state['suppliers'][state['current_supplier_index']]


def guarded(function):
    def node(state: BatchState, runtime: Runtime[RunContext]):
        ctx=runtime.context;name=function.__name__;sid=None
        if state.get('current_supplier_index',0)<len(state['suppliers']):
            sid=supplier(state)['supplier_id']
        occurrence=state.get('event_count',0)+1
        try:
            ctx.repo.heartbeat(state['rfp_run_id'],ctx.claim_token)
            result=function(state,ctx)
            ctx.repo.event(state['rfp_run_id'],EVENT_IDS[name],name,sid,occurrence)
            return {**result,'event_count':occurrence}
        except Exception as e:
            # Never persist arbitrary exception text from provider/configuration internals.
            message=str(e) if isinstance(e,ValueError) and not isinstance(e,InvalidModelJSON) else 'Step failed. Check inputs or selected-provider configuration.'
            error={'node_id':EVENT_IDS[name],'node_name':name,'supplier_id':sid,'message':message,'error_type':type(e).__name__}
            try:
                ctx.repo.event(state['rfp_run_id'],EVENT_IDS[name],name,sid,occurrence,'failed')
            except Exception:
                pass
            return {'fatal_error':error,'next_action':'fail','event_count':occurrence}
    node.__name__=function.__name__
    return node


@guarded
def load_and_freeze_inputs(s,c):
    criteria,baseline=c.repo.freeze(s['rfp_run_id'],s['owner_hash'])
    return {'criteria_snapshot':criteria,'criteria_hash':digest(criteria),'industry_snapshot':baseline,'next_action':'select','run_status':'running'}


@guarded
def select_supplier(s,c):
    i=s['current_supplier_index'];cards=dict(s.get('scorecards',{}))
    while i<len(s['suppliers']):
        sid=s['suppliers'][i]['supplier_id'];staged=c.repo.staged(s['rfp_run_id'],sid)
        if not staged['normalized_json']:
            return {'current_supplier_index':i,'scorecards':cards,'repair_used':False,'retry_reason':'','attempts':staged['attempts'],'next_action':'extract'}
        cards[sid]=json.loads(staged['normalized_json']);i+=1
    if len(cards)!=len(s['suppliers']):
        raise ValueError('Incomplete scorecards; cannot calculate benchmarks.')
    return {'current_supplier_index':i,'scorecards':cards,'next_action':'score'}


@guarded
def extract_document(s,c):
    item=supplier(s)
    pages=extract_pdf(read_artifact(c.repo,item['artifact_ref']),item['file_sha256'])
    # Keep extracted text outside checkpoint state; state carries artifact ref only.
    ref=f'artifacts/{s["rfp_run_id"]}/{item["supplier_id"]}.pages.json'
    path=c.repo.directory/ref
    path.write_text(json.dumps(pages),encoding='utf-8')
    return {'current_pages_ref':ref,'next_action':'evaluate'}



def pages(s,c):
    path=(c.repo.directory/s['current_pages_ref']).resolve()
    if not path.is_relative_to(c.repo.artifacts.resolve()):
        raise ValueError('Invalid extracted-text artifact.')
    return json.loads(path.read_text())


@guarded
def evaluate_supplier(s,c):
    item=supplier(s);sid=item['supplier_id']
    prompt=build_prompt(item['supplier_name'],s['criteria_snapshot'],pages(s,c),s.get('repair_used',False))
    prompt_hash=digest({'prompt':prompt,'provider':s['provider_snapshot']})
    previous=c.repo.response(s['rfp_run_id'],sid,prompt_hash)
    if previous:
        return {'current_response':previous,'next_action':'validate'}
    attempt=c.repo.reserve_call(s['rfp_run_id'],sid)
    try:
        response=c.client.evaluate(prompt)
        if response['provider']!=s['provider_snapshot']['provider'] or response['requested_model']!=s['provider_snapshot']['model']:
            raise ValueError('Provider/model mismatch; result rejected.')
        c.repo.save_response(s['rfp_run_id'],sid,attempt,prompt_hash,response)
        return {'current_response':response,'attempts':attempt,'next_action':'validate'}
    except ProviderFailure as e:
        if e.retryable and attempt<3:
            return {'attempts':attempt,'retry_reason':'transport','next_action':'retry'}
        return {'attempts':attempt,'next_action':'fail','fatal_error':{'node_id':'F04','supplier_id':sid,'message':str(e)}}


@guarded
def validate_scorecard(s,c):
    item=supplier(s)
    try:
        card=normalize(s['current_response']['text'],s['criteria_snapshot'],pages(s,c),item['supplier_name'])
        card={**card,**item,'model_response':{k:v for k,v in s['current_response'].items() if k!='text'},
              'attempts':c.repo.staged(s['rfp_run_id'],item['supplier_id'])['attempts']}
        # Artifact references are internal; downloads retain file hash/name only.
        card.pop('artifact_ref',None)
        return {'current_card':card,'next_action':'stage'}
    except InvalidModelJSON:
        attempts=c.repo.staged(s['rfp_run_id'],item['supplier_id'])['attempts']
        if not s.get('repair_used') and attempts<3:
            return {'retry_reason':'json','next_action':'retry','attempts':attempts}
        return {'next_action':'fail','fatal_error':{'node_id':'F05','supplier_id':item['supplier_id'],'message':'Model JSON remained invalid after the permitted correction/budget.'}}


@guarded
def prepare_retry(s,c):
    if s.get('retry_reason')=='transport':
        sleep(min(2**s.get('attempts',1),8))
    return {'repair_used':s.get('repair_used',False) or s.get('retry_reason')=='json','next_action':'evaluate'}


@guarded
def stage_validated_scorecard(s,c):
    item=supplier(s);cards=dict(s['scorecards'])
    c.repo.stage(s['rfp_run_id'],item['supplier_id'],s['current_card'])
    cards[item['supplier_id']]=s['current_card']
    return {'scorecards':cards,'next_action':'advance'}


@guarded
def advance_supplier(s,c):
    return {'current_supplier_index':s['current_supplier_index']+1,'current_response':{},'current_card':{},'next_action':'select'}


@guarded
def calculate_absolute_scores(s,c):
    cards=[s['scorecards'][x['supplier_id']] for x in s['suppliers']]
    return {'calculations':absolute_scores(cards),'next_action':'peer'}


@guarded
def calculate_peer_metrics(s,c):
    return {'calculations':peer_metrics(s['calculations']),'next_action':'industry'}


@guarded
def calculate_industry_metrics(s,c):
    return {'calculations':industry_metrics(s['calculations'],s['industry_snapshot']),'next_action':'rank'}


@guarded
def rank_suppliers(s,c):
    return {'calculations':deterministic_rank(s['calculations']),'next_action':'persist'}


@guarded
def persist_complete_result(s,c):
    run=c.repo.run(s['rfp_run_id'],s['owner_hash'])
    result={'schema_version':'1','rules_version':s['rules_version'],'prompt_version':s['prompt_version'],
            'graph_version':s['graph_version'],'rfp_run_id':s['rfp_run_id'],'created_at':run['created_at'],
            'completed_at':now(),'status':'completed','provider':s['provider_snapshot'],
            'criteria':s['criteria_snapshot'],'criteria_hash':s['criteria_hash'],'industry_baseline':s['industry_snapshot'],
            'suppliers':s['calculations'],'warnings':[w for x in s['calculations'] for w in x['warnings']],
            'events':c.repo.events(s['rfp_run_id'],s['owner_hash']),
            'reproducibility_note':'Saved validated scores reproduce arithmetic and rank. Fresh model calls may differ.'}
    # On replay after a commit/checkpoint crash, use the committed result exactly.
    if run['status']=='completed':
        result=json.loads(run['export_json'])
    else:
        c.repo.complete(s['rfp_run_id'],s['owner_hash'],result)
    return {'result':result,'next_action':'finalize'}


@guarded
def finalize_run(s,c):
    run=c.repo.run(s['rfp_run_id'],s['owner_hash'])
    return {'result':json.loads(run['export_json']),'run_status':'completed','next_action':'end'}


@guarded
def fail_run(s,c):
    error=s.get('fatal_error') or {'message':'Run stopped; no complete leaderboard was saved.'}
    c.repo.fail(s['rfp_run_id'],error)
    return {'run_status':'failed','fatal_error':error,'next_action':'end'}


def build_graph(checkpointer):
    graph=StateGraph(BatchState,context_schema=RunContext)
    functions=[load_and_freeze_inputs,select_supplier,extract_document,evaluate_supplier,validate_scorecard,
               prepare_retry,stage_validated_scorecard,advance_supplier,calculate_absolute_scores,
               calculate_peer_metrics,calculate_industry_metrics,rank_suppliers,persist_complete_result,finalize_run,fail_run]
    for fn in functions:
        graph.add_node(fn.__name__,fn)
    graph.add_edge(START,'load_and_freeze_inputs')
    destinations={'select':'select_supplier','extract':'extract_document','evaluate':'evaluate_supplier',
                  'validate':'validate_scorecard','retry':'prepare_retry','stage':'stage_validated_scorecard',
                  'advance':'advance_supplier','score':'calculate_absolute_scores','peer':'calculate_peer_metrics',
                  'industry':'calculate_industry_metrics','rank':'rank_suppliers','persist':'persist_complete_result',
                  'finalize':'finalize_run','fail':'fail_run','end':END}
    routes={
        'load_and_freeze_inputs':['select','fail'],'select_supplier':['extract','score','fail'],
        'extract_document':['evaluate','fail'],'evaluate_supplier':['validate','retry','fail'],
        'validate_scorecard':['stage','retry','fail'],'prepare_retry':['evaluate','fail'],
        'stage_validated_scorecard':['advance','fail'],'advance_supplier':['select','fail'],
        'calculate_absolute_scores':['peer','fail'],'calculate_peer_metrics':['industry','fail'],
        'calculate_industry_metrics':['rank','fail'],'rank_suppliers':['persist','fail'],
        'persist_complete_result':['finalize','fail'],'finalize_run':['end','fail'],
    }
    for fn in functions:
        if fn.__name__=='fail_run':
            graph.add_edge('fail_run',END)
        else:
            graph.add_conditional_edges(fn.__name__,lambda s:s['next_action'],{k:destinations[k] for k in routes[fn.__name__]})
    return graph.compile(checkpointer=checkpointer)
