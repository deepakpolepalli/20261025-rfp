from types import SimpleNamespace
import pytest
from rfp.clients.llm import OpenAIClient,ProviderFailure,safe_failure
from rfp.provider_policy import openai_models


@pytest.mark.parametrize('mode',['local','public'])
def test_every_displayed_model_is_accepted_by_client(monkeypatch,mode):
    import openai
    monkeypatch.setenv('RFP_DEPLOYMENT_MODE',mode)
    received=[]
    monkeypatch.setattr(openai,'OpenAI',lambda **kwargs:received.append(kwargs) or SimpleNamespace())
    for model in openai_models():
        OpenAIClient('  CANARY-NOT-A-REAL-KEY\n',model)
    assert len(received)==len(openai_models())
    assert all(x['api_key']=='CANARY-NOT-A-REAL-KEY' for x in received)
    assert all(x['base_url']=='https://api.openai.com/v1' for x in received)


def test_auth_error_does_not_echo_rejected_key():
    error=SimpleNamespace(status_code=401,code='invalid_api_key',body={'message':'Rejected CANARY-SECRET-KEY'})
    result=safe_failure(error,'OpenAI')
    assert 'HTTP 401' in str(result) and 'API key' in str(result)
    assert 'CANARY-SECRET-KEY' not in str(result) and not result.retryable


def test_quota_and_rate_limit_have_different_retry_policy():
    quota=safe_failure(SimpleNamespace(status_code=429,code='insufficient_quota'),'OpenAI')
    throttle=safe_failure(SimpleNamespace(status_code=429,code='rate_limit_exceeded'),'OpenAI')
    assert not quota.retryable and throttle.retryable
    assert 'billing' in str(quota)


def test_quoted_or_header_key_is_rejected_before_client_creation(monkeypatch):
    import openai
    def forbidden(**kwargs):
        raise AssertionError('Provider client should not be constructed')
    monkeypatch.setattr(openai,'OpenAI',forbidden)
    for key in ['"CANARY-KEY"','Bearer CANARY-KEY','CANARY KEY']:
        with pytest.raises(ProviderFailure,match='Paste only'):
            OpenAIClient(key,'gpt-4o-mini')
