from pathlib import Path
from streamlit.testing.v1 import AppTest
from test_core import FakeClient

ROOT=Path(__file__).resolve().parents[1]


def app_at(monkeypatch,tmp_path):
    monkeypatch.setenv('RFP_DEPLOYMENT_MODE','local')
    monkeypatch.setenv('RFP_DATA_DIR',str(tmp_path))
    return AppTest.from_file(str(ROOT/'app.py'),default_timeout=30).run()


def button(app,label):
    return next(b for b in app.button if b.label==label)


def test_initial_ui_has_all_sections_and_no_provider_call(monkeypatch,tmp_path):
    app=app_at(monkeypatch,tmp_path)
    assert not app.exception
    assert len(app.tabs)==5
    assert app.selectbox(key='provider_choice').options==['OpenAI · use my key']
    assert any(x.label=='OpenAI API key' for x in app.text_input)


def test_ui_evaluation_uses_graph_and_displays_complete_results(monkeypatch,tmp_path):
    import rfp.clients.llm
    fake=FakeClient()
    monkeypatch.setattr(rfp.clients.llm,'make_client',lambda provider,key='',**kwargs:fake)
    app=app_at(monkeypatch,tmp_path)
    button(app,'Evaluate proposals →').click().run()
    assert not app.exception
    assert fake.calls==4
    assert app.session_state['result']['status']=='completed'
    assert len(app.session_state['result']['suppliers'])==4
    assert len(app.dataframe)>=3
    button(app,'New evaluation').click().run()
    assert not app.exception
    assert 'result' not in app.session_state


def test_invalid_weights_are_explained_without_saving(monkeypatch,tmp_path):
    app=app_at(monkeypatch,tmp_path)
    app.number_input(key='weight_1').set_value(29.0)
    button(app,'Save criteria').click().run()
    assert not app.exception
    assert any('100%' in e.value for e in app.error)
    from rfp.persistence.db import Repository
    assert Repository(tmp_path).criteria()[0]['weight']=='30'


def test_openai_missing_key_shows_clear_error_and_no_run(monkeypatch,tmp_path):
    app=app_at(monkeypatch,tmp_path)
    app.selectbox(key='provider_choice').select('OpenAI · use my key').run()
    assert any(x.label=='OpenAI API key' for x in app.text_input)
    button(app,'Evaluate proposals →').click().run()
    assert not app.exception
    assert any('OpenAI API key' in e.value for e in app.error)
    from rfp.persistence.db import Repository
    with Repository(tmp_path).connect() as c:
        assert c.execute('SELECT COUNT(*) FROM rfp_runs').fetchone()[0]==0


def test_connection_check_accepts_gpt4o_mini_and_session_key(monkeypatch,tmp_path):
    import openai
    from types import SimpleNamespace
    captured={}
    class SDK:
        def __init__(self,**kwargs):
            captured.update(kwargs)
            self.responses=SimpleNamespace(create=self.create)
        def create(self,**kwargs):
            captured['model']=kwargs['model']
            return SimpleNamespace(status='completed',output_text='{"status":"ok"}',model=kwargs['model'],usage=None,id='test-id')
    monkeypatch.setattr(openai,'OpenAI',SDK)
    app=app_at(monkeypatch,tmp_path)
    app.selectbox(key='provider_choice').select('OpenAI · use my key').run()
    app.selectbox(key='openai_model').select('gpt-4o-mini').run()
    app.text_input(key='openai_key').set_value('CANARY-NOT-REAL').run()
    button(app,'Test connection').click().run()
    assert not app.exception
    assert any('Connection verified' in x.value for x in app.success)
    assert captured['api_key']=='CANARY-NOT-REAL' and captured['model']=='gpt-4o-mini'
