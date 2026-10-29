from pathlib import Path
import argparse
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from rfp.persistence.db import Repository
parser=argparse.ArgumentParser(description='Idempotent SQLite schema creation and sample criteria seeding.')
parser.add_argument('--data-dir',default='data')
args=parser.parse_args()
repo=Repository(args.data_dir)
print(f'SQLite ready; {len(repo.criteria())} active criteria. Existing weights preserved.')
