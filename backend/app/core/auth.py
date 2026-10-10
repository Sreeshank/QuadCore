import hashlib
import secrets
from datetime import datetime, timedelta, timezone
import httpx
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.core.config import settings
from app.db.session import get_db
from app.models import User, DemoSession

bearer = HTTPBearer(auto_error=False)


def create_demo_session(db: Session):
    user = User(email=f'demo-{secrets.token_hex(4)}@example.invalid')
    db.add(user)
    db.flush()
    token = 'demo_' + secrets.token_urlsafe(48)
    db.add(DemoSession(token_hash=hashlib.sha256(token.encode()).hexdigest(), user_id=user.id, expires_at=datetime.now(timezone.utc) + timedelta(hours=24)))
    db.commit()
    return user, token


def current_user(auth: HTTPAuthorizationCredentials | None = Depends(bearer), db: Session = Depends(get_db)) -> User:
    if not auth:
        raise HTTPException(401, 'Sign in to continue', headers={'WWW-Authenticate': 'Bearer'})
    token = auth.credentials
    if token.startswith('demo_'):
        if not settings.demo_mode or settings.app_env == 'production':
            raise HTTPException(401, 'Demo authentication is disabled')
        session = db.get(DemoSession, hashlib.sha256(token.encode()).hexdigest())
        if not session or session.expires_at.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
            raise HTTPException(401, 'Demo session expired. Start a new demo.')
        return db.get(User, session.user_id)
    if not settings.supabase_url:
        raise HTTPException(401, 'Invalid session')
    try:
        response = httpx.get(f'{settings.supabase_url}/auth/v1/user', headers={'apikey': settings.supabase_anon_key, 'Authorization': f'Bearer {token}'}, timeout=10)
        if response.status_code != 200:
            raise HTTPException(401, 'Invalid or expired session')
        identity = response.json()
        user = db.get(User, identity['id'])
        if not user:
            user = User(id=identity['id'], email=identity.get('email', ''))
            db.add(user)
            db.commit()
        return user
    except (httpx.HTTPError, KeyError, ValueError):
        raise HTTPException(503, 'Authentication provider unavailable')

