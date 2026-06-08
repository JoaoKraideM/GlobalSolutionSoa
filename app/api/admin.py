from __future__ import annotations

from flask import Blueprint, render_template

from app.api.deps import role_required
from app.services.auditoria_service import (
    listar_contas_criadas_por_admin,
    listar_ips_com_tentativas_suspeitas,
    listar_logs_dashboard,
)


bp = Blueprint("admin", __name__, url_prefix="/admin")


@bp.get("/logs/dashboard")
@role_required("ADMIN")
def logs_dashboard():
    logs = listar_logs_dashboard(limite=100)
    return render_template("admin/dashboard_logs.html", logs=logs)


@bp.get("/logs/login-ips")
@role_required("ADMIN")
def logs_login_ips():
    ips = listar_ips_com_tentativas_suspeitas(limite=100, falhas_minimas=3, horas=24)
    return render_template("admin/login_ip_logs.html", ips=ips)


@bp.get("/logs/contas-criadas")
@role_required("ADMIN")
def logs_contas_criadas():
    contas = listar_contas_criadas_por_admin(limite=100)
    return render_template("admin/account_creation_logs.html", contas=contas)
