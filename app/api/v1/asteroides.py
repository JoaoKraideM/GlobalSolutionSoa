from __future__ import annotations

from flask import Blueprint, g, jsonify, request

from app.api.deps import api_token_required
from app.schemas.dtos import AsteroideRequestDTO
from app.services.asteroide_service import AsteroideService

bp = Blueprint("api_asteroides", __name__, url_prefix="/api/v1/asteroides")

# O serviço é instanciado uma vez por módulo. O repositório interno
# só faz chamadas ao banco dentro de um request context, então não há
# problema em manter a instância no nível do módulo.
_svc = AsteroideService()


@bp.get("/")
@api_token_required
def listar():
    """Lista todos os asteroides cadastrados (paginado).
    ---
    tags:
      - Asteroides
    security:
      - Bearer: []
    parameters:
      - name: limite
        in: query
        type: integer
        default: 100
        description: Maximo de registros retornados (max 500)
      - name: offset
        in: query
        type: integer
        default: 0
        description: Posicao de inicio para paginacao
    responses:
      200:
        description: Lista paginada de asteroides
        schema:
          type: object
          properties:
            status:
              type: string
              example: success
            data:
              type: array
              items:
                $ref: '#/definitions/AsteroideResponse'
            total:
              type: integer
              description: Total de registros no banco (ignorando limite/offset)
            pagina:
              type: object
              properties:
                limite:
                  type: integer
                offset:
                  type: integer
      401:
        description: Token ausente ou invalido
    """
    limite = min(int(request.args.get("limite", 100)), 500)
    offset = max(int(request.args.get("offset", 0)), 0)
    resultado = _svc.listar(limite=limite, offset=offset)
    return jsonify({"status": "success", **resultado}), 200


@bp.get("/<int:asteroide_id>")
@api_token_required
def buscar(asteroide_id: int):
    """Retorna um asteroide especifico pelo seu ID.
    ---
    tags:
      - Asteroides
    security:
      - Bearer: []
    parameters:
      - name: asteroide_id
        in: path
        type: integer
        required: true
        description: ID unico do asteroide
    responses:
      200:
        description: Asteroide encontrado
        schema:
          type: object
          properties:
            status:
              type: string
              example: success
            data:
              $ref: '#/definitions/AsteroideResponse'
      401:
        description: Token ausente ou invalido
      404:
        description: Asteroide nao encontrado
    """
    try:
        dto = _svc.buscar(asteroide_id)
        return jsonify({"status": "success", "data": dto.to_dict()}), 200
    except LookupError as exc:
        return jsonify({"status": "error", "message": str(exc), "code": 404}), 404


@bp.post("/")
@api_token_required
def criar():
    """Cadastra um novo asteroide.
    ---
    tags:
      - Asteroides
    security:
      - Bearer: []
    parameters:
      - in: body
        name: body
        required: true
        schema:
          $ref: '#/definitions/AsteroideRequest'
    responses:
      201:
        description: Asteroide criado com sucesso
        schema:
          type: object
          properties:
            status:
              type: string
              example: success
            data:
              $ref: '#/definitions/AsteroideResponse'
      400:
        description: Dados invalidos ou codigo duplicado
      401:
        description: Token ausente ou invalido
    definitions:
      AsteroideRequest:
        type: object
        required:
          - codigo
          - nome
        properties:
          codigo:
            type: string
            example: 2026-AB1
          nome:
            type: string
            example: Nebula Core
          classe_espectral:
            type: string
            example: M
          diametro_km:
            type: number
            example: 2.1
          delta_v_kms:
            type: number
            example: 5.0
          mineral_destaque:
            type: string
            example: Ferro
          valor_estimado_usd:
            type: number
            example: 800000000
          score_viabilidade:
            type: number
            example: 72.0
      AsteroideResponse:
        type: object
        properties:
          asteroide_id:
            type: integer
          codigo:
            type: string
          nome:
            type: string
          classe_espectral:
            type: string
          diametro_km:
            type: number
          delta_v_kms:
            type: number
          mineral_destaque:
            type: string
          valor_estimado_usd:
            type: number
          score_viabilidade:
            type: number
          atualizado_em:
            type: string
            format: date-time
    """
    payload = request.get_json(silent=True)
    if not payload:
        return jsonify({"status": "error", "message": "Body JSON obrigatorio.", "code": 400}), 400
    try:
        dto = _svc.criar(AsteroideRequestDTO.from_dict(payload))
        return jsonify({"status": "success", "data": dto.to_dict()}), 201
    except ValueError as exc:
        return jsonify({"status": "error", "message": str(exc), "code": 400}), 400


@bp.put("/<int:asteroide_id>")
@api_token_required
def atualizar(asteroide_id: int):
    """Atualiza completamente um asteroide existente.
    ---
    tags:
      - Asteroides
    security:
      - Bearer: []
    parameters:
      - name: asteroide_id
        in: path
        type: integer
        required: true
      - in: body
        name: body
        required: true
        schema:
          $ref: '#/definitions/AsteroideRequest'
    responses:
      200:
        description: Asteroide atualizado com sucesso
      400:
        description: Dados invalidos
      401:
        description: Token ausente ou invalido
      404:
        description: Asteroide nao encontrado
    """
    payload = request.get_json(silent=True)
    if not payload:
        return jsonify({"status": "error", "message": "Body JSON obrigatorio.", "code": 400}), 400
    try:
        dto = _svc.atualizar(asteroide_id, AsteroideRequestDTO.from_dict(payload))
        return jsonify({"status": "success", "data": dto.to_dict()}), 200
    except LookupError as exc:
        return jsonify({"status": "error", "message": str(exc), "code": 404}), 404
    except ValueError as exc:
        return jsonify({"status": "error", "message": str(exc), "code": 400}), 400


@bp.delete("/<int:asteroide_id>")
@api_token_required
def remover(asteroide_id: int):
    """Remove um asteroide pelo ID.
    ---
    tags:
      - Asteroides
    security:
      - Bearer: []
    parameters:
      - name: asteroide_id
        in: path
        type: integer
        required: true
    responses:
      204:
        description: Removido com sucesso (sem corpo de resposta)
      401:
        description: Token ausente ou invalido
      404:
        description: Asteroide nao encontrado
    """
    try:
        _svc.remover(asteroide_id)
        return "", 204
    except LookupError as exc:
        return jsonify({"status": "error", "message": str(exc), "code": 404}), 404
