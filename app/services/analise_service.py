from __future__ import annotations

from app.models.modelos import AnaliseViabilidade
from app.repositories.analise_repository import AnaliseRepository
from app.repositories.asteroide_repository import AsteroideRepository
from app.schemas.dtos import AnaliseRequestDTO, AnaliseResponseDTO


class AnaliseService:
    """Serviço de negócio para AnaliseViabilidade.

    Toda operação que cria ou atualiza uma análise verifica primeiro se
    o asteroide referenciado existe — essa é uma regra de negócio, não
    uma constraint de banco de dados, e por isso vive aqui no serviço.
    """

    def __init__(
        self,
        repo: AnaliseRepository | None = None,
        repo_asteroide: AsteroideRepository | None = None,
    ) -> None:
        self.repo = repo or AnaliseRepository()
        # Dependência cruzada controlada: o serviço de análise precisa
        # consultar asteroides, mas nunca os modifica — apenas lê.
        self.repo_asteroide = repo_asteroide or AsteroideRepository()

    # ── Helpers privados ──────────────────────────────────────────────────────

    def _calcular_roi(self, dto: AnaliseRequestDTO) -> float:
        """Calcula o ROI automaticamente quando o cliente não fornece o valor.

        ROI = (receita - custo_total) / custo_total * 100
        Retorna 0.0 quando o custo total é zero para evitar divisão por zero.
        """
        custo_total = (
            dto.custo_extracao_usd
            + dto.custo_transporte_usd
            + dto.custo_processamento_usd
        )
        if custo_total == 0:
            return 0.0
        return round(((dto.receita_estimada_usd - custo_total) / custo_total) * 100, 2)

    def _verificar_asteroide(self, asteroide_id: int) -> None:
        """Lança LookupError se o asteroide referenciado não existir."""
        if self.repo_asteroide.buscar_por_id(asteroide_id) is None:
            raise LookupError(f"Asteroide id={asteroide_id} não encontrado.")

    # ── Consultas ─────────────────────────────────────────────────────────────

    def listar(self, limite: int = 100, offset: int = 0) -> dict:
        modelos = self.repo.listar(limite=limite, offset=offset)
        return {
            "data": [AnaliseResponseDTO.from_model(m).to_dict() for m in modelos],
            "total": self.repo.contar(),
            "pagina": {"limite": limite, "offset": offset},
        }

    def buscar(self, analise_id: int) -> AnaliseResponseDTO:
        modelo = self.repo.buscar_por_id(analise_id)
        if modelo is None:
            raise LookupError(f"Analise id={analise_id} não encontrada.")
        return AnaliseResponseDTO.from_model(modelo)

    # ── Mutações ──────────────────────────────────────────────────────────────

    def criar(self, dto: AnaliseRequestDTO, usuario_id: str | None = None) -> AnaliseResponseDTO:
        erros = dto.validar()
        if erros:
            raise ValueError(" | ".join(erros))

        self._verificar_asteroide(dto.asteroide_id)

        roi = dto.roi_percentual if dto.roi_percentual is not None else self._calcular_roi(dto)

        nova = AnaliseViabilidade(
            asteroide_id=dto.asteroide_id,
            versao_modelo=dto.versao_modelo,
            custo_extracao_usd=dto.custo_extracao_usd,
            custo_transporte_usd=dto.custo_transporte_usd,
            custo_processamento_usd=dto.custo_processamento_usd,
            receita_estimada_usd=dto.receita_estimada_usd,
            roi_percentual=roi,
            score_viabilidade=dto.score_viabilidade,
            classificacao=dto.classificacao,
            gerado_por_usuario_id=usuario_id,
        )
        return AnaliseResponseDTO.from_model(self.repo.salvar(nova))

    def atualizar(
        self,
        analise_id: int,
        dto: AnaliseRequestDTO,
        usuario_id: str | None = None,
    ) -> AnaliseResponseDTO:
        erros = dto.validar()
        if erros:
            raise ValueError(" | ".join(erros))

        modelo = self.repo.buscar_por_id(analise_id)
        if modelo is None:
            raise LookupError(f"Analise id={analise_id} não encontrada.")

        self._verificar_asteroide(dto.asteroide_id)

        roi = dto.roi_percentual if dto.roi_percentual is not None else self._calcular_roi(dto)

        modelo.asteroide_id = dto.asteroide_id
        modelo.versao_modelo = dto.versao_modelo
        modelo.custo_extracao_usd = dto.custo_extracao_usd
        modelo.custo_transporte_usd = dto.custo_transporte_usd
        modelo.custo_processamento_usd = dto.custo_processamento_usd
        modelo.receita_estimada_usd = dto.receita_estimada_usd
        modelo.roi_percentual = roi
        modelo.score_viabilidade = dto.score_viabilidade
        modelo.classificacao = dto.classificacao
        modelo.gerado_por_usuario_id = usuario_id

        return AnaliseResponseDTO.from_model(self.repo.salvar(modelo))

    def remover(self, analise_id: int) -> None:
        modelo = self.repo.buscar_por_id(analise_id)
        if modelo is None:
            raise LookupError(f"Analise id={analise_id} não encontrada.")
        self.repo.deletar(modelo)
