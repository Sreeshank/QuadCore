from collections import defaultdict, deque
from contextlib import asynccontextmanager
import hashlib
import time
import httpx
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.db.session import Base, engine
from app.api.routes import router
from app.api.workspace import router as workspace_router
from app.services.storage import ensure_private_bucket


@asynccontextmanager
async def lifespan(app):
    settings.validate_runtime()
    ensure_private_bucket()
    if settings.app_env != 'production':
        Base.metadata.create_all(engine)
    yield


app = FastAPI(title='TaxReady AI API',version='1.0.0',description='Document intelligence and preparation guidance. No tax filing or tax advice.',lifespan=lifespan)
app.add_middleware(CORSMiddleware,allow_origins=[v.strip() for v in settings.cors_origins.split(',')],allow_credentials=False,allow_methods=['GET','POST','PUT','PATCH','DELETE','OPTIONS'],allow_headers=['Authorization','Content-Type','X-Assistant-Api-Key'])
buckets = defaultdict(deque)


@app.middleware('http')
async def guardrails(request: Request, call_next):
    if request.method != 'OPTIONS' and request.url.path.startswith('/api/'):
        now = time.monotonic()
        client = request.client.host if request.client else 'unknown'
        credential = '' if request.url.path == '/api/v1/auth/demo' else request.headers.get('authorization','')
        key = client + ':' + hashlib.sha256(credential.encode()).hexdigest()
        if len(buckets) > 10000:
            for old_key in list(buckets):
                if not buckets[old_key] or buckets[old_key][-1] < now - 60:
                    del buckets[old_key]
        bucket = buckets[key]
        while bucket and bucket[0] < now - 60:
            bucket.popleft()
        if len(bucket) >= settings.rate_limit:
            return JSONResponse(status_code=429,content={'detail':'Too many requests. Try again in one minute.'},headers={'Retry-After':'60'})
        bucket.append(now)
        if request.method in {'POST','PUT','PATCH'}:
            limit = (settings.max_upload_mb * 1024 * 1024 + 65536) if request.url.path.endswith('/upload') else 65536
            chunks = []
            length = 0
            async for chunk in request.stream():
                length += len(chunk)
                if length > limit:
                    return JSONResponse(status_code=413,content={'detail':'Request exceeds the allowed size'})
                chunks.append(chunk)
            request._body = b''.join(chunks)
    response = await call_next(request)
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['Referrer-Policy'] = 'no-referrer'
    response.headers['Cache-Control'] = 'no-store'
    return response


@app.exception_handler(httpx.HTTPError)
async def upstream_error(request, error):
    return JSONResponse(status_code=503,content={'detail':'Private storage or an external provider is unavailable. Please retry.'})


@app.exception_handler(FileNotFoundError)
async def missing_storage(request, error):
    return JSONResponse(status_code=404,content={'detail':'Stored file is unavailable. Upload or generate it again.'})


@app.get('/health')
def health():
    return {'status':'ok','service':'taxready-ai'}


app.include_router(router)


app.include_router(workspace_router)
