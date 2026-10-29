from hashlib import sha256
from io import BytesIO
from pathlib import Path
from pypdf import PdfReader


def extract_document(data, expected_hash=None):
    if not isinstance(data,bytes) or not data or len(data)>10*1024*1024:
        raise ValueError('PDF must be non-empty and no larger than 10 MiB.')
    if not data.startswith(b'%PDF-'):
        raise ValueError('The file is not a PDF.')
    if expected_hash and sha256(data).hexdigest()!=expected_hash:
        raise ValueError('Document integrity check failed.')
    try:
        reader=PdfReader(BytesIO(data))
        if reader.is_encrypted:
            raise ValueError('Encrypted PDFs are not supported; upload an unlocked text PDF.')
        if not 1<=len(reader.pages)<=40:
            raise ValueError('Supported PDFs contain 1-40 pages.')
        pages=[{'page':i+1,'text':p.extract_text() or ''} for i,p in enumerate(reader.pages)]
    except ValueError:
        raise
    except Exception:
        raise ValueError('PDF could not be read. Upload a valid text-based PDF.') from None
    if not any(p['text'].strip() for p in pages):
        raise ValueError('No extractable text found. Scanned PDFs require OCR, which is outside this mini-project.')
    if sum(len(p['text']) for p in pages)>120000:
        raise ValueError('Proposal exceeds the 120,000-character limit; text was not truncated.')
    return pages


def read_artifact(repo, ref):
    path=(repo.directory/ref).resolve()
    if not path.is_relative_to(repo.artifacts.resolve()):
        raise ValueError('Invalid artifact reference.')
    return path.read_bytes()
