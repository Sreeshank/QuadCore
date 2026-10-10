from app.models import AuditEvent

def record(db, user_id, action, resource_id=None, details=None):
    """Store action metadata, never financial amounts, identifiers, tokens or document text."""
    db.add(AuditEvent(user_id=user_id, action=action, resource_id=resource_id, details_json=details or {}))

