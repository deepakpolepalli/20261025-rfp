"""ProcureIQ: Streamlit UI. All evaluation orchestration lives in LangGraph."""
from datetime import date
from decimal import Decimal
from hashlib import sha256
from html import escape
from io import BytesIO
from pathlib import Path
from uuid import uuid4
import json
import os
import sys
import zipfile

ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'src'))
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from rfp.contracts import validate_criteria
from rfp.persistence.db import Repository
from rfp.clients.llm import make_client,ProviderFailure
from rfp.provider_policy import deployment_mode,openai_models
from rfp.services.runs import prepare_run,execute_run

st.set_page_config(page_title='ProcureIQ | RFP Evaluation',page_icon='◈',layout='wide')
st.markdown('''<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Manrope:wght@400;600;700;800&display=swap');
:root{--purple:#6346c7;--ink:#242337;--muted:#78758c;--line:#e9e6ef}
html,body,[class*="css"],.stApp{font-family:'DM Sans',sans-serif;color:var(--ink)}
.stApp{background:#faf9fc}[data-testid="stSidebar"]{background:#f1eff7;border-right:1px solid #e6e2ee}
[data-testid="stSidebar"] [data-testid="stVerticalBlock"]{gap:.8rem}
.block-container{max-width:1490px;padding:2.4rem 3.2rem 3rem}
h1,h2,h3{font-family:'Manrope',sans-serif;letter-spacing:-.035em}h2{font-size:1.55rem!important}h3{font-size:1.08rem!important}
[data-testid="stHeader"]{background:transparent}
.hero{background:linear-gradient(115deg,#35227f 0%,#5833a3 58%,#7b45bb 100%);border-radius:18px;padding:32px 38px 30px;color:white;margin-bottom:25px;box-shadow:0 16px 38px #43308015;position:relative;overflow:hidden}
.hero:after{content:'◈';position:absolute;right:44px;top:0;font-size:190px;color:#ffffff0b;transform:rotate(12deg)}
.eyebrow{font-size:10px;letter-spacing:2.2px;font-weight:700;color:#d3c8f5;margin-bottom:10px}.hero h1{font-size:36px!important;font-weight:800;margin:0 0 9px;line-height:1.25;color:white}.hero p{font-size:14px;line-height:1.7;max-width:760px;margin:0;color:#e8e0fa}
.flow{display:flex;gap:9px;align-items:center;margin-top:21px;font-size:11px;color:#d6cbef}.flow b{background:#ffffff12;border:1px solid #ffffff26;border-radius:99px;padding:7px 13px;font-weight:500}.flow .ai{background:#ffffff24}
.stat{background:#fff;border:1px solid var(--line);border-radius:12px;padding:17px 20px;margin-bottom:17px;min-height:93px}.stat small{font-size:10px;text-transform:uppercase;letter-spacing:1.2px;color:#898498;font-weight:700}.stat strong{display:block;font-size:25px;font-family:'Manrope',sans-serif;letter-spacing:-1px;margin-top:5px}.stat span{font-size:11px;color:#8b879a}
.section-note{font-size:13px;color:#827c91;line-height:1.7;margin-bottom:20px}
.criterion{background:#fff;border:1px solid var(--line);border-radius:12px;padding:19px 21px;margin:0 0 12px}.criterion-head{display:flex;align-items:center;justify-content:space-between;gap:12px}.criterion-title{font-size:14px;font-weight:700}.criterion-weight{font-weight:700;font-size:18px}.tag{font-size:10px;color:#867b9c;margin-top:5px}.criterion p{font-size:12px;color:#827b90;margin:11px 0 0;line-height:1.6}.bar{height:5px;border-radius:9px;margin-top:16px;background:#eeeaf6}.bar div{height:5px;border-radius:9px}.max{font-size:11px;color:#8d8799;margin-left:12px;font-weight:400}.active{font-size:10px;color:#497c6a;background:#eef8f2;padding:4px 8px;border-radius:6px;margin-left:10px}
.side-brand{font-family:'Manrope';font-weight:800;font-size:22px;letter-spacing:-1px;color:#47318d}.side-sub{font-size:10px;letter-spacing:1.2px;color:#9991ab;margin-top:0;margin-bottom:20px}.mode-card{border-left:3px solid #7453d5;background:#fff;border-radius:10px;padding:13px 15px;border-top:1px solid #e7e1f1;border-bottom:1px solid #e7e1f1;border-right:1px solid #e7e1f1}.mode-card small{font-size:9px;letter-spacing:1.3px;color:#8e869d}.mode-card b{display:block;font-size:13px;margin:5px 0}.mode-card p{font-size:11px;color:#8c829a;margin:0;line-height:1.6}
.insight{padding:18px 20px;background:#f1ecfa;border:1px solid #e6ddf4;border-radius:12px;font-size:12px;line-height:1.7;color:#6b5b85}.insight b{display:block;color:#4e367e;margin-bottom:5px}.empty{text-align:center;padding:42px 18px;border:1px dashed #dcd5e8;border-radius:14px;color:#9b91ac;background:#fff}.empty b{display:block;font-size:17px;color:#61556f;margin:10px 0}.empty p{font-size:13px;line-height:1.7}
[data-testid="stTabs"] [data-baseweb="tab-list"]{gap:21px;border-bottom:1px solid #e4deed;margin-bottom:22px}[data-baseweb="tab"]{font-size:12px!important;padding:9px 0 12px!important}
.stButton>button[kind="primary"],.stFormSubmitButton>button[kind="primary"]{background:#6546c7;border-color:#6546c7;border-radius:9px}.stButton>button,.stDownloadButton>button{border-radius:9px;font-size:12px}
[data-testid="stMetric"]{background:#fff;border:1px solid var(--line);border-radius:12px;padding:16px}
footer{visibility:hidden}.footnote{font-size:10px;color:#a59bad;margin-top:27px;border-top:1px solid #eee9f3;padding-top:15px}
@media(max-width:900px){.block-container{padding:1.4rem 1rem}.hero{padding:24px}.hero h1{font-size:29px!important}.flow{flex-wrap:wrap}}
</style>''',unsafe_allow_html=True)

PUBLIC_MODE=deployment_mode()=='public'
DATA=Path(os.getenv('RFP_DATA_DIR',str(ROOT/'data')))
repo=Repository(DATA)
if 'owner_hash' not in st.session_state:
    st.session_state.owner_hash=sha256(str(uuid4()).encode()).hexdigest()
if 'batch_generation' not in st.session_state:
    st.session_state.batch_generation=0
COLORS=['#7053c6','#5c9e8a','#d6a15c','#7690cc','#bd86a6']


def metric(label,value,note=''):
    st.markdown(f'<div class="stat"><small>{escape(label)}</small><strong>{escape(str(value))}</strong><span>{escape(note)}</span></div>',unsafe_allow_html=True)


def empty(title,message):
    st.markdown(f'<div class="empty">◈<b>{escape(title)}</b><p>{escape(message)}</p></div>',unsafe_allow_html=True)


def fmt(value):
    return f'{Decimal(str(value)):.2f}' if value is not None else 'Unavailable'


with st.sidebar:
    st.markdown('<div class="side-brand">◈ ProcureIQ</div><div class="side-sub">PROCUREMENT INTELLIGENCE</div>',unsafe_allow_html=True)
    st.subheader('AI configuration')
    provider_options=['OpenAI · use my key']
    if st.session_state.get('provider_choice') not in provider_options:
        st.session_state.pop('provider_choice',None)
    st.selectbox('Provider',provider_options,key='provider_choice')
    st.caption('Your OpenAI API key is required. It stays in this session only.')
    options=openai_models()
    if st.session_state.get('openai_model') not in options:
        st.session_state.pop('openai_model',None)
    model=st.selectbox('GPT model',options,key='openai_model')
    st.text_input('OpenAI API key',type='password',key='openai_key',help='Session only. Never saved to SQLite, exports or logs.')
    key=st.session_state.get('openai_key','')
    provider={'provider':'openai','model':model}
    if st.button('Clear my key',width='stretch'):
        st.session_state.pop('openai_key',None);st.rerun()
    st.markdown('<div class="mode-card"><small>EVALUATION MODE</small><b>● Live model evaluation</b><p>AI judges proposal evidence.<br>Python calculates every benchmark and rank.</p></div>',unsafe_allow_html=True)
    if st.button('Test connection',width='stretch'):
        try:
            with st.spinner('Checking selected model…'):
                client=make_client(provider,key)
                # Connectivity does not depend on the model choosing JSON formatting.
                # RFP scorecards still pass the strict JSON/evidence validator at F05.
                response=client.evaluate('Reply briefly with OK to confirm that text generation works.')
                text=response.get('text')
                if not isinstance(text,str) or not text.strip():
                    raise ProviderFailure('The selected provider returned no text. Retry Test connection.')
            st.success('Connection verified.')
        except Exception as e:
            st.error(str(e) if isinstance(e,(ProviderFailure,ValueError)) else 'Connection failed. Check provider credentials and model access.')
    st.divider()
    st.caption('RECORDED EXAMPLE')
    sample=ROOT/'sample_output/completed_run.json'
    recorded_sample=json.loads(sample.read_text()) if sample.exists() else None
    if recorded_sample and recorded_sample.get('provider',{}).get('provider')=='openai':
        if st.button('Open recorded OpenAI run',width='stretch'):
            st.session_state.result=recorded_sample;st.session_state.recorded=True
            st.session_state.workspace_tabs='▥  Leaderboard';st.rerun()
        st.caption('Saved OpenAI evidence, not a new model call.')
    else:
        st.caption('Run an evaluation with your key to produce an OpenAI result.')
    st.divider()
    st.caption('YOUR SESSION')
    if st.session_state.get('run_id'):
        st.code(st.session_state.run_id,language=None)
    if st.button('New evaluation',width='stretch'):
        for name in ['result','run_id','recorded','last_submission','eval_error']:
            st.session_state.pop(name,None)
        st.session_state.batch_generation+=1
        st.session_state.workspace_tabs='◫  Criteria'
        st.rerun()
    st.caption('Synthetic proposals only. No contract awards or external actions.')

st.markdown('''<div class="hero"><div class="eyebrow">AGENTIC AI · PROCUREMENT INTELLIGENCE</div><h1>Better evidence. Clearer decisions.</h1><p>Evaluate supplier proposals consistently. Compare the details, understand the gaps,<br>and trace every score back to its source.</p><div class="flow"><b>01 &nbsp; Extract</b> → <b class="ai">02 &nbsp; Evaluate · LLM</b> → <b>03 &nbsp; Validate</b> → <b>04 &nbsp; Rank · Python</b></div></div>''',unsafe_allow_html=True)
criteria=repo.criteria()
try:
    active=validate_criteria(criteria);criteria_error=None
except ValueError as e:
    active=criteria;criteria_error=str(e)
result=st.session_state.get('result')
if result and result.get('provider',{}).get('provider')!='openai':
    st.session_state.pop('result',None)
    st.session_state.pop('recorded',None)
    result=None
cols=st.columns(4)
with cols[0]:metric('Active criteria',len(criteria),'Loaded from SQLite')
with cols[1]:metric('Total weight',f'{sum(Decimal(c["weight"]) for c in criteria):g}%','Must equal 100%')
with cols[2]:metric('Suppliers evaluated',len(result['suppliers']) if result else '—','4–5 proposals per batch')
with cols[3]:metric('Model provider','OpenAI','Your API key · your model')
if st.session_state.get('recorded'):
    st.info('Viewing a recorded OpenAI evaluation. Start a new evaluation to generate fresh results.')
if criteria_error:
    st.error(criteria_error)

tabs=st.tabs(['◫  Criteria','⇧  Supplier input & evaluate','▥  Leaderboard','▤  Detailed scorecards','◷  Run details'],key='workspace_tabs',on_change='rerun')
with tabs[0]:
    left,right=st.columns([1.9,1],gap='large')
    with left:
        st.subheader('Evaluation criteria')
        st.markdown('<div class="section-note">Criteria live in SQLite and feed the evaluation prompt dynamically.<br>Active weights must total 100%; each score is supported by proposal evidence.</div>',unsafe_allow_html=True)
        for i,c in enumerate(criteria):
            color=COLORS[i%len(COLORS)]
            st.markdown(f'''<div class="criterion"><div class="criterion-head"><span class="criterion-title">{escape(c['name'])}</span><span class="criterion-weight">{fmt(c['weight'])}%<span class="max">max {escape(c['max_score'])}</span><span class="active">Active</span></span></div><div class="tag">LLM-SCORED · EVIDENCE REQUIRED</div><div class="bar"><div style="width:100%;background:{color}"></div></div><p>{escape(c['description'])}</p></div>''',unsafe_allow_html=True)
        with st.expander('Configure active criteria and weights'):
            if PUBLIC_MODE or os.getenv('RFP_ALLOW_CRITERIA_EDIT','true').lower()!='true':
                st.caption('Criteria editing is disabled on this deployment. The seed script controls configuration.')
            else:
                with st.form('criteria_editor'):
                    rows=[]
                    for c in repo.criteria(active=False):
                        a,b=st.columns([3,1])
                        enabled=a.checkbox(c['name'],value=bool(c['is_active']),key=f'active_{c["criterion_id"]}')
                        weight=b.number_input('Weight %',min_value=0.0,max_value=100.0,value=float(c['weight']),step=1.0,key=f'weight_{c["criterion_id"]}')
                        rows.append({**c,'is_active':enabled,'weight':str(weight)})
                    if st.form_submit_button('Save criteria',type='primary'):
                        try:repo.update_criteria(rows);st.rerun()
                        except ValueError as e:st.error(str(e))
    with right:
        st.subheader('Active weight distribution')
        fig=go.Figure(go.Pie(labels=[c['name'] for c in criteria],values=[float(c['weight']) for c in criteria],hole=.72,sort=False,marker={'colors':COLORS},textinfo='percent',textfont={'size':12,'color':'white'}))
        fig.update_layout(height=340,margin=dict(l=10,r=10,t=15,b=25),paper_bgcolor='rgba(0,0,0,0)',font={'family':'DM Sans','color':'#6b627c','size':11},legend={'orientation':'h','y':-.15,'x':0},annotations=[{'text':f'<b>{len(criteria)}</b><br>criteria','x':.5,'y':.5,'showarrow':False,'font':{'size':21,'color':'#54406f'}}])
        st.plotly_chart(fig,width='stretch',config={'displayModeBar':False})
        st.markdown('<div class="insight"><b>Evidence first. Arithmetic second.</b>The LLM evaluates proposal content. Weighted scores, peer benchmarks, tie-breaks and final ranks are deterministic Python.<br><br>Historical experience affects ties only.</div>',unsafe_allow_html=True)

with tabs[1]:
    st.subheader('Bring your proposals into focus')
    st.caption('Use the four included fictional proposals or upload 4–5 text-based PDFs. Every supplier is evaluated independently.')
    source=st.radio('Proposal source',['Included fictional proposals','Upload my synthetic PDFs'],horizontal=True,label_visibility='collapsed')
    if source=='Included fictional proposals':
        paths=[ROOT/'fixtures/proposals'/f for f in ['apex_systems.pdf','brightpath_tech.pdf','nexaworks.pdf','orbit_digital.pdf']]
        files=[(p.name,p.read_bytes()) for p in paths if p.exists()]
        names=['Apex Systems','BrightPath Tech','NexaWorks','Orbit Digital']
        package=BytesIO()
        with zipfile.ZipFile(package,'w') as z:
            for filename,data in files:z.writestr(filename,data)
        st.download_button('Download all four sample PDFs',package.getvalue(),'fictional_rfp_proposals.zip','application/zip')
    else:
        uploads=st.file_uploader('Upload 4–5 supplier proposals',type=['pdf'],accept_multiple_files=True,max_upload_size=10)
        files=[(f.name,f.getvalue()) for f in uploads]
        names=[Path(n).stem.replace('_',' ').title() for n,_ in files]
    metadata=[]
    if files:
        st.caption('SUPPLIER METADATA · Date and experience are used only when peer PPI ties.')
        for i,((filename,data),name) in enumerate(zip(files,names)):
            with st.container(border=True):
                a,b,c=st.columns([2,1,1])
                uid=sha256(data).hexdigest()[:12]+str(st.session_state.batch_generation)+str(i)
                supplier_name=a.text_input('Supplier name',value=name,key='name_'+uid)
                a.caption(filename)
                submitted=b.date_input('Submission date',date(2026,10,12+min(i,3)),key='date_'+uid)
                experience=c.number_input('Experience rating / 10',min_value=0.0,max_value=10.0,value=[8.0,3.0,8.0,9.0][i%4],step=.5,key='experience_'+uid)
                metadata.append({'supplier_name':supplier_name,'submission_date':submitted.isoformat(),'experience_rating':str(experience)})
    if st.session_state.get('eval_error'):st.error(st.session_state.eval_error)
    if len(files) not in (4,5):st.warning('Choose exactly 4 or 5 supplier PDFs to evaluate.')
    st.caption('Evaluation sends extracted synthetic proposal text to the selected provider. Industry comparison uses labelled illustrative targets.')
    if st.button('Evaluate proposals →',type='primary',disabled=len(files) not in (4,5) or bool(criteria_error),width='stretch'):
        try:
            st.session_state.pop('eval_error',None)
            st.session_state.pop('result',None)
            st.session_state.recorded=False
            client=make_client(provider,key)
            fingerprint=sha256(json.dumps({'files':[sha256(d).hexdigest() for _,d in files],'metadata':metadata,'provider':provider},sort_keys=True).encode()).hexdigest()
            if st.session_state.get('last_submission')==fingerprint and st.session_state.get('run_id'):
                run_id=st.session_state.run_id
            else:
                run_id=prepare_run(repo,st.session_state.owner_hash,files,metadata,provider)
                st.session_state.run_id=run_id;st.session_state.last_submission=fingerprint
            with st.status('Evaluating supplier proposals…',expanded=True) as status:
                def progress(node,values):
                    from rfp.graph.build import EVENT_IDS
                    st.write(f'{EVENT_IDS.get(node,node)} · {node.replace("_"," ")}')
                completed=execute_run(repo,run_id,st.session_state.owner_hash,client,progress)
                status.update(label='Evaluation complete',state='complete',expanded=False)
            st.session_state.result=completed;st.session_state.recorded=False
            st.success('Complete results saved. Open Leaderboard or Detailed scorecards to inspect them.')
            st.rerun()
        except Exception as e:
            st.session_state.eval_error=str(e) if isinstance(e,(ValueError,ProviderFailure)) else 'Evaluation interrupted. No partial leaderboard is shown; check configuration and run details.'
            st.rerun()
    if st.session_state.get('run_id'):
        owned=repo.run(st.session_state.run_id,st.session_state.owner_hash)
        if owned['status']=='running' and st.button('Resume interrupted evaluation'):
            try:
                saved_provider=json.loads(owned['provider_json'])
                if saved_provider!=provider:raise ValueError('Select the original provider/model before resuming.')
                client=make_client(provider,key)
                with st.spinner('Resuming saved LangGraph state…'):
                    st.session_state.result=execute_run(repo,owned['rfp_run_id'],st.session_state.owner_hash,client)
                st.session_state.recorded=False;st.rerun()
            except Exception as e:st.error(str(e) if isinstance(e,(ValueError,ProviderFailure)) else 'Resume failed; saved run remains available.')
        if owned['status']=='failed':st.warning('This run failed and has no leaderboard. Use New evaluation after correcting the issue.')

with tabs[2]:
    st.subheader('Supplier leaderboard')
    st.caption('Ranked by peer PPI, then earlier submission, higher experience and supplier name. Scores are displayed to two decimals; sorting uses full precision.')
    if not result:empty('Your shortlist starts here','Evaluate the proposals to see an evidence-backed supplier comparison.')
    else:
        winner=result['suppliers'][0]
        a,b,c=st.columns(3)
        a.metric('Top-ranked supplier',winner['supplier_name'])
        a.caption(f'Peer PPI: {fmt(winner["ppi"])} / 100')
        b.metric('Suppliers compared',len(result['suppliers']))
        c.metric('Validation warnings',len(result['warnings']))
        st.dataframe(pd.DataFrame([{'Rank':s['final_rank'],'Supplier':s['supplier_name'],'Weighted score':float(s['absolute_score']),'Peer PPI':float(s['ppi']),'Industry index':float(s['industry_index']) if s['industry_index'] else None,'Submission date':s['submission_date'],'Experience':float(s['experience_rating'])} for s in result['suppliers']]),hide_index=True,width='stretch',column_config={name:st.column_config.NumberColumn(format='%.2f') for name in ['Weighted score','Peer PPI','Industry index','Experience']})
        st.caption('Industry index: illustrative classroom baseline, not measured industry averages. It does not affect rank; an index above 100 is possible.')
        chart=go.Figure()
        chart.add_bar(name='Absolute weighted score',x=[s['supplier_name'] for s in result['suppliers']],y=[float(s['absolute_score']) for s in result['suppliers']],marker_color='#b8a6df')
        chart.add_bar(name='Peer PPI',x=[s['supplier_name'] for s in result['suppliers']],y=[float(s['ppi']) for s in result['suppliers']],marker_color='#6746bd')
        chart.update_layout(height=300,barmode='group',paper_bgcolor='rgba(0,0,0,0)',plot_bgcolor='rgba(0,0,0,0)',yaxis={'range':[0,105],'gridcolor':'#eee9f5'},legend={'orientation':'h','y':1.15},margin=dict(l=10,r=10,t=35,b=10))
        st.plotly_chart(chart,width='stretch',config={'displayModeBar':False})

with tabs[3]:
    st.subheader('Every score, explained')
    if not result:empty('Evidence will appear here','Inspect criterion scores, quotations, gaps and validation warnings after evaluation.')
    else:
        selected=st.selectbox('Supplier',[s['supplier_name'] for s in result['suppliers']],key='detail_supplier')
        card=next(s for s in result['suppliers'] if s['supplier_name']==selected)
        st.write(card['overall_summary'])
        rows=[{'Criterion':c['name'],'Raw score':c['score'],'Maximum':c['max_score'],'Weight %':c['weight'],'Weighted contribution':fmt(c['weighted_score']),'Peer benchmark':c['benchmark'],'Peer gap':c['gap'],'Relative %':fmt(c['relative_percentage']),'Industry target':c['industry_target'],'Industry gap':c['industry_gap']} for c in card['criteria']]
        st.dataframe(pd.DataFrame(rows),hide_index=True,width='stretch')
        st.caption(card['industry_source'])
        for c in card['criteria']:
            with st.expander(f'{c["name"]} · {c["score"]}/{c["max_score"]} · {"verified quotation" if c["evidence_verified"] else "no verified quotation"}',expanded=False):
                st.write(c['justification'])
                if c['evidence']:
                    st.text(c['evidence'])
                    st.caption(f'Source: {card["filename"]} · pages {", ".join(map(str,c["evidence_pages"])) or "unverified"}')
                st.caption(f'Industry relative performance: {fmt(c["industry_relative_percentage"])}% · Raw model score: {c["raw_score"]}')
                for w in c['warnings']:st.warning(w)
        if card['risks']:
            st.markdown('**Supplier risks / clarification points**')
            for risk in card['risks']:st.write('• '+risk)

with tabs[4]:
    st.subheader('Run details & audit trail')
    if not result:
        empty('Follow the workflow','A completed run includes the frozen criteria, model identity, warnings and numbered graph events.')
        if st.session_state.get('run_id'):
            owned=repo.run(st.session_state.run_id,st.session_state.owner_hash)
            st.write('Status:',owned['status'])
            if owned['error_json']:st.json(json.loads(owned['error_json']))
            st.dataframe(repo.events(owned['rfp_run_id'],st.session_state.owner_hash),hide_index=True)
    else:
        st.code(result['rfp_run_id'],language=None)
        st.caption(f'Provider: {result["provider"]["provider"]} · Model: {result["provider"]["model"]} · Status: {result["status"]}')
        st.write(result['suppliers'][0]['ranking_explanation'])
        st.info(result['reproducibility_note'])
        st.download_button('Download complete run · JSON',json.dumps(result,indent=2,ensure_ascii=False),f'rfp_run_{result["rfp_run_id"]}.json','application/json',type='primary')
        with st.expander('Numbered workflow events',expanded=True):st.dataframe(pd.DataFrame(result['events']),hide_index=True,width='stretch')
        with st.expander(f'Validation warnings ({len(result["warnings"])})'):
            if not result['warnings']:st.success('No normalization warnings in this run.')
            for warning in result['warnings']:st.warning(warning)
        with st.expander('Frozen criteria and provider settings'):st.json({'criteria':result['criteria'],'criteria_hash':result['criteria_hash'],'provider':result['provider']})
        with st.expander('Complete result'):st.json(result,expanded=False)

st.markdown('<div class="footnote">PROCUREIQ · CLASSROOM MINI PROJECT &nbsp; / &nbsp; Synthetic proposals · Evidence-backed evaluation · Human procurement decisions</div>',unsafe_allow_html=True)
