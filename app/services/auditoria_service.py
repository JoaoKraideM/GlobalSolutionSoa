from __future__ import annotations

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from sqlalchemy import and_, desc, func, or_
from sqlalchemy.orm import aliased

from app.db.session import db
from app.models.modelos import (
    AdminAccountCreationLog,
    DashboardFileLog,
    LoginAttempt,
    User,
)

BRT = ZoneInfo("America/Sao_Paulo")


def registrar_tentativa_login(
    email: str,
    ip_origem: str,
    user_agent: str | None,
    sucesso: bool,
    motivo_falha: str | None = None,
    usuario_id: str | None = None,
) -> None:
    """Persiste uma tentativa de login.  Data e hora são geradas automaticamente
    pelos defaults do modelo (utcnow_date / utcnow_time)."""
    tentativa = LoginAttempt(
        usuario_id=usuario_id,
        email_informado=email,
        ip_origem=ip_origem or "0.0.0.0",
        user_agent=(user_agent or "")[:300],
        sucesso=sucesso,
        motivo_falha=motivo_falha,
    )
    db.session.add(tentativa)
    db.session.commit()


def contar_falhas_recentes_por_ip(ip_origem: str, janela_minutos: int) -> int:
    """Conta tentativas de login com falha de um IP dentro de uma janela de tempo.

    Como data e hora estão em colunas separadas, o filtro precisa comparar
    os dois campos juntos.  A lógica é:
        (data > limite_data)  →  qualquer horário desse dia já é mais recente
        OU
        (data == limite_data AND hora >= limite_hora)  →  mesmo dia, mas após o horário limite

    Esse padrão é equivalente a DATETIME >= limite, porém totalmente indexável
    pois não usa funções sobre as colunas.
    """
    agora = datetime.now(BRT)
    limite = agora - timedelta(minutes=janela_minutos)
    limite_data = limite.date()
    limite_hora = limite.time().replace(tzinfo=None)

    total = (
        db.session.query(func.count(LoginAttempt.tentativa_id))
        .filter(
            LoginAttempt.ip_origem == (ip_origem or "0.0.0.0"),
            LoginAttempt.sucesso.is_(False),
            or_(
                LoginAttempt.ocorreu_em_data > limite_data,
                and_(
                    LoginAttempt.ocorreu_em_data == limite_data,
                    LoginAttempt.ocorreu_em_hora >= limite_hora,
                ),
            ),
        )
        .scalar()
    )
    return int(total or 0)


def registrar_log_dashboard(
    usuario_id: str,
    operacao: str,
    formato: str,
    nome_arquivo: str | None,
    total_registros: int | None,
    status: str,
    ip_origem: str | None,
) -> None:
    log = DashboardFileLog(
        usuario_id=usuario_id,
        operacao=operacao.upper(),
        formato=formato.upper(),
        nome_arquivo=nome_arquivo,
        total_registros=total_registros,
        status=status.upper(),
        ip_origem=ip_origem,
    )
    db.session.add(log)
    db.session.commit()


def registrar_conta_criada_por_admin(
    admin_usuario_id: str,
    novo_usuario_id: str,
    novo_usuario_role: str,
    ip_origem: str | None,
) -> None:
    log = AdminAccountCreationLog(
        admin_usuario_id=admin_usuario_id,
        novo_usuario_id=novo_usuario_id,
        novo_usuario_role=novo_usuario_role.upper(),
        ip_origem=ip_origem,
    )
    db.session.add(log)
    db.session.commit()


def listar_logs_dashboard(limite: int = 100):
    """Retorna logs de dashboard ordenados do mais recente para o mais antigo.

    Ordenação por dois campos: primeiro pela data (mais recente), depois pela
    hora (mais recente dentro do mesmo dia).  Isso garante a ordenação correta
    mesmo com dados de dias diferentes.
    """
    return (
        db.session.query(DashboardFileLog, User.email.label("email_usuario"))
        .join(User, User.usuario_id == DashboardFileLog.usuario_id)
        .order_by(
            desc(DashboardFileLog.ocorreu_em_data),
            desc(DashboardFileLog.ocorreu_em_hora),
        )
        .limit(limite)
        .all()
    )


def listar_ips_com_tentativas_suspeitas(limite: int = 100, falhas_minimas: int = 5, horas: int = 24):
    """Agrupa IPs com muitas tentativas de login com falha nas últimas N horas.

    O filtro de janela de tempo usa a mesma lógica de (data, hora) da função
    contar_falhas_recentes_por_ip.  Os campos primeira_data/hora e ultima_data/hora
    retornam os extremos do período de atividade suspeita — separados para permitir
    filtragem independente no template ou em relatórios futuros.
    """
    agora = datetime.now(BRT)
    inicio = agora - timedelta(hours=horas)
    inicio_data = inicio.date()
    inicio_hora = inicio.time().replace(tzinfo=None)

    return (
        db.session.query(
            LoginAttempt.ip_origem,
            func.count(LoginAttempt.tentativa_id).label("total_falhas"),
            func.min(LoginAttempt.ocorreu_em_data).label("primeira_data"),
            func.min(LoginAttempt.ocorreu_em_hora).label("primeira_hora"),
            func.max(LoginAttempt.ocorreu_em_data).label("ultima_data"),
            func.max(LoginAttempt.ocorreu_em_hora).label("ultima_hora"),
        )
        .filter(
            LoginAttempt.sucesso.is_(False),
            or_(
                LoginAttempt.ocorreu_em_data > inicio_data,
                and_(
                    LoginAttempt.ocorreu_em_data == inicio_data,
                    LoginAttempt.ocorreu_em_hora >= inicio_hora,
                ),
            ),
        )
        .group_by(LoginAttempt.ip_origem)
        .having(func.count(LoginAttempt.tentativa_id) >= falhas_minimas)
        .order_by(desc("total_falhas"))
        .limit(limite)
        .all()
    )


def listar_contas_criadas_por_admin(limite: int = 100):
    AdminCriador  = aliased(User)
    UsuarioCriado = aliased(User)
    return (
        db.session.query(
            AdminAccountCreationLog,
            AdminCriador.email.label("email_admin"),
            UsuarioCriado.email.label("email_criado"),
        )
        .join(AdminCriador,  AdminCriador.usuario_id  == AdminAccountCreationLog.admin_usuario_id)
        .join(UsuarioCriado, UsuarioCriado.usuario_id == AdminAccountCreationLog.novo_usuario_id)
        .order_by(
            desc(AdminAccountCreationLog.ocorreu_em_data),
            desc(AdminAccountCreationLog.ocorreu_em_hora),
        )
        .limit(limite)
        .all()
    )
