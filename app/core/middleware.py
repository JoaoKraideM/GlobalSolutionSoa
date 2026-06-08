from __future__ import annotations

import secrets
import uuid

from flask import Flask, g, request, session


def csrf_valido(token_formulario: str | None) -> bool:
    token_sessao = session.get("csrf_token")
    if not token_sessao or not token_formulario:
        return False
    return secrets.compare_digest(token_sessao, token_formulario)


def registrar_middlewares(app: Flask) -> None:
    @app.before_request
    def preparar_request() -> None:
        g.correlation_id = str(uuid.uuid4())
        if "csrf_token" not in session:
            session["csrf_token"] = secrets.token_urlsafe(24)

    @app.after_request
    def headers_seguranca(response):
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "SAMEORIGIN"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"

        # As rotas do Swagger UI (/api/v1/docs e /flasgger_static) precisam de
        # 'unsafe-inline' em script-src porque o Flasgger inicializa o
        # SwaggerUIBundle() via <script> inline no seu template.
        # Sem isso, o CSP bloqueia o script e o Swagger fica em loading infinito.
        # Para todas as outras rotas da aplicacao, mantemos o CSP restritivo.
        if request.path.startswith("/api/v1/docs") or request.path.startswith("/flasgger_static"):
            csp = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline'; "
                "style-src 'self' 'unsafe-inline'; "
                "img-src 'self' data:; "
                "font-src 'self'; "
                "connect-src 'self'; "
                "frame-ancestors 'self';"
            )
        else:
            csp = (
                "default-src 'self'; "
                "script-src 'self'; "
                "style-src 'self' 'unsafe-inline'; "
                "img-src 'self' data:; "
                "font-src 'self'; "
                "connect-src 'self'; "
                "form-action 'self'; "
                "frame-ancestors 'self';"
            )

        response.headers["Content-Security-Policy"] = csp
        if request.is_secure:
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        return response
