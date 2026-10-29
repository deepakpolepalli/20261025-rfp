"""OpenAI-only provider policy for local and public entry points."""
import os


def deployment_mode():
    mode=os.getenv('RFP_DEPLOYMENT_MODE','local').strip().lower()
    if mode not in ('local','public'):
        raise ValueError('RFP_DEPLOYMENT_MODE must be local or public.')
    return mode


def openai_models():
    return [m.strip() for m in os.getenv('RFP_OPENAI_MODELS','gpt-4o-mini,gpt-4.1-mini,gpt-4.1').split(',') if m.strip()]


def validate_provider(provider):
    if provider.get('provider')!='openai':
        raise ValueError('This app supports OpenAI API-key authentication only.')
    if provider.get('provider')=='openai' and provider.get('model') not in openai_models():
        raise ValueError('Selected OpenAI model is not allowed in this deployment.')
