from __future__ import annotations

import hashlib


def mascarar_email(email: str) -> str:
    valor = (email or "").strip()
    if "@" not in valor:
        return "***"
    usuario, dominio = valor.split("@", 1)
    if len(usuario) <= 2:
        usuario_mask = usuario[0] + "*"
    else:
        usuario_mask = usuario[:2] + "*" * max(len(usuario) - 2, 1)
    return f"{usuario_mask}@{dominio}"


def hash_sha256(texto: str) -> str:
    return hashlib.sha256((texto or "").encode("utf-8")).hexdigest()
