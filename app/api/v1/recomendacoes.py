from __future__ import annotations

from flask import Blueprint, jsonify, request

from app.api.deps import api_token_required
from app.repositories.recomendacao_repository import RecomendacaoRepository
from app.schemas.dtos import RecomendacaoResponseDTO

bp = Blueprint("api_recomendacoes", __name__, url_prefix="/api/v1/recomendacoes")

_repo = RecomendacaoRepository()


@bp.get("/")
@api_token_required
def listar():
    """Lista todas as recomendacoes de IA (paginado).
    ---
    tags:
      - Recomendacoes IA
    security:
      - Bearer: []
    parameters:
      - name: limite
        in: query
        type: integer
        default: 100
      - name: offset
        in: query
        type: integer
        default: 0
    responses:
      200:
        description: Lista de recomendacoes
        schema:
          type: object
          properties:
            status:
              type: string
              example: success
            data:
              type: array
              items:
                $ref: '#/definitions/RecomendacaoResponse'
            total:
              type: integer
            pagina:
              type: object
      401:
        description: Token ausente ou invalido
    definitions:
      RecomendacaoResponse:
        type: object
        properties:
          recomendacao_id:
            type: integer
          analise_id:
            type: integer
          modelo_ia:
            type: string
          resumo_recomendacao:
            type: string
          plano_acao:
            type: string
          confianca:
            type: number
          criado_em:
            type: string
            format: date-time
    """
    limite = min(int(request.args.get("limite", 100)), 500)
    offset = max(int(request.args.get("offset", 0)), 0)
    modelos = _repo.listar(limite=limite, offset=offset)
    total = _repo.contar()
    return jsonify({
        "status": "success",
        "data": [RecomendacaoResponseDTO.from_model(m).to_dict() for m in modelos],
        "total": total,
        "pagina": {"limite": limite, "offset": offset},
    }), 200


@bp.get("/<int:recomendacao_id>")
@api_token_required
def buscar(recomendacao_id: int):
    """Retorna uma recomendacao de IA pelo ID.
    ---
    tags:
      - Recomendacoes IA
    security:
      - Bearer: []
    parameters:
      - name: recomendacao_id
        in: path
        type: integer
        required: true
    responses:
      200:
        description: Recomendacao encontrada
        schema:
          type: object
          properties:
            status:
              type: string
            data:
              $ref: '#/definitions/RecomendacaoResponse'
      401:
        description: Token ausente ou invalido
      404:
        description: Recomendacao nao encontrada
    """
    modelo = _repo.buscar_por_id(recomendacao_id)
    if modelo is None:
        return jsonify({
            "status": "error",
            "message": f"Recomendacao id={recomendacao_id} nao encontrada.",
            "code": 404,
        }), 404
    return jsonify({
        "status": "success",
        "data": RecomendacaoResponseDTO.from_model(modelo).to_dict(),
    }), 200
