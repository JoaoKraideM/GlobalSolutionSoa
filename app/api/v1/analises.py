from __future__ import annotations

from flask import Blueprint, g, jsonify, request

from app.api.deps import api_token_required
from app.schemas.dtos import AnaliseRequestDTO
from app.services.analise_service import AnaliseService

bp = Blueprint("api_analises", __name__, url_prefix="/api/v1/analises")

_svc = AnaliseService()


@bp.get("/")
@api_token_required
def listar():
    """Lista todas as analises de viabilidade (paginado).
    ---
    tags:
      - Analises de Viabilidade
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
        description: Lista paginada de analises
        schema:
          type: object
          properties:
            status:
              type: string
              example: success
            data:
              type: array
              items:
                $ref: '#/definitions/AnaliseResponse'
            total:
              type: integer
            pagina:
              type: object
      401:
        description: Token ausente ou invalido
    """
    limite = min(int(request.args.get("limite", 100)), 500)
    offset = max(int(request.args.get("offset", 0)), 0)
    resultado = _svc.listar(limite=limite, offset=offset)
    return jsonify({"status": "success", **resultado}), 200


@bp.get("/<int:analise_id>")
@api_token_required
def buscar(analise_id: int):
    """Retorna uma analise de viabilidade pelo ID.
    ---
    tags:
      - Analises de Viabilidade
    security:
      - Bearer: []
    parameters:
      - name: analise_id
        in: path
        type: integer
        required: true
    responses:
      200:
        description: Analise encontrada
        schema:
          type: object
          properties:
            status:
              type: string
            data:
              $ref: '#/definitions/AnaliseResponse'
      401:
        description: Token ausente ou invalido
      404:
        description: Analise nao encontrada
    """
    try:
        dto = _svc.buscar(analise_id)
        return jsonify({"status": "success", "data": dto.to_dict()}), 200
    except LookupError as exc:
        return jsonify({"status": "error", "message": str(exc), "code": 404}), 404


@bp.post("/")
@api_token_required
def criar():
    """Cria uma nova analise de viabilidade para um asteroide.
    ---
    tags:
      - Analises de Viabilidade
    security:
      - Bearer: []
    parameters:
      - in: body
        name: body
        required: true
        schema:
          $ref: '#/definitions/AnaliseRequest'
    responses:
      201:
        description: Analise criada com sucesso
      400:
        description: Dados invalidos ou asteroide nao encontrado
      401:
        description: Token ausente ou invalido
    definitions:
      AnaliseRequest:
        type: object
        required:
          - asteroide_id
          - versao_modelo
          - custo_extracao_usd
          - custo_transporte_usd
          - custo_processamento_usd
          - receita_estimada_usd
          - score_viabilidade
          - classificacao
        properties:
          asteroide_id:
            type: integer
            example: 1
          versao_modelo:
            type: string
            example: v2.5
          custo_extracao_usd:
            type: number
            example: 950000000
          custo_transporte_usd:
            type: number
            example: 320000000
          custo_processamento_usd:
            type: number
            example: 140000000
          receita_estimada_usd:
            type: number
            example: 4500000000
          roi_percentual:
            type: number
            example: 216.5
            description: Calculado automaticamente se omitido
          score_viabilidade:
            type: number
            example: 87.2
          classificacao:
            type: string
            enum: [ALTA, MEDIA, BAIXA]
            example: ALTA
      AnaliseResponse:
        type: object
        properties:
          analise_id:
            type: integer
          asteroide_id:
            type: integer
          versao_modelo:
            type: string
          custo_extracao_usd:
            type: number
          custo_transporte_usd:
            type: number
          custo_processamento_usd:
            type: number
          receita_estimada_usd:
            type: number
          roi_percentual:
            type: number
          score_viabilidade:
            type: number
          classificacao:
            type: string
          gerado_em:
            type: string
            format: date-time
          gerado_por_usuario_id:
            type: string
    """
    payload = request.get_json(silent=True)
    if not payload:
        return jsonify({"status": "error", "message": "Body JSON obrigatorio.", "code": 400}), 400
    try:
        usuario_id = g.api_user.usuario_id
        dto = _svc.criar(AnaliseRequestDTO.from_dict(payload), usuario_id=usuario_id)
        return jsonify({"status": "success", "data": dto.to_dict()}), 201
    except LookupError as exc:
        return jsonify({"status": "error", "message": str(exc), "code": 404}), 404
    except ValueError as exc:
        return jsonify({"status": "error", "message": str(exc), "code": 400}), 400


@bp.put("/<int:analise_id>")
@api_token_required
def atualizar(analise_id: int):
    """Atualiza completamente uma analise de viabilidade existente.
    ---
    tags:
      - Analises de Viabilidade
    security:
      - Bearer: []
    parameters:
      - name: analise_id
        in: path
        type: integer
        required: true
      - in: body
        name: body
        required: true
        schema:
          $ref: '#/definitions/AnaliseRequest'
    responses:
      200:
        description: Analise atualizada com sucesso
      400:
        description: Dados invalidos
      401:
        description: Token ausente ou invalido
      404:
        description: Analise ou asteroide nao encontrado
    """
    payload = request.get_json(silent=True)
    if not payload:
        return jsonify({"status": "error", "message": "Body JSON obrigatorio.", "code": 400}), 400
    try:
        usuario_id = g.api_user.usuario_id
        dto = _svc.atualizar(analise_id, AnaliseRequestDTO.from_dict(payload), usuario_id=usuario_id)
        return jsonify({"status": "success", "data": dto.to_dict()}), 200
    except LookupError as exc:
        return jsonify({"status": "error", "message": str(exc), "code": 404}), 404
    except ValueError as exc:
        return jsonify({"status": "error", "message": str(exc), "code": 400}), 400


@bp.delete("/<int:analise_id>")
@api_token_required
def remover(analise_id: int):
    """Remove uma analise de viabilidade pelo ID.
    ---
    tags:
      - Analises de Viabilidade
    security:
      - Bearer: []
    parameters:
      - name: analise_id
        in: path
        type: integer
        required: true
    responses:
      204:
        description: Removida com sucesso (sem corpo)
      401:
        description: Token ausente ou invalido
      404:
        description: Analise nao encontrada
    """
    try:
        _svc.remover(analise_id)
        return "", 204
    except LookupError as exc:
        return jsonify({"status": "error", "message": str(exc), "code": 404}), 404
