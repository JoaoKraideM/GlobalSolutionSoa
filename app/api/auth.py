from __future__ import annotations

from flask import Blueprint, current_app, flash, g, redirect, render_template, request, session, url_for

from app.api.deps import carregar_usuario_logado, login_required, obter_ip_origem, obter_user_agent, validar_csrf_ou_erro
from app.schemas.schemas import validar_role
from app.services.auth_service import AuthError, alterar_senha, criar_usuario, autenticar_usuario, usuario_e_admin


bp = Blueprint("auth", __name__)


@bp.get("/login")
def login():
    usuario, _ = carregar_usuario_logado()
    if usuario:
        return redirect(url_for("main.dashboard"))
    return render_template("login.html")


@bp.post("/login")
def login_post():
    if not validar_csrf_ou_erro():
        return redirect(url_for("auth.login"))

    email = request.form.get("email", "")
    senha = request.form.get("senha", "")
    ip = obter_ip_origem()
    user_agent = obter_user_agent()

    try:
        resultado = autenticar_usuario(
            email=email,
            senha=senha,
            ip_origem=ip,
            user_agent=user_agent,
            config=current_app.config,
        )
    except AuthError as exc:
        flash(str(exc), "danger")
        return redirect(url_for("auth.login"))

    session["access_token"] = resultado.token
    session["user_email"] = resultado.usuario.email
    session["user_role"] = resultado.role
    flash("Login realizado com sucesso.", "success")
    return redirect(url_for("main.dashboard"))


@bp.post("/logout")
def logout():
    session.pop("access_token", None)
    session.pop("user_email", None)
    session.pop("user_role", None)
    flash("Sessao finalizada.", "info")
    return redirect(url_for("auth.login"))


@bp.get("/cadastro")
def cadastro():
    usuario, role = carregar_usuario_logado()
    return render_template("register.html", current_user=usuario, current_role=role)


@bp.post("/cadastro")
def cadastro_post():
    if not validar_csrf_ou_erro():
        return redirect(url_for("auth.cadastro"))

    nome = request.form.get("nome_completo", "")
    email = request.form.get("email", "")
    senha = request.form.get("senha", "")
    role_enviado = request.form.get("role", "ANALISTA")
    ip = obter_ip_origem()

    solicitante, _ = carregar_usuario_logado()
    role_final = "ANALISTA"
    if solicitante and usuario_e_admin(solicitante):
        role_final = validar_role(role_enviado)

    try:
        criar_usuario(
            nome_completo=nome,
            email=email,
            senha=senha,
            role_codigo=role_final,
            criador=solicitante,
            ip_origem=ip,
        )
    except (AuthError, ValueError) as exc:
        flash(str(exc), "danger")
        return redirect(url_for("auth.cadastro"))

    if solicitante and usuario_e_admin(solicitante):
        flash("Conta criada com sucesso pelo ADMIN.", "success")
        return redirect(url_for("admin.logs_contas_criadas"))

    flash("Conta criada com sucesso. Agora faca login.", "success")
    return redirect(url_for("auth.login"))


@bp.get("/alterar-senha")
@login_required
def alterar_senha_page():
    return render_template("change_password.html", current_user=g.current_user, current_role=g.current_role)


@bp.post("/alterar-senha")
@login_required
def alterar_senha_post():
    if not validar_csrf_ou_erro():
        return redirect(url_for("auth.alterar_senha_page"))

    solicitante = g.current_user
    senha_atual = request.form.get("senha_atual")
    nova_senha = request.form.get("nova_senha", "")
    email_alvo = request.form.get("email_alvo", "").strip() or None

    try:
        alterar_senha(
            solicitante=solicitante,
            senha_atual=senha_atual,
            nova_senha=nova_senha,
            email_alvo=email_alvo,
            motivo="ALTERACAO_VIA_PORTAL",
            profundidade_historico=current_app.config["PASSWORD_HISTORY_DEPTH"],
        )
    except (AuthError, ValueError) as exc:
        flash(str(exc), "danger")
        return redirect(url_for("auth.alterar_senha_page"))

    if email_alvo and email_alvo.lower() != solicitante.email.lower():
        flash("Senha do colaborador alterada com sucesso.", "success")
        return redirect(url_for("auth.alterar_senha_page"))

    session.pop("access_token", None)
    flash("Senha alterada com sucesso. Entre novamente com a nova senha.", "success")
    return redirect(url_for("auth.login"))
