"""Common response contract; clients are runtime-only, never serialized."""
from rfp.provider_policy import openai_models, validate_provider


class ProviderFailure(RuntimeError):
    def __init__(self, message, retryable=False):
        super().__init__(message)
        self.retryable=retryable


def safe_failure(error,provider='Provider'):
    status=getattr(error,'status',None) or getattr(error,'status_code',None)
    # Only expose known, non-sensitive error codes; never provider body/message,
    # which can contain the rejected credential or request text.
    code=getattr(error,'code',None)
    retryable=status in (408,429,500,502,503,504) or 'timeout' in type(error).__name__.lower() or 'connection' in type(error).__name__.lower()
    if provider=='OpenAI':
        if status==401:
            return ProviderFailure('OpenAI rejected the API key (HTTP 401). Re-enter an active OpenAI Platform API key for the correct project. Check for a revoked key or copied quotation marks. No model or provider fallback was attempted.')
        if status==403:
            return ProviderFailure('OpenAI denied access (HTTP 403). Check the API project model permissions and regional availability.')
        if status==404:
            return ProviderFailure('The selected OpenAI model/resource is unavailable to this key (HTTP 404). No substitute model was used.')
        if status==429 and code=='insufficient_quota':
            return ProviderFailure('OpenAI API quota is exhausted (HTTP 429). Check the API project billing and spending limits; this is not a model-selection error.')
        if status==429:
            return ProviderFailure('OpenAI rate limit reached (HTTP 429). Retry later within the request budget.',True)
    label={401:'Authentication failed.',403:'Permission denied.',404:'Model or resource unavailable.',429:'Provider rate limit reached.'}.get(status,'Provider request failed.')
    return ProviderFailure(f'{label} Check the selected provider, credentials and model. No provider fallback was attempted.',retryable)


class OpenAIClient:
    def __init__(self,key,model):
        from openai import OpenAI
        allowed=openai_models()
        key=key.strip() if isinstance(key,str) else ''
        if not key:
            raise ProviderFailure('Enter your OpenAI API key before using OpenAI BYOK.')
        if key.startswith(('"', "'")) or any(ch.isspace() for ch in key):
            raise ProviderFailure('Paste only the OpenAI API key, without quotation marks, a Bearer prefix or internal whitespace.')
        if model not in allowed:
            raise ProviderFailure(f'The selected model ({model}) is not allowed by the current server policy. Allowed models: {", ".join(allowed)}. Restart the app if its model options were recently updated.')
        self.model=model
        self.client=OpenAI(api_key=key,base_url='https://api.openai.com/v1',timeout=90,max_retries=0)

    def evaluate(self,prompt):
        try:
            response=self.client.responses.create(model=self.model,input=prompt,max_output_tokens=8192,store=False)
            if response.status!='completed' or not response.output_text:
                raise ProviderFailure('OpenAI response incomplete; no scorecard was accepted.')
            return {'text':response.output_text,'provider':'openai','requested_model':self.model,
                    'returned_model':response.model,'usage':response.usage.model_dump() if response.usage else {},'safe_request_id':response.id}
        except ProviderFailure:
            raise
        except Exception as e:
            raise safe_failure(e,'OpenAI') from None


def make_client(provider,key=''):
    validate_provider(provider)
    return OpenAIClient(key,provider['model'])
