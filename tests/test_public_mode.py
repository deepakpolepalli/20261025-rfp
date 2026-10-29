from pathlib import Path
import pytest
from streamlit.testing.v1 import AppTest

ROOT=Path(__file__).resolve().parents[1]


def test_public_entrypoint_offers_models_key_and_editable_criteria(monkeypatch,tmp_path):
    monkeypatch.setenv('RFP_DATA_DIR',str(tmp_path))
    monkeypatch.setenv('RFP_DEPLOYMENT_MODE','local')
    app=AppTest.from_file(str(ROOT/'streamlit_public.py'),default_timeout=30).run()
    assert not app.exception
    assert app.selectbox(key='provider_choice').options==['OpenAI · use my key']
    assert app.selectbox(key='openai_model').options==['gpt-4o-mini','gpt-4.1-mini','gpt-4.1']
    app.selectbox(key='openai_model').select('gpt-4.1').run()
    assert not app.exception
    assert app.selectbox(key='openai_model').value=='gpt-4.1'
    assert any(x.label=='OpenAI API key' for x in app.text_input)
    assert any(b.label=='Save criteria' for b in app.button)
    next(b for b in app.button if b.label=='Evaluate proposals →').click().run()
    assert not app.exception
    assert any('OpenAI API key' in e.value for e in app.error)


def test_public_mode_blocks_oci_before_client_creation(monkeypatch):
    from rfp.clients.llm import make_client
    monkeypatch.setenv('RFP_DEPLOYMENT_MODE','public')
    with pytest.raises(ValueError,match='supports OpenAI'):
        make_client({'provider':'oci','model':'openai.gpt-oss-120b','region':'eu-frankfurt-1'})


def test_public_mode_blocks_oci_run_creation(monkeypatch,tmp_path):
    from rfp.services.runs import prepare_run
    from rfp.persistence.db import Repository
    monkeypatch.setenv('RFP_DEPLOYMENT_MODE','public')
    repo=Repository(tmp_path)
    with pytest.raises(ValueError,match='supports OpenAI'):
        prepare_run(repo,'owner',[],[],{'provider':'oci','model':'openai.gpt-oss-120b'})
    with repo.connect() as c:
        assert c.execute('SELECT COUNT(*) FROM rfp_runs').fetchone()[0]==0


def test_public_mode_cannot_resume_an_old_oci_run(monkeypatch,tmp_path):
    from test_core import prepared,FakeClient
    from rfp.services.runs import execute_run
    from rfp.persistence.db import Repository
    monkeypatch.setenv('RFP_DEPLOYMENT_MODE','local')
    repo=Repository(tmp_path);run_id=prepared(repo)
    with repo.connect() as connection:
        import json
        connection.execute('UPDATE rfp_runs SET provider_json=? WHERE rfp_run_id=?',(json.dumps({'provider':'oci','model':'openai.gpt-oss-120b'}),run_id))
    monkeypatch.setenv('RFP_DEPLOYMENT_MODE','public')
    client=FakeClient()
    with pytest.raises(ValueError,match='supports OpenAI'):
        execute_run(repo,run_id,'owner',client)
    assert client.calls==0


@pytest.mark.parametrize('mode',['local','public'])
def test_unsupported_provider_is_rejected_in_all_modes(monkeypatch,mode):
    from rfp.clients.llm import make_client
    monkeypatch.setenv('RFP_DEPLOYMENT_MODE',mode)
    with pytest.raises(ValueError,match='supports OpenAI'):
        make_client({'provider':'oci','model':'unsupported'})


def public_app(monkeypatch,tmp_path):
    monkeypatch.setenv('RFP_DATA_DIR',str(tmp_path))
    monkeypatch.delenv('RFP_ALLOW_CRITERIA_EDIT',raising=False)
    return AppTest.from_file(str(ROOT/'streamlit_public.py'),default_timeout=30).run()


def test_public_weight_edits_are_isolated_and_frozen_per_run(monkeypatch,tmp_path):
    from rfp.persistence.db import Repository
    from test_core import prepared
    first=public_app(monkeypatch,tmp_path)
    second=public_app(monkeypatch,tmp_path)
    assert not first.exception and not second.exception
    first_repo=Repository(tmp_path/'sessions'/first.session_state['owner_hash'])
    second_repo=Repository(tmp_path/'sessions'/second.session_state['owner_hash'])
    assert first_repo.directory!=second_repo.directory
    run_id=prepared(first_repo)
    before,_=first_repo.freeze(run_id,'owner')
    first.number_input(key='weight_1').set_value(40.0)
    first.number_input(key='weight_2').set_value(10.0)
    next(b for b in first.button if b.label=='Save criteria').click().run()
    assert not first.exception
    assert first_repo.criteria()[0]['weight']=='40.0'
    assert second_repo.criteria()[0]['weight']=='30'
    frozen,_=first_repo.freeze(run_id,'owner')
    assert frozen==before
    new_run_id=prepared(first_repo)
    new_snapshot,_=first_repo.freeze(new_run_id,'owner')
    assert str(new_snapshot[0]['weight'])=='40.0'
    next(b for b in first.button if b.label=='New evaluation').click().run()
    assert not first.exception
    assert first.number_input(key='weight_1').value==40.0
    third=public_app(monkeypatch,tmp_path)
    assert third.number_input(key='weight_1').value==30.0


def test_public_invalid_weight_total_does_not_save(monkeypatch,tmp_path):
    from rfp.persistence.db import Repository
    app=public_app(monkeypatch,tmp_path)
    app.number_input(key='weight_1').set_value(29.0)
    next(b for b in app.button if b.label=='Save criteria').click().run()
    assert not app.exception
    assert any('100%' in e.value for e in app.error)
    assert Repository(tmp_path/'sessions'/app.session_state['owner_hash']).criteria()[0]['weight']=='30'


def test_operator_can_disable_public_editor(monkeypatch,tmp_path):
    monkeypatch.setenv('RFP_DATA_DIR',str(tmp_path))
    monkeypatch.setenv('RFP_ALLOW_CRITERIA_EDIT','false')
    app=AppTest.from_file(str(ROOT/'streamlit_public.py'),default_timeout=30).run()
    assert not app.exception
    assert not any(b.label=='Save criteria' for b in app.button)


@pytest.mark.parametrize('model',['gpt-4o-mini','gpt-4.1-mini','gpt-4.1'])
def test_public_backend_accepts_each_model(monkeypatch,model):
    from rfp.provider_policy import validate_provider
    monkeypatch.setenv('RFP_DEPLOYMENT_MODE','public')
    monkeypatch.delenv('RFP_OPENAI_MODELS',raising=False)
    validate_provider({'provider':'openai','model':model})
