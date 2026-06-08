from __future__ import annotations

from app.db.session import db
from app.models.modelos import Asteroide


class AsteroideRepository:
    """Camada de acesso a dados exclusiva para a entidade Asteroide.

    O objetivo desta classe é isolar completamente o SQLAlchemy dos
    serviços de negócio. Os serviços chamam métodos semânticos como
    `buscar_por_codigo` ou `salvar` — sem precisar saber que existe
    um ORM por baixo. Isso também facilita a escrita de testes
    unitários: basta substituir o repositório por um mock/stub.
    """

    def listar(self, limite: int = 100, offset: int = 0) -> list[Asteroide]:
        """Retorna asteroides paginados, ordenados por score (maior primeiro)."""
        return (
            Asteroide.query
            .order_by(Asteroide.score_viabilidade.desc())
            .offset(offset)
            .limit(limite)
            .all()
        )

    def contar(self) -> int:
        """Retorna o total de asteroides — usado para metadados de paginação."""
        return Asteroide.query.count()

    def buscar_por_id(self, asteroide_id: int) -> Asteroide | None:
        return Asteroide.query.get(asteroide_id)

    def buscar_por_codigo(self, codigo: str) -> Asteroide | None:
        return Asteroide.query.filter_by(codigo=codigo.strip().upper()).first()

    def salvar(self, asteroide: Asteroide) -> Asteroide:
        """INSERT ou UPDATE + refresh: retorna o objeto com dados atualizados do banco."""
        db.session.add(asteroide)
        db.session.commit()
        db.session.refresh(asteroide)
        return asteroide

    def deletar(self, asteroide: Asteroide) -> None:
        db.session.delete(asteroide)
        db.session.commit()
