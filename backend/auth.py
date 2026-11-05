import hashlib
import secrets

from fastapi import Depends, Header, HTTPException
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import SessionToken, User


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 120_000)
    return f"{salt}${digest.hex()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        salt, hashed = stored.split("$", 1)
    except ValueError:
        return False
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 120_000)
    return hashed == digest.hex()


def create_session(db: Session, user: User) -> str:
    token = secrets.token_hex(32)
    db.add(SessionToken(token=token, user_id=user.id))
    db.commit()
    return token


def get_current_user(
    authorization: str = Header(None),
    db: Session = Depends(get_db),
) -> User:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Sesión requerida")
    token = authorization.split(" ", 1)[1]
    session = db.query(SessionToken).filter(SessionToken.token == token).first()
    if not session:
        raise HTTPException(status_code=401, detail="Sesión inválida")
    user = db.query(User).filter(User.id == session.user_id).first()
    if not user:
        raise HTTPException(status_code=401, detail="Usuario no encontrado")
    return user


def require_admin(user: User = Depends(get_current_user)) -> User:
    if user.rol != "admin":
        raise HTTPException(status_code=403, detail="Solo administradores")
    return user
