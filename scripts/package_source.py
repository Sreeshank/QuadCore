"""Package distributable source, excluding credentials and runtime financial data."""
import os
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
root = Path(__file__).resolve().parents[1]
output = root.parent / 'TaxReady-AI.zip'
excluded = {'.venv', 'node_modules', 'dist', 'data', '.git', '__pycache__', '.pytest_cache', 'test-results', 'playwright-report'}
with ZipFile(output,'w',compression=ZIP_DEFLATED) as archive:
    for current, folders, files in os.walk(root):
        folders[:] = [name for name in folders if name not in excluded]
        for name in files:
            if name == '.env' or name.endswith(('.db','.db-shm','.db-wal','.zip','.tsbuildinfo','.pyc')):
                continue
            path = Path(current) / name
            archive.write(path, Path('taxready-ai') / path.relative_to(root))
with ZipFile(output) as archive:
    names = archive.namelist()
    assert 'taxready-ai/README.md' in names
    assert 'taxready-ai/sample_documents/form16.pdf' in names
    assert not any('/data/' in name or '/node_modules/' in name or name.endswith('/.env') for name in names)
print(f'Source archive: {output} ({output.stat().st_size:,} bytes; {len(names)} files)')

