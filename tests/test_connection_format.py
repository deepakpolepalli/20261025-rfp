from types import SimpleNamespace
import pytest
from test_ui import app_at,button


@pytest.mark.parametrize('answer',['OK','```json\n{"status":"ok"}\n```'])
def test_connection_accepts_successful_text_without_requiring_json(monkeypatch,tmp_path,answer):
    import openai
    class SDK:
        def __init__(self,**kwargs):
            self.responses=SimpleNamespace(create=lambda **kwargs:SimpleNamespace(
                status='completed',output_text=answer,model=kwargs['model'],usage=None,id='test-id'))
    monkeypatch.setattr(openai,'OpenAI',SDK)
    app=app_at(monkeypatch,tmp_path)
    app.selectbox(key='provider_choice').select('OpenAI · use my key').run()
    app.selectbox(key='openai_model').select('gpt-4o-mini').run()
    app.text_input(key='openai_key').set_value('CANARY-KEY-NOT-REAL').run()
    button(app,'Test connection').click().run()
    assert not app.exception and not app.error
    assert any('Connection verified' in x.value for x in app.success)


def test_connection_empty_response_is_not_reported_as_success(monkeypatch,tmp_path):
    import rfp.clients.llm
    monkeypatch.setattr(rfp.clients.llm,'make_client',lambda *args,**kwargs:SimpleNamespace(evaluate=lambda prompt:{'text':' '}))
    app=app_at(monkeypatch,tmp_path)
    button(app,'Test connection').click().run()
    assert not app.exception
    assert any('returned no text' in x.value for x in app.error)
    assert not app.success
