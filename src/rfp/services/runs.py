"""Service boundary: upload validation, ownership, graph lifecycle and recovery."""
from datetime import date
from hashlib import sha256
from pathlib import Path
from uuid import uuid4
import json
import sqlite3
from langgraph.checkpoint.sqlite import SqliteSaver
from rfp.contracts import SupplierInput,canonical,digest
from rfp.graph.build import build_graph
from rfp.graph.state import RunContext
from rfp.prompts.evaluation import PROMPT_VERSION
from rfp.provider_policy import validate_provider


def prepare_run(repo, owner_hash, files, metadata, provider):
    validate_provider(provider)
    if len(files) not in (4,5) or len(metadata)!=len(files):
        raise ValueError('Upload 4 or 5 PDFs, with metadata for each supplier.')
    if provider.get('provider') not in ('oci','openai') or not provider.get('model'):
        raise ValueError('Choose a supported provider and model.')
    run_id=str(uuid4());suppliers=[];names=set();hashes=set()
    for (filename,data),meta in zip(files,metadata):
        if not data or len(data)>10*1024*1024 or not data.startswith(b'%PDF-'):
            raise ValueError('Each file must be a non-empty PDF no larger than 10 MiB.')
        name=canonical(meta['supplier_name']);hashed=sha256(data).hexdigest()
        if name in names:
            raise ValueError('Supplier names must be unique within the batch.')
        if hashed in hashes:
            raise ValueError('Identical PDF uploaded more than once. Use one document per supplier.')
        names.add(name);hashes.add(hashed)
        sid=str(uuid4())
        item=SupplierInput(supplier_id=sid,filename=Path(filename).name,file_sha256=hashed,
                           artifact_ref=f'artifacts/{run_id}/{sid}.pdf',**meta).model_dump(mode='json')
        suppliers.append(item)
    # Do not create a partial run on invalid metadata; write only after full validation.
    for (_,data),item in zip(files,suppliers):
        path=repo.directory/item['artifact_ref'];path.parent.mkdir(parents=True,exist_ok=True)
        path.write_bytes(data)
    repo.create_run(run_id,owner_hash,suppliers,provider)
    return run_id


def initial_state(repo,run_id,owner_hash):
    run=repo.run(run_id,owner_hash)
    with repo.connect() as c:
        suppliers=[json.loads(x[0]) for x in c.execute('SELECT input_json FROM run_suppliers WHERE rfp_run_id=? ORDER BY rowid',(run_id,))]
    return {'state_schema_version':'1','graph_version':'rfp-graph-v1','rules_version':'rfp-rules-v1',
            'prompt_version':PROMPT_VERSION,'rfp_run_id':run_id,'owner_hash':owner_hash,
            'input_fingerprint':run['input_fingerprint'],'suppliers':suppliers,
            'provider_snapshot':json.loads(run['provider_json']),'current_supplier_index':0,
            'scorecards':{},'event_count':0,'repair_used':False,'fatal_error':None,'run_status':'running'}


def execute_run(repo,run_id,owner_hash,client,on_progress=None):
    run=repo.run(run_id,owner_hash)
    validate_provider(json.loads(run['provider_json']))
    if run['status']=='completed':
        return json.loads(run['export_json'])
    if run['status']!='running':
        raise ValueError('Failed runs are terminal. Correct the issue and create a new evaluation.')
    token=str(uuid4());repo.claim(run_id,owner_hash,token)
    try:
        with SqliteSaver.from_conn_string(str(repo.directory/'checkpoints.sqlite')) as saver:
            graph=build_graph(saver)
            config={'configurable':{'thread_id':run_id},'recursion_limit':160}
            checkpoint=graph.get_state(config)
            if checkpoint.values:
                state=checkpoint.values
                expected=initial_state(repo,run_id,owner_hash)
                for key in ['state_schema_version','graph_version','prompt_version','rules_version','provider_snapshot','owner_hash','input_fingerprint']:
                    if state.get(key)!=expected[key]:
                        raise ValueError('Incompatible saved run configuration; do not resume this checkpoint.')
                inputs=None
            else:
                inputs=initial_state(repo,run_id,owner_hash)
            ctx=RunContext(repo,client,token)
            for update in graph.stream(inputs,config,context=ctx,stream_mode='updates'):
                if on_progress:
                    for name,values in update.items():
                        on_progress(name,values)
            final=repo.run(run_id,owner_hash)
            if final['status']!='completed':
                error=json.loads(final['error_json'] or '{}')
                raise ValueError(error.get('message','Evaluation failed. No complete leaderboard was saved.'))
            result=json.loads(final['export_json'])
            result['events']=repo.events(run_id,owner_hash)
            with repo.connect() as c:
                c.execute('UPDATE rfp_runs SET export_json=?,result_hash=? WHERE rfp_run_id=? AND owner_hash=?',
                          (json.dumps(result,sort_keys=True,ensure_ascii=False),digest(result),run_id,owner_hash))
            return result
    except Exception:
        # A crash/fault may leave a completed commit; never turn that into failure.
        if repo.run(run_id,owner_hash)['status']=='completed':
            return json.loads(repo.run(run_id,owner_hash)['export_json'])
        # Expected node failures are already terminal. Unexpected interruption remains
        # running so a compatible checkpoint can be recovered, after lease release.
        raise
    finally:
        repo.release(run_id,token)
