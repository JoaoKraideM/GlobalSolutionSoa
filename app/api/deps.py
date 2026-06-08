from __future__ import annotations

from functools import wraps
from typing import Callable

import jwt
from flask import current_app, flash, g, jsonify, redirect, request, session, url_for

from app.core.middleware import csrf_valido
from app.core.security import decodificar_jwt
from app.models.modelos import User


def obter_ip_origem() -> str:
    encaminhado = request.headers.get("X-Forwarded-For", "").split(",")[0].strip()
    return encaminhado or request.remote_addr or "0.0.0.0"


def obter_user_agent() -> str:
    return (request.headers.get("User-Agent") or "desconhecido")[:300]


def carregar_usuario_logado() -> tuple[User | None, str | None]:
    token = session.get("access_token")
    if not token:
        g.current_user = None
        g.current_role = None
        return None, None

    try:
        claims = decodificar_jwt(current_app.config, token)
    except (jwt.InvalidTokenError, KeyError):
        session.pop("access_token", None)
        g.current_user = None
        g.current_role = None
        return None, None

    usuario = User.query.get(claims.get("sub"))
    if not usuario or not usuario.ativo:
        session.pop("access_token", None)
        g.current_user = None
        g.current_role = None
        return None, None

    role = claims.get("role", "ANALISTA")
    g.current_user = usuario
    g.current_role = role
    return usuario, role


def login_required(view: Callable):
    @wraps(view)
    def wrapped(*args, **kwargs):
        usuario, _ = carregar_usuario_logado()
        if not usuario:
            flash("Voce precisa se autenticar para continuar.", "warning")
            return redirect(url_for("auth.login"))
        return view(*args, **kwargs)

    return wrapped


def role_required(*roles_aceitas: str):
    roles_normalizadas = {role.upper() for role in roles_aceitas}

    def decorator(view: Callable):
        @wraps(view)
        def wrapped(*args, **kwargs):
            usuario, role = carregar_usuario_logado()
            if not usuario:
                flash("Sessao expirada. Faca login novamente.", "warning")
                return redirect(url_for("auth.login"))
            if (role or "").upper() not in roles_normalizadas:
                flash("Acesso negado para este recurso.", "danger")
                return redirect(url_for("main.dashboard"))
            return view(*args, **kwargs)

        return wrapped

    return decorator


def validar_csrf_ou_erro() -> bool:
    token_form = request.form.get("csrf_token")
    if csrf_valido(token_form):
        return True
    flash("Falha de seguranca no formulario. Tente novamente.", "danger")
    return False


def api_token_required(view: Callable):
    """Decorator para endpoints da API REST v1.

    Autentica via Bearer Token no header Authorization — diferente do
    login_required (que usa sessão de cookie), este decorator é stateless:
    cada requisição traz suas próprias credenciais, sem depender de sessão
    no servidor.  Isso é essencial para APIs consumidas por scripts,
    dispositivos IoT, ou ferramentas externas como o Swagger UI.

    Uso:  Authorization: Bearer <token_obtido_em_POST_/api/v1/auth/token>
    """
    @wraps(view)
    def wrapped(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return jsonify({
                "status": "error",
                "message": "Token nao fornecido. Header esperado: Authorization: Bearer <token>",
                "code": 401,
            }), 401

        token = auth_header[7:]
        try:
            claims = decodificar_jwt(current_app.config, token)
        except jwt.InvalidTokenError:
            return jsonify({
                "status": "error",
                "message": "Token invalido ou expirado.",
                "code": 401,
            }), 401

        usuario = User.query.get(claims.get("sub"))
        if not usuario or not usuario.ativo:
            return jsonify({
                "status": "error",
                "message": "Usuario inativo ou nao encontrado.",
                "code": 401,
            }), 401

        # Armazena no contexto da requisição para os endpoints usarem
        g.api_user = usuario
        g.api_role = claims.get("role", "ANALISTA")
        return view(*args, **kwargs)

    return wrapped
