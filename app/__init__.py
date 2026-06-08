from __future__ import annotations

from flask import Flask, g, jsonify, redirect, request, session, url_for
from flasgger import Swagger

from app.api.deps import carregar_usuario_logado
from app.core.config import Config
from app.core.middleware import registrar_middlewares
from app.db.init_db import inicializar_banco
from app.db.session import db


# ─────────────────────────────────────────────────────────────────────────────
# Configuração do Swagger / OpenAPI
# ─────────────────────────────────────────────────────────────────────────────

_SWAGGER_TEMPLATE = {
    "swagger": "2.0",
    "info": {
        "title": "Mineração Espacial API",
        "description": (
            "API REST para análise de viabilidade de mineração espacial.<br><br>"
            "<b>Como autenticar:</b><br>"
            "1. Use <code>POST /api/v1/auth/token</code> com seu email e senha.<br>"
            "2. Copie o token retornado.<br>"
            "3. Clique em <b>Authorize</b> acima e insira: <code>Bearer {seu_token}</code>."
        ),
        "version": "1.0.0",
        "contact": {"name": "FIAP Global Solution 2026 — ODS 9"},
    },
    "securityDefinitions": {
        "Bearer": {
            "type": "apiKey",
            "name": "Authorization",
            "in": "header",
            "description": "JWT no formato: Bearer &lt;token&gt;",
        }
    },
    "consumes": ["application/json"],
    "produces": ["application/json"],
}

_SWAGGER_CONFIG = {
    "headers": [],
    "specs": [
        {
            "endpoint": "apispec_v1",
            "route": "/api/v1/spec.json",
            # Filtra apenas as rotas da API REST — a interface web não aparece no Swagger
            "rule_filter": lambda rule: "/api/v1/" in rule.rule,
            "model_filter": lambda tag: True,
        }
    ],
    "static_url_path": "/flasgger_static",
    "swagger_ui": True,
    "specs_route": "/api/v1/docs",
}


# ─────────────────────────────────────────────────────────────────────────────
# Application factory
# ─────────────────────────────────────────────────────────────────────────────

def create_app() -> Flask:
    app = Flask(__name__, template_folder="templates", static_folder="static")
    app.config.from_object(Config)

    db.init_app(app)
    registrar_middlewares(app)
    Swagger(app, config=_SWAGGER_CONFIG, template=_SWAGGER_TEMPLATE)

    # ── Blueprints da interface web (existentes) ──────────────────────────────
    from app.api.admin import bp as admin_bp
    from app.api.auth import bp as auth_bp
    from app.api.main import bp as main_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(admin_bp)

    # ── Blueprints da API REST v1 (novos) ─────────────────────────────────────
    from app.api.v1.auth_token import bp as api_auth_bp
    from app.api.v1.asteroides import bp as api_asteroides_bp
    from app.api.v1.analises import bp as api_analises_bp
    from app.api.v1.recomendacoes import bp as api_recomendacoes_bp

    app.register_blueprint(api_auth_bp)
    app.register_blueprint(api_asteroides_bp)
    app.register_blueprint(api_analises_bp)
    app.register_blueprint(api_recomendacoes_bp)

    @app.before_request
    def carregar_contexto_usuario() -> None:
        carregar_usuario_logado()

    @app.context_processor
    def variaveis_globais():
        return {
            "current_user": getattr(g, "current_user", None),
            "current_role": getattr(g, "current_role", None),
            "csrf_token": session.get("csrf_token", ""),
            "app_name": app.config["APP_NAME"],
        }

    # ── Tratamento centralizado de erros ─────────────────────────────────────
    # Rotas /api/* retornam JSON padronizado.
    # Rotas web retornam redirecionamentos (comportamento original mantido).

    @app.errorhandler(400)
    def bad_request(e):
        if request.path.startswith("/api/"):
            return jsonify({"status": "error", "message": "Requisicao invalida.", "code": 400}), 400
        return redirect(url_for("main.dashboard"))

    @app.errorhandler(401)
    def unauthorized(e):
        if request.path.startswith("/api/"):
            return jsonify({"status": "error", "message": "Nao autorizado.", "code": 401}), 401
        return redirect(url_for("auth.login"))

    @app.errorhandler(404)
    def not_found(e):
        if request.path.startswith("/api/"):
            return jsonify({"status": "error", "message": "Recurso nao encontrado.", "code": 404}), 404
        return redirect(url_for("auth.login"))

    @app.errorhandler(405)
    def method_not_allowed(e):
        if request.path.startswith("/api/"):
            return jsonify({"status": "error", "message": "Metodo HTTP nao permitido.", "code": 405}), 405
        return redirect(url_for("main.dashboard"))

    @app.errorhandler(500)
    def internal_error(e):
        # Rollback previne que sessoes SQLAlchemy sujas contaminem requests futuros
        db.session.rollback()
        if request.path.startswith("/api/"):
            return jsonify({"status": "error", "message": "Erro interno do servidor.", "code": 500}), 500
        return redirect(url_for("main.dashboard"))

    with app.app_context():
        inicializar_banco(app.config)

    return app
