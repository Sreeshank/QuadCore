from pathlib import Path
import httpx
from app.core.config import settings


def _headers():
    return {'apikey': settings.supabase_service_role_key, 'Authorization': f'Bearer {settings.supabase_service_role_key}'}


def _local(key: str) -> Path:
    root = settings.storage_dir.resolve()
    path = (root / key).resolve()
    if not path.is_relative_to(root):
        raise ValueError('Invalid storage path')
    return path


def put(key: str, data: bytes, mime: str):
    if settings.storage_backend == 'supabase':
        with httpx.Client(timeout=30) as client:
            response = client.post(f'{settings.supabase_url}/storage/v1/object/{settings.supabase_bucket}/{key}', headers={**_headers(), 'Content-Type': mime}, content=data)
            response.raise_for_status()
    else:
        path = _local(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)


def read(key: str) -> bytes:
    if settings.storage_backend == 'supabase':
        with httpx.Client(timeout=30) as client:
            response = client.get(f'{settings.supabase_url}/storage/v1/object/authenticated/{settings.supabase_bucket}/{key}', headers=_headers())
            response.raise_for_status()
            return response.content
    return _local(key).read_bytes()


def delete(key: str):
    if settings.storage_backend == 'supabase':
        with httpx.Client(timeout=30) as client:
            response = client.delete(f'{settings.supabase_url}/storage/v1/object/{settings.supabase_bucket}', headers=_headers(), json={'prefixes': [key]})
            response.raise_for_status()
    else:
        _local(key).unlink(missing_ok=True)


def ensure_private_bucket():
    if settings.storage_backend != 'supabase':
        return
    response = httpx.get(f'{settings.supabase_url}/storage/v1/bucket/{settings.supabase_bucket}', headers=_headers(), timeout=15)
    response.raise_for_status()
    if response.json().get('public') is not False:
        raise RuntimeError('TaxReady requires a private Supabase bucket. Refusing public storage.')
