from __future__ import annotations

from sqlalchemy.exc import IntegrityError

from app.models.modelos import Asteroide
from app.repositories.asteroide_repository import AsteroideRepository
from app.schemas.dtos import AsteroideRequestDTO, AsteroideResponseDTO


class AsteroideService:
    """Serviço de negócio para a entidade Asteroide.

    Esta camada orquestra regras de negócio sem conhecer HTTP ou SQLAlchemy.
    Ela recebe DTOs (objetos puros de dados) e delega a persistência ao
    AsteroideRepository — esse é o núcleo da separação de responsabilidades
    exigida pela arquitetura em camadas: Controller → Service → Repository → Model.

    Para injetar um repositório de teste, basta passar `repo=MockRepository()`
    no construtor — o serviço funciona sem mudanças.
    """

    def __init__(self, repo: AsteroideRepository | None = None) -> None:
        # Injeção de dependência via construtor: padrão IoC simples e eficaz.
        self.repo = repo or AsteroideRepository()

    # ── Consultas ─────────────────────────────────────────────────────────────

    def listar(self, limite: int = 100, offset: int = 0) -> dict:
        modelos = self.repo.listar(limite=limite, offset=offset)
        return {
            "data": [AsteroideResponseDTO.from_model(m).to_dict() for m in modelos],
            "total": self.repo.contar(),
            "pagina": {"limite": limite, "offset": offset},
        }

    def buscar(self, asteroide_id: int) -> AsteroideResponseDTO:
        modelo = self.repo.buscar_por_id(asteroide_id)
        if modelo is None:
            raise LookupError(f"Asteroide id={asteroide_id} não encontrado.")
        return AsteroideResponseDTO.from_model(modelo)

    # ── Mutações ──────────────────────────────────────────────────────────────

    def criar(self, dto: AsteroideRequestDTO) -> AsteroideResponseDTO:
        erros = dto.validar()
        if erros:
            raise ValueError(" | ".join(erros))

        if self.repo.buscar_por_codigo(dto.codigo):
            raise ValueError(f"Já existe um asteroide com o código '{dto.codigo}'.")

        novo = Asteroide(
            codigo=dto.codigo,
            nome=dto.nome,
            classe_espectral=dto.classe_espectral,
            diametro_km=dto.diametro_km,
            delta_v_kms=dto.delta_v_kms,
            mineral_destaque=dto.mineral_destaque,
            valor_estimado_usd=dto.valor_estimado_usd,
            score_viabilidade=dto.score_viabilidade,
        )
        try:
            salvo = self.repo.salvar(novo)
        except IntegrityError as exc:
            raise ValueError("Código de asteroide já cadastrado (conflito de integridade).") from exc
        return AsteroideResponseDTO.from_model(salvo)

    def atualizar(self, asteroide_id: int, dto: AsteroideRequestDTO) -> AsteroideResponseDTO:
        erros = dto.validar()
        if erros:
            raise ValueError(" | ".join(erros))

        modelo = self.repo.buscar_por_id(asteroide_id)
        if modelo is None:
            raise LookupError(f"Asteroide id={asteroide_id} não encontrado.")

        # Garante que o novo código não conflita com outro asteroide existente
        existente = self.repo.buscar_por_codigo(dto.codigo)
        if existente and existente.asteroide_id != asteroide_id:
            raise ValueError(f"O código '{dto.codigo}' já pertence a outro asteroide.")

        modelo.codigo = dto.codigo
        modelo.nome = dto.nome
        modelo.classe_espectral = dto.classe_espectral
        modelo.diametro_km = dto.diametro_km
        modelo.delta_v_kms = dto.delta_v_kms
        modelo.mineral_destaque = dto.mineral_destaque
        modelo.valor_estimado_usd = dto.valor_estimado_usd
        modelo.score_viabilidade = dto.score_viabilidade

        return AsteroideResponseDTO.from_model(self.repo.salvar(modelo))

    def remover(self, asteroide_id: int) -> None:
        modelo = self.repo.buscar_por_id(asteroide_id)
        if modelo is None:
            raise LookupError(f"Asteroide id={asteroide_id} não encontrado.")
        self.repo.deletar(modelo)
