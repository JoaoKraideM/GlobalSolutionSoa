from __future__ import annotations

import secrets
from datetime import datetime, timedelta, timezone
from typing import Any

import jwt
from passlib.hash import bcrypt


JWT_ALGORITHM = "HS256"


def hash_senha(senha: str) -> str:
    return bcrypt.hash(senha)


def verificar_senha(senha: str, senha_hash: str) -> bool:
    try:
        return bcrypt.verify(senha, senha_hash)
    except ValueError:
        return False


def criar_jwt(config: dict[str, Any], usuario_id: str, email: str, role: str) -> str:
    agora = datetime.now(timezone.utc)
    expira_em = agora + timedelta(minutes=int(config["JWT_EXP_MINUTES"]))
    payload = {
        "sub": usuario_id,
        "email": email,
        "role": role,
        "jti": secrets.token_hex(16),
        "iat": int(agora.timestamp()),
        "exp": int(expira_em.timestamp()),
    }
    return jwt.encode(payload, config["JWT_SECRET_KEY"], algorithm=JWT_ALGORITHM)


def decodificar_jwt(config: dict[str, Any], token: str) -> dict[str, Any]:
    return jwt.decode(token, config["JWT_SECRET_KEY"], algorithms=[JWT_ALGORITHM])


def token_aleatorio() -> str:
    return secrets.token_urlsafe(32)
