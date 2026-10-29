"""Inspect Git index blobs before publication; report locations, never secret values."""
import argparse
import fnmatch
from io import BytesIO
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
BLOCKED = (
    'local.md', '.env', '.env.*', '*.key', '*.pem', '*.p12', '*.pfx', '*.jks',
    '*.db', '*.db-*', '*.sqlite*', '*.log', '.streamlit/secrets.toml',
    '.streamlit/secrets.*.toml', 'data/*', 'uploads/*', 'artifacts/*',
    'sample_output/*', 'screenshots/*', '.venv/*', '.oci/*', '*__pycache__/*',
)
PATTERNS = {
    'OpenAI-style key': r'\bsk-[A-Za-z0-9_-]{20,}',
    'GitHub token': r'\b(?:gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,})',
    'AWS access key': r'\b(?:AKIA|ASIA)[A-Z0-9]{16}\b',
    'Google API key': r'\bAIza[A-Za-z0-9_-]{30,}',
    'private key': r'-----BEGIN (?:RSA |EC |OPENSSH |ENCRYPTED )?PRIVATE KEY-----',
    'cloud resource identifier': r'\bocid1\.[a-z0-9]+\.[a-z0-9.]+',
    'personal absolute path': r'(?:/Users/|/home/|[A-Z]:\\Users\\)[A-Za-z0-9_.-]+',
    'credential in URL': r'https?://[^\s/:]+:[^\s/@]+@',
}


def git(*args):
    return subprocess.check_output(['git', *args], cwd=ROOT)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--staged', action='store_true', help='Scan exactly the next commit content.')
    args = parser.parse_args()
    if args.staged:
        names = git('diff', '--cached', '--name-only', '--diff-filter=ACMR', '-z')
    else:
        names = git('ls-files', '-z')
    paths = [n.decode() for n in names.split(b'\0') if n]
    if not paths:
        print('Nothing to audit. Stage the release files first.')
        return 1
    findings = []
    for name in paths:
        if name != '.streamlit/secrets.example.toml' and any(fnmatch.fnmatch(name, p) for p in BLOCKED):
            findings.append((name, 'private artifact filename'))
        data = git('show', ':' + name)
        if name.endswith('.pdf'):
            if not name.startswith('fixtures/proposals/'):
                findings.append((name, 'PDF outside approved fictional fixtures'))
            from pypdf import PdfReader
            reader = PdfReader(BytesIO(data))
            text = str(reader.metadata) + '\n' + '\n'.join(p.extract_text() or '' for p in reader.pages)
        else:
            try:
                text = data.decode('utf-8')
            except UnicodeDecodeError:
                findings.append((name, 'unreviewed binary file'))
                continue
        for label, pattern in PATTERNS.items():
            if re.search(pattern, text):
                findings.append((name, label))
    for name, label in findings:
        print(f'BLOCKED: {name}: {label}')
    if findings:
        print(f'Audit failed: {len(findings)} finding(s). No matched values were printed.')
        return 1
    print(f'PASS: {len(paths)} staged/index files checked, including PDF text and metadata. No configured sensitive patterns found.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
