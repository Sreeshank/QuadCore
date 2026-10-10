from pathlib import Path
import sys
root = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(root / 'backend'))
from app.services.demo import SAMPLES, sample_pdf
for name in SAMPLES:
    (root / 'sample_documents' / name).write_bytes(sample_pdf(name))
print(f'Generated {len(SAMPLES)} synthetic sample PDFs in sample_documents/.')

