from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Optional


# ─────────────────────────────────────────────────────────────────────────────
# Asteroide
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class AsteroideRequestDTO:
    """Contrato de entrada para criação ou atualização de asteroide via API."""
    codigo: str
    nome: str
    classe_espectral: Optional[str] = None
    diametro_km: Optional[float] = None
    delta_v_kms: Optional[float] = None
    mineral_destaque: Optional[str] = None
    valor_estimado_usd: Optional[float] = None
    score_viabilidade: float = 0.0

    @classmethod
    def from_dict(cls, data: dict) -> "AsteroideRequestDTO":
        return cls(
            codigo=(data.get("codigo") or "").strip().upper(),
            nome=(data.get("nome") or "").strip(),
            classe_espectral=data.get("classe_espectral"),
            diametro_km=_float_or_none(data.get("diametro_km")),
            delta_v_kms=_float_or_none(data.get("delta_v_kms")),
            mineral_destaque=data.get("mineral_destaque"),
            valor_estimado_usd=_float_or_none(data.get("valor_estimado_usd")),
            score_viabilidade=float(data.get("score_viabilidade") or 0.0),
        )

    def validar(self) -> list[str]:
        erros: list[str] = []
        if not self.codigo:
            erros.append("Campo 'codigo' e obrigatorio.")
        if not self.nome:
            erros.append("Campo 'nome' e obrigatorio.")
        if not (0.0 <= self.score_viabilidade <= 100.0):
            erros.append("'score_viabilidade' deve estar entre 0 e 100.")
        if self.diametro_km is not None and self.diametro_km < 0:
            erros.append("'diametro_km' nao pode ser negativo.")
        if self.delta_v_kms is not None and self.delta_v_kms < 0:
            erros.append("'delta_v_kms' nao pode ser negativo.")
        return erros


@dataclass
class AsteroideResponseDTO:
    """Contrato de saída para asteroide.
    
    Os campos de timestamp foram divididos em _data e _hora para
    facilitar filtragem por intervalo no cliente.  Exemplo de uso:
      "atualizado_em_data": "2025-06-03"
      "atualizado_em_hora": "14:32:07"
    """
    asteroide_id: int
    codigo: str
    nome: str
    classe_espectral: Optional[str]
    diametro_km: Optional[float]
    delta_v_kms: Optional[float]
    mineral_destaque: Optional[str]
    valor_estimado_usd: Optional[float]
    score_viabilidade: float
    atualizado_em_data: Optional[str]
    atualizado_em_hora: Optional[str]

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_model(cls, model) -> "AsteroideResponseDTO":
        return cls(
            asteroide_id=model.asteroide_id,
            codigo=model.codigo,
            nome=model.nome,
            classe_espectral=model.classe_espectral,
            diametro_km=model.diametro_km,
            delta_v_kms=model.delta_v_kms,
            mineral_destaque=model.mineral_destaque,
            valor_estimado_usd=model.valor_estimado_usd,
            score_viabilidade=model.score_viabilidade,
            atualizado_em_data=model.atualizado_em_data.isoformat() if model.atualizado_em_data else None,
            atualizado_em_hora=str(model.atualizado_em_hora) if model.atualizado_em_hora else None,
        )


# ─────────────────────────────────────────────────────────────────────────────
# Analise de Viabilidade
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class AnaliseRequestDTO:
    """Contrato de entrada para criação ou atualização de análise de viabilidade."""
    asteroide_id: int
    versao_modelo: str
    custo_extracao_usd: float
    custo_transporte_usd: float
    custo_processamento_usd: float
    receita_estimada_usd: float
    score_viabilidade: float
    classificacao: str
    roi_percentual: Optional[float] = None

    @classmethod
    def from_dict(cls, data: dict) -> "AnaliseRequestDTO":
        return cls(
            asteroide_id=int(data.get("asteroide_id") or 0),
            versao_modelo=(data.get("versao_modelo") or "").strip(),
            custo_extracao_usd=float(data.get("custo_extracao_usd") or 0),
            custo_transporte_usd=float(data.get("custo_transporte_usd") or 0),
            custo_processamento_usd=float(data.get("custo_processamento_usd") or 0),
            receita_estimada_usd=float(data.get("receita_estimada_usd") or 0),
            score_viabilidade=float(data.get("score_viabilidade") or 0),
            classificacao=(data.get("classificacao") or "").strip().upper(),
            roi_percentual=_float_or_none(data.get("roi_percentual")),
        )

    def validar(self) -> list[str]:
        erros: list[str] = []
        if not self.asteroide_id:
            erros.append("Campo 'asteroide_id' e obrigatorio.")
        if not self.versao_modelo:
            erros.append("Campo 'versao_modelo' e obrigatorio.")
        if self.classificacao not in {"ALTA", "MEDIA", "BAIXA"}:
            erros.append("'classificacao' deve ser ALTA, MEDIA ou BAIXA.")
        for campo in ("custo_extracao_usd", "custo_transporte_usd",
                      "custo_processamento_usd", "receita_estimada_usd"):
            if getattr(self, campo) < 0:
                erros.append(f"'{campo}' nao pode ser negativo.")
        if not (0.0 <= self.score_viabilidade <= 100.0):
            erros.append("'score_viabilidade' deve estar entre 0 e 100.")
        return erros


@dataclass
class AnaliseResponseDTO:
    """Contrato de saída para análise de viabilidade."""
    analise_id: int
    asteroide_id: int
    versao_modelo: str
    custo_extracao_usd: float
    custo_transporte_usd: float
    custo_processamento_usd: float
    receita_estimada_usd: float
    roi_percentual: Optional[float]
    score_viabilidade: float
    classificacao: str
    gerado_em_data: Optional[str]
    gerado_em_hora: Optional[str]
    gerado_por_usuario_id: Optional[str]

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_model(cls, model) -> "AnaliseResponseDTO":
        return cls(
            analise_id=model.analise_id,
            asteroide_id=model.asteroide_id,
            versao_modelo=model.versao_modelo,
            custo_extracao_usd=model.custo_extracao_usd,
            custo_transporte_usd=model.custo_transporte_usd,
            custo_processamento_usd=model.custo_processamento_usd,
            receita_estimada_usd=model.receita_estimada_usd,
            roi_percentual=model.roi_percentual,
            score_viabilidade=model.score_viabilidade,
            classificacao=model.classificacao,
            gerado_em_data=model.gerado_em_data.isoformat() if model.gerado_em_data else None,
            gerado_em_hora=str(model.gerado_em_hora) if model.gerado_em_hora else None,
            gerado_por_usuario_id=model.gerado_por_usuario_id,
        )


# ─────────────────────────────────────────────────────────────────────────────
# Recomendacao IA
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class RecomendacaoResponseDTO:
    """Contrato de saída para recomendação de IA."""
    recomendacao_id: int
    analise_id: int
    modelo_ia: str
    resumo_recomendacao: str
    plano_acao: Optional[str]
    confianca: Optional[float]
    criado_em_data: Optional[str]
    criado_em_hora: Optional[str]

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_model(cls, model) -> "RecomendacaoResponseDTO":
        return cls(
            recomendacao_id=model.recomendacao_id,
            analise_id=model.analise_id,
            modelo_ia=model.modelo_ia,
            resumo_recomendacao=model.resumo_recomendacao,
            plano_acao=model.plano_acao,
            confianca=model.confianca,
            criado_em_data=model.criado_em_data.isoformat() if model.criado_em_data else None,
            criado_em_hora=str(model.criado_em_hora) if model.criado_em_hora else None,
        )


# ─────────────────────────────────────────────────────────────────────────────
# Auxiliar interno
# ─────────────────────────────────────────────────────────────────────────────

def _float_or_none(value) -> Optional[float]:
    if value is None or value == "":
        return None
    return float(value)
