from __future__ import annotations

from app.core.security import hash_senha
from app.db.session import db
from app.models.modelos import AnaliseViabilidade, Asteroide, PasswordHistory, RecomendacaoIA, Role, User


def _seed_roles() -> None:
    base_roles = [
        ("ADMIN", "Administrador", "Acesso total ao ambiente interno"),
        ("ANALISTA", "Analista", "Acesso ao dashboard e recomendacoes"),
    ]
    for codigo, nome, descricao in base_roles:
        if not Role.query.filter_by(codigo=codigo).first():
            db.session.add(Role(codigo=codigo, nome=nome, descricao=descricao))
    db.session.commit()


def _seed_admin_padrao(config: dict) -> None:
    admin_existente = (
        db.session.query(User)
        .join(User.roles)
        .filter(Role.codigo == "ADMIN")
        .first()
    )
    if admin_existente:
        return

    role_admin = Role.query.filter_by(codigo="ADMIN").first()
    if not role_admin:
        return

    admin = User(
        nome_completo=config["DEFAULT_ADMIN_NAME"],
        email=config["DEFAULT_ADMIN_EMAIL"].strip().lower(),
        senha_hash=hash_senha(config["DEFAULT_ADMIN_PASSWORD"]),
        ativo=True,
    )
    admin.roles.append(role_admin)
    db.session.add(admin)
    db.session.flush()

    db.session.add(
        PasswordHistory(
            usuario_id=admin.usuario_id,
            senha_hash=admin.senha_hash,
            alterada_por=admin.usuario_id,
            motivo="SEED_ADMIN_INICIAL",
        )
    )
    db.session.commit()


def _seed_dados_asteroides() -> None:
    # Garante que os 3 asteroides base existem (upsert por codigo)
    _asteroides_base = [
        dict(
            codigo="2025-QA1", nome="Atena Prime", classe_espectral="M",
            diametro_km=1.34, delta_v_kms=4.8, mineral_destaque="Platina",
            valor_estimado_usd=4_500_000_000, score_viabilidade=87.2,
        ),
        dict(
            codigo="2024-KR9", nome="Helios Ridge", classe_espectral="S",
            diametro_km=0.92, delta_v_kms=5.2, mineral_destaque="Niquel",
            valor_estimado_usd=980_000_000, score_viabilidade=74.6,
        ),
        dict(
            codigo="2031-ZT3", nome="Orion Dust", classe_espectral="C",
            diametro_km=1.88, delta_v_kms=6.1, mineral_destaque="Agua para propelente",
            valor_estimado_usd=1_240_000_000, score_viabilidade=69.4,
        ),
        dict(
            codigo="2028-NX7", nome="Vega Shard", classe_espectral="M",
            diametro_km=0.65, delta_v_kms=3.9, mineral_destaque="Ferro-Niquel",
            valor_estimado_usd=720_000_000, score_viabilidade=61.8,
        ),
        dict(
            codigo="2033-PL2", nome="Kronos Belt", classe_espectral="X",
            diametro_km=2.10, delta_v_kms=7.4, mineral_destaque="Iridio",
            valor_estimado_usd=9_800_000_000, score_viabilidade=55.3,
        ),
    ]

    asteroides_criados: list[Asteroide] = []
    for dados in _asteroides_base:
        ast = Asteroide.query.filter_by(codigo=dados["codigo"]).first()
        if not ast:
            ast = Asteroide(**dados)
            db.session.add(ast)
        asteroides_criados.append(ast)

    db.session.flush()

    # ── Seed de análises e recomendações ──────────────────────────────────────
    # Só insere se ainda não houver nenhuma recomendação
    if RecomendacaoIA.query.count() > 0:
        db.session.commit()
        return

    _analises_dados = [
        dict(
            asteroide=asteroides_criados[0],
            versao_modelo="v2.4",
            custo_extracao_usd=950_000_000,
            custo_transporte_usd=320_000_000,
            custo_processamento_usd=140_000_000,
            receita_estimada_usd=4_500_000_000,
            roi_percentual=216.5,
            score_viabilidade=87.2,
            classificacao="ALTA",
            resumo="Iniciar missao de validacao orbital com foco em extracao de metais raros.",
            plano="Fase 1: sonda de prospeccao. Fase 2: modulo de extracao automatizada. Fase 3: retorno amostral.",
            confianca=91.3,
        ),
        dict(
            asteroide=asteroides_criados[1],
            versao_modelo="v2.4",
            custo_extracao_usd=410_000_000,
            custo_transporte_usd=270_000_000,
            custo_processamento_usd=115_000_000,
            receita_estimada_usd=980_000_000,
            roi_percentual=23.2,
            score_viabilidade=74.6,
            classificacao="MEDIA",
            resumo="Priorizar estudo de rota para reduzir delta-v e renegociar janela de lancamento.",
            plano="Executar simulacao de transferencia Hohmann em 3 cenarios de janela.",
            confianca=82.7,
        ),
        dict(
            asteroide=asteroides_criados[2],
            versao_modelo="v2.4",
            custo_extracao_usd=310_000_000,
            custo_transporte_usd=205_000_000,
            custo_processamento_usd=88_000_000,
            receita_estimada_usd=1_240_000_000,
            roi_percentual=148.9,
            score_viabilidade=69.4,
            classificacao="MEDIA",
            resumo="Alta concentracao de volateis util para producao de propelente in-situ (ISRU).",
            plano="Avaliar instalacao de reator de eletrolise na superficie para producao de H2/O2.",
            confianca=76.1,
        ),
        dict(
            asteroide=asteroides_criados[3],
            versao_modelo="v2.4",
            custo_extracao_usd=180_000_000,
            custo_transporte_usd=140_000_000,
            custo_processamento_usd=62_000_000,
            receita_estimada_usd=720_000_000,
            roi_percentual=88.6,
            score_viabilidade=61.8,
            classificacao="MEDIA",
            resumo="Candidato secundario para missao combinada com Atena Prime — delta-v favoravel.",
            plano="Incluir como ponto de escala na rota de retorno da missao principal.",
            confianca=68.4,
        ),
        dict(
            asteroide=asteroides_criados[4],
            versao_modelo="v2.4",
            custo_extracao_usd=2_100_000_000,
            custo_transporte_usd=890_000_000,
            custo_processamento_usd=540_000_000,
            receita_estimada_usd=9_800_000_000,
            roi_percentual=181.4,
            score_viabilidade=55.3,
            classificacao="BAIXA",
            resumo="Alto potencial economico mas delta-v elevado torna missao tecnicamente arriscada no horizonte atual.",
            plano="Aguardar maturidade de propulsao ionica de alta impulso especifico. Reavaliar em 2035.",
            confianca=54.9,
        ),
    ]

    for d in _analises_dados:
        analise = AnaliseViabilidade(
            asteroide_id=d["asteroide"].asteroide_id,
            versao_modelo=d["versao_modelo"],
            custo_extracao_usd=d["custo_extracao_usd"],
            custo_transporte_usd=d["custo_transporte_usd"],
            custo_processamento_usd=d["custo_processamento_usd"],
            receita_estimada_usd=d["receita_estimada_usd"],
            roi_percentual=d["roi_percentual"],
            score_viabilidade=d["score_viabilidade"],
            classificacao=d["classificacao"],
        )
        db.session.add(analise)
        db.session.flush()

        recomendacao = RecomendacaoIA(
            analise_id=analise.analise_id,
            modelo_ia="astro-rank-gpt",
            resumo_recomendacao=d["resumo"],
            plano_acao=d["plano"],
            confianca=d["confianca"],
        )
        db.session.add(recomendacao)

    db.session.commit()


def inicializar_banco(config: dict) -> None:
    db.create_all()
    _seed_roles()
    _seed_admin_padrao(config)
    _seed_dados_asteroides()
