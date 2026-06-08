from __future__ import annotations

import csv
import io
from datetime import datetime
from zoneinfo import ZoneInfo

BRT = ZoneInfo("America/Sao_Paulo")

from flask import Blueprint, flash, g, make_response, redirect, render_template, request, url_for

from app.api.deps import carregar_usuario_logado, login_required, obter_ip_origem, validar_csrf_ou_erro
from app.db.session import db
from app.models.modelos import AnaliseViabilidade, Asteroide, RecomendacaoIA
from app.services.auditoria_service import registrar_log_dashboard
from app.services.auth_service import AuthError, alterar_senha, autenticar_usuario


bp = Blueprint("main", __name__)

# Colunas esperadas no CSV/XLSX de importação
_COLUNAS_ESPERADAS = {
    "codigo", "nome", "classe_espectral", "diametro_km",
    "delta_v_kms", "mineral_destaque", "valor_estimado_usd", "score_viabilidade",
}
# Aceita também "classe_espectal" (typo frequente no template exportado)
_ALIAS_COLUNAS = {"classe_espectal": "classe_espectral"}


@bp.get("/")
def index():
    usuario, _ = carregar_usuario_logado()
    if not usuario:
        return redirect(url_for("auth.login"))
    return redirect(url_for("main.dashboard"))


@bp.get("/dashboard")
@login_required
def dashboard():
    asteroides = Asteroide.query.order_by(Asteroide.score_viabilidade.desc()).limit(30).all()
    return render_template("dashboard.html", asteroides=asteroides)


@bp.post("/dashboard/exportar")
@login_required
def exportar_dashboard_csv():
    if not validar_csrf_ou_erro():
        return redirect(url_for("main.dashboard"))

    asteroides = Asteroide.query.order_by(Asteroide.score_viabilidade.desc()).all()
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(
        [
            "codigo",
            "nome",
            "classe_espectral",
            "diametro_km",
            "delta_v_kms",
            "mineral_destaque",
            "valor_estimado_usd",
            "score_viabilidade",
        ]
    )
    for item in asteroides:
        writer.writerow(
            [
                item.codigo,
                item.nome,
                item.classe_espectral or "",
                item.diametro_km or "",
                item.delta_v_kms or "",
                item.mineral_destaque or "",
                item.valor_estimado_usd or "",
                item.score_viabilidade,
            ]
        )

    data_ref = datetime.now(BRT).strftime("%Y%m%d_%H%M%S")
    nome_arquivo = f"dashboard_asteroides_{data_ref}.csv"
    registrar_log_dashboard(
        usuario_id=g.current_user.usuario_id,
        operacao="EXPORTACAO",
        formato="CSV",
        nome_arquivo=nome_arquivo,
        total_registros=len(asteroides),
        status="SUCESSO",
        ip_origem=obter_ip_origem(),
    )

    response = make_response(buffer.getvalue())
    response.headers["Content-Type"] = "text/csv; charset=utf-8"
    response.headers["Content-Disposition"] = f'attachment; filename="{nome_arquivo}"'
    return response


def _normalizar_cabecalho(cabecalho: list[str]) -> list[str]:
    """Aplica aliases de colunas e retorna lista normalizada."""
    return [_ALIAS_COLUNAS.get(c.strip().lower(), c.strip().lower()) for c in cabecalho]


def _importar_linhas_csv(linhas: list[dict]) -> tuple[int, int, list[str]]:
    """
    Importa ou atualiza asteroides a partir de linhas dicionarizadas.
    Retorna (inseridos, atualizados, erros).
    """
    inseridos = 0
    atualizados = 0
    erros: list[str] = []

    for i, linha in enumerate(linhas, start=2):  # linha 1 = cabeçalho
        codigo = (linha.get("codigo") or "").strip()
        if not codigo:
            erros.append(f"Linha {i}: campo 'codigo' vazio, ignorado.")
            continue

        try:
            asteroide = Asteroide.query.filter_by(codigo=codigo).first()
            novo = asteroide is None
            if novo:
                asteroide = Asteroide(codigo=codigo)

            asteroide.nome = (linha.get("nome") or codigo).strip()
            asteroide.classe_espectral = (linha.get("classe_espectral") or "").strip() or None

            def _float(val: str | None) -> float | None:
                try:
                    return float(val) if val not in (None, "") else None
                except (ValueError, TypeError):
                    return None

            asteroide.diametro_km = _float(linha.get("diametro_km"))
            asteroide.delta_v_kms = _float(linha.get("delta_v_kms"))
            asteroide.mineral_destaque = (linha.get("mineral_destaque") or "").strip() or None
            asteroide.valor_estimado_usd = _float(linha.get("valor_estimado_usd"))
            score = _float(linha.get("score_viabilidade"))
            asteroide.score_viabilidade = score if score is not None else 0.0

            if novo:
                db.session.add(asteroide)
                inseridos += 1
            else:
                atualizados += 1

        except Exception as exc:  # noqa: BLE001
            erros.append(f"Linha {i}: {exc}")

    db.session.commit()
    return inseridos, atualizados, erros


@bp.post("/dashboard/importar")
@login_required
def importar_dashboard_csv():
    if not validar_csrf_ou_erro():
        return redirect(url_for("main.dashboard"))

    arquivo = request.files.get("arquivo_dashboard")
    if not arquivo or not arquivo.filename:
        flash("Selecione um arquivo CSV ou XLSX para importar.", "warning")
        return redirect(url_for("main.dashboard"))

    nome = arquivo.filename.lower()
    formato = ""

    if nome.endswith(".csv"):
        formato = "CSV"
        conteudo = arquivo.stream.read().decode("utf-8", errors="ignore")
        leitor = csv.DictReader(io.StringIO(conteudo))
        cabecalho_norm = _normalizar_cabecalho(leitor.fieldnames or [])
        linhas = []
        for row in leitor:
            linha_norm = {_normalizar_cabecalho([k])[0]: v for k, v in row.items()}
            linhas.append(linha_norm)

    elif nome.endswith((".xlsx", ".xls")):
        formato = "XLSX"
        try:
            import openpyxl  # noqa: PLC0415
            wb = openpyxl.load_workbook(arquivo.stream, read_only=True, data_only=True)
            ws = wb.active
            rows = list(ws.iter_rows(values_only=True))
            if not rows:
                flash("Arquivo XLSX vazio.", "warning")
                return redirect(url_for("main.dashboard"))
            cabecalho_raw = [str(c) if c is not None else "" for c in rows[0]]
            cabecalho_norm = _normalizar_cabecalho(cabecalho_raw)
            linhas = []
            for row in rows[1:]:
                linha_norm = {cabecalho_norm[j]: (str(v) if v is not None else "") for j, v in enumerate(row)}
                linhas.append(linha_norm)
        except Exception as exc:  # noqa: BLE001
            flash(f"Erro ao ler XLSX: {exc}", "danger")
            return redirect(url_for("main.dashboard"))
    else:
        flash("Somente arquivos .csv ou .xlsx sao aceitos.", "danger")
        return redirect(url_for("main.dashboard"))

    if not linhas:
        flash("Nenhuma linha de dados encontrada no arquivo.", "warning")
        return redirect(url_for("main.dashboard"))

    inseridos, atualizados, erros = _importar_linhas_csv(linhas)
    total = inseridos + atualizados

    registrar_log_dashboard(
        usuario_id=g.current_user.usuario_id,
        operacao="IMPORTACAO",
        formato=formato,
        nome_arquivo=arquivo.filename,
        total_registros=total,
        status="SUCESSO" if not erros else "PARCIAL",
        ip_origem=obter_ip_origem(),
    )

    msg = f"Importacao concluida: {inseridos} novo(s), {atualizados} atualizado(s)."
    if erros:
        msg += f" Avisos: {'; '.join(erros[:3])}"
    flash(msg, "success" if not erros else "warning")
    return redirect(url_for("main.dashboard"))


@bp.get("/recomendacoes")
@login_required
def recomendacoes():
    registros = (
        db.session.query(RecomendacaoIA, AnaliseViabilidade, Asteroide)
        .join(AnaliseViabilidade, AnaliseViabilidade.analise_id == RecomendacaoIA.analise_id)
        .join(Asteroide, Asteroide.asteroide_id == AnaliseViabilidade.asteroide_id)
        .order_by(RecomendacaoIA.criado_em_data.desc(), RecomendacaoIA.criado_em_hora.desc())
        .limit(40)
        .all()
    )
    return render_template("recommendations.html", registros=registros)


# ─────────────────────────────────────────────────────────────────────────────
# Alteração de senha sem login (rota pública — usuário esqueceu a senha)
# ─────────────────────────────────────────────────────────────────────────────

@bp.get("/alterar-senha-login")
def change_password_login():
    usuario, _ = carregar_usuario_logado()
    if usuario:
        return redirect(url_for("auth.alterar_senha_page"))
    return render_template("change_password_login.html")


@bp.post("/alterar-senha-login")
def change_password_login_post():
    if not validar_csrf_ou_erro():
        return redirect(url_for("main.change_password_login"))

    from app.models.modelos import User  # noqa: PLC0415

    email = request.form.get("email", "").strip()
    senha_atual = request.form.get("senha_atual", "")
    nova_senha = request.form.get("nova_senha", "")

    usuario = User.query.filter_by(email=email, ativo=True).first()
    if not usuario:
        flash("E-mail nao encontrado ou conta inativa.", "danger")
        return redirect(url_for("main.change_password_login"))

    # Usa autenticação local sem criar sessão — só valida credenciais
    from app.core.security import verificar_senha as _verifica  # noqa: PLC0415
    if not _verifica(senha_atual, usuario.senha_hash):
        flash("Senha atual incorreta.", "danger")
        return redirect(url_for("main.change_password_login"))

    try:
        from flask import current_app  # noqa: PLC0415
        alterar_senha(
            solicitante=usuario,
            senha_atual=senha_atual,
            nova_senha=nova_senha,
            motivo="RECUPERACAO_SEM_LOGIN",
            profundidade_historico=current_app.config.get("PASSWORD_HISTORY_DEPTH", 5),
        )
    except (AuthError, ValueError) as exc:
        flash(str(exc), "danger")
        return redirect(url_for("main.change_password_login"))

    flash("Senha alterada com sucesso. Faca login com a nova senha.", "success")
    return redirect(url_for("auth.login"))
