from pathlib import Path
import pytest
from streamlit.testing.v1 import AppTest

ROOT=Path(__file__).resolve().parents[1]


def test_public_entrypoint_only_offers_visitor_key_and_requested_model(monkeypatch,tmp_path):
    monkeypatch.setenv('RFP_DATA_DIR',str(tmp_path))
    monkeypatch.setenv('RFP_DEPLOYMENT_MODE','local')
    app=AppTest.from_file(str(ROOT/'streamlit_public.py'),default_timeout=30).run()
    assert not app.exception
    assert app.selectbox(key='provider_choice').options==['OpenAI · use my key']
    assert app.selectbox(key='openai_model').options==['gpt-4o-mini']
    assert any(x.label=='OpenAI API key' for x in app.text_input)
    assert not any(b.label=='Save criteria' for b in app.button)
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
