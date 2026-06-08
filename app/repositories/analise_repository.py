from __future__ import annotations

from app.db.session import db
from app.models.modelos import AnaliseViabilidade


class AnaliseRepository:
    """Camada de acesso a dados exclusiva para AnaliseViabilidade."""

    def listar(self, limite: int = 100, offset: int = 0) -> list[AnaliseViabilidade]:
        # Ordena por data descrescente e, dentro do mesmo dia, por hora decrescente.
        # Esse padrão de ordenação dupla é necessário sempre que data e hora
        # estão em colunas separadas — garante o mesmo resultado que ORDER BY datetime DESC.
        return (
            AnaliseViabilidade.query
            .order_by(AnaliseViabilidade.gerado_em_data.desc(),
                      AnaliseViabilidade.gerado_em_hora.desc())
            .offset(offset)
            .limit(limite)
            .all()
        )

    def contar(self) -> int:
        return AnaliseViabilidade.query.count()

    def buscar_por_id(self, analise_id: int) -> AnaliseViabilidade | None:
        return AnaliseViabilidade.query.get(analise_id)

    def listar_por_asteroide(self, asteroide_id: int) -> list[AnaliseViabilidade]:
        return (
            AnaliseViabilidade.query
            .filter_by(asteroide_id=asteroide_id)
            .order_by(AnaliseViabilidade.gerado_em_data.desc(),
                      AnaliseViabilidade.gerado_em_hora.desc())
            .all()
        )

    def salvar(self, analise: AnaliseViabilidade) -> AnaliseViabilidade:
        db.session.add(analise)
        db.session.commit()
        db.session.refresh(analise)
        return analise

    def deletar(self, analise: AnaliseViabilidade) -> None:
        db.session.delete(analise)
        db.session.commit()
