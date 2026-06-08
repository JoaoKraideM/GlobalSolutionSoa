from __future__ import annotations

from app.db.session import db
from app.models.modelos import RecomendacaoIA


class RecomendacaoRepository:
    """Camada de acesso a dados exclusiva para RecomendacaoIA."""

    def listar(self, limite: int = 100, offset: int = 0) -> list[RecomendacaoIA]:
        return (
            RecomendacaoIA.query
            .order_by(RecomendacaoIA.criado_em_data.desc(),
                      RecomendacaoIA.criado_em_hora.desc())
            .offset(offset)
            .limit(limite)
            .all()
        )

    def contar(self) -> int:
        return RecomendacaoIA.query.count()

    def buscar_por_id(self, recomendacao_id: int) -> RecomendacaoIA | None:
        return RecomendacaoIA.query.get(recomendacao_id)

    def listar_por_analise(self, analise_id: int) -> list[RecomendacaoIA]:
        return (
            RecomendacaoIA.query
            .filter_by(analise_id=analise_id)
            .order_by(RecomendacaoIA.criado_em_data.desc(),
                      RecomendacaoIA.criado_em_hora.desc())
            .all()
        )

    def salvar(self, recomendacao: RecomendacaoIA) -> RecomendacaoIA:
        db.session.add(recomendacao)
        db.session.commit()
        db.session.refresh(recomendacao)
        return recomendacao

    def deletar(self, recomendacao: RecomendacaoIA) -> None:
        db.session.delete(recomendacao)
        db.session.commit()
