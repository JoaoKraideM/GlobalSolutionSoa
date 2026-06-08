from __future__ import annotations

from flask import Blueprint, current_app, jsonify, request

from app.api.deps import obter_ip_origem, obter_user_agent
from app.services.auth_service import AuthError, autenticar_usuario

bp = Blueprint("api_auth", __name__, url_prefix="/api/v1/auth")


@bp.post("/token")
def obter_token():
    """Autentica um usuário e retorna um Bearer Token para uso na API.
    ---
    tags:
      - Auth
    summary: Obter token JWT
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - email
            - senha
          properties:
            email:
              type: string
              example: admin@mineracao.local
            senha:
              type: string
              example: Admin@123456
    responses:
      200:
        description: Token gerado com sucesso
        schema:
          type: object
          properties:
            status:
              type: string
              example: success
            data:
              type: object
              properties:
                token:
                  type: string
                  description: JWT para usar no header Authorization (Bearer token)
                email:
                  type: string
                role:
                  type: string
                  example: ADMIN
      400:
        description: Body JSON ausente ou malformado
      401:
        description: Credenciais inválidas ou IP bloqueado
    """
    payload = request.get_json(silent=True)
    if not payload:
        return jsonify({"status": "error", "message": "Body JSON obrigatorio.", "code": 400}), 400

    try:
        resultado = autenticar_usuario(
            email=payload.get("email", ""),
            senha=payload.get("senha", ""),
            ip_origem=obter_ip_origem(),
            user_agent=obter_user_agent(),
            config=current_app.config,
        )
    except AuthError as exc:
        return jsonify({"status": "error", "message": str(exc), "code": 401}), 401

    return jsonify({
        "status": "success",
        "data": {
            "token": resultado.token,
            "email": resultado.usuario.email,
            "role": resultado.role,
        },
    }), 200
