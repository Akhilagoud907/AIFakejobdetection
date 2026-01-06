import os
from typing import Optional, Dict

from fastapi import HTTPException, status

try:
    import firebase_admin
    from firebase_admin import auth, credentials
except Exception:  # pragma: no cover - optional dependency
    firebase_admin = None
    auth = None
    credentials = None


def _init_app() -> bool:
    """Initialize Firebase Admin if credentials are present."""
    if firebase_admin is None or credentials is None:
        return False
    if firebase_admin._apps:  # already initialized
        return True

    cred_path = os.getenv("FIREBASE_CREDENTIALS")
    project_id = os.getenv("FIREBASE_PROJECT_ID")
    if not cred_path or not os.path.exists(cred_path):
        return False
    try:
        cred = credentials.Certificate(cred_path)
        firebase_admin.initialize_app(cred, {"projectId": project_id} if project_id else None)
        return True
    except Exception:
        return False


def verify_id_token(id_token: str) -> Dict:
    """Verify an ID token and return decoded claims."""
    if not id_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing token")
    if not _init_app() or auth is None:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Firebase not configured")
    try:
        decoded = auth.verify_id_token(id_token, check_revoked=True)
        return decoded
    except auth.ExpiredIdTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired")
    except auth.RevokedIdTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token revoked")
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")


def require_admin_claim(claims: Dict) -> Dict:
    is_admin = bool(claims.get("admin") or claims.get("role") == "admin")
    if not is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin privileges required")
    return claims


def configured() -> bool:
    """Return whether Firebase Admin is ready."""
    return _init_app()
