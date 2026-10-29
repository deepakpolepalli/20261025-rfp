"""Public entry point: visitor OpenAI BYOK only, with session-scoped credentials."""
import os
from pathlib import Path
import runpy

os.environ['RFP_DEPLOYMENT_MODE']='public'
runpy.run_path(str(Path(__file__).with_name('app.py')),run_name='__main__')
