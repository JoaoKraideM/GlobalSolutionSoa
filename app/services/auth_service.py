from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy import desc
from sqlalchemy.exc import IntegrityError

from app.core.security import criar_jwt, hash_senha, verificar_senha
from app.db.session import db
from app.models.modelos import PasswordHistory, Role, User, utcnow_date, utcnow_time
from app.schemas.schemas import validar_email, validar_nome, validar_role, validar_senha
from app.services.auditoria_service import (
    contar_falhas_recentes_por_ip,
    registrar_conta_criada_por_admin,
    registrar_tentativa_login,
)


class AuthError(Exception):
    pass


@dataclass
class ResultadoLogin:
    token: str
    usuario: User
    role: str


def usuario_e_admin(usuario: User) -> bool:
    return any(role.codigo == "ADMIN" for role in usuario.roles)


def role_principal_usuario(usuario: User) -> str:
    codigos = {role.codigo for role in usuario.roles}
    return "ADMIN" if "ADMIN" in codigos else "ANALISTA"


def _obter_role(codigo: str) -> Role:
    role = Role.query.filter_by(codigo=codigo).first()
    if not role:
        raise AuthError(f"Role {codigo} nao encontrada.")
    return role


def criar_usuario(
    nome_completo: str,
    email: str,
    senha: str,
    role_codigo: str,
    criador: User | None = None,
    ip_origem: str | None = None,
) -> User:
    nome_validado  = validar_nome(nome_completo)
    email_validado = validar_email(email)
    senha_validada = validar_senha(senha)
    role_validada  = validar_role(role_codigo)

    if User.query.filter_by(email=email_validado).first():
        raise AuthError("Ja existe uma conta com este e-mail.")

    if role_validada == "ADMIN":
        existe_admin = (
            db.session.query(User)
            .join(User.roles)
            .filter(Role.codigo == "ADMIN")
            .first()
        )
        if existe_admin and (not criador or not usuario_e_admin(criador)):
            raise AuthError("Somente um ADMIN pode criar outra conta ADMIN.")

    role_obj = _obter_role(role_validada)

    usuario = User(
        nome_completo=nome_validado,
        email=email_validado,
        senha_hash=hash_senha(senha_validada),
        criado_por=(criador.usuario_id if criador else None),
        ativo=True,
    )
    usuario.roles.append(role_obj)

    try:
        db.session.add(usuario)
        db.session.flush()

        historico = PasswordHistory(
            usuario_id=usuario.usuario_id,
            senha_hash=usuario.senha_hash,
            alterada_por=(criador.usuario_id if criador else usuario.usuario_id),
            motivo="CRIACAO_CONTA",
        )
        db.session.add(historico)
        db.session.commit()
    except IntegrityError as exc:
        db.session.rollback()
        raise AuthError("Falha ao criar usuario.") from exc

    if criador and usuario_e_admin(criador):
        registrar_conta_criada_por_admin(
            admin_usuario_id=criador.usuario_id,
            novo_usuario_id=usuario.usuario_id,
            novo_usuario_role=role_validada,
            ip_origem=ip_origem,
        )

    return usuario


def autenticar_usuario(
    email: str,
    senha: str,
    ip_origem: str,
    user_agent: str | None,
    config: dict,
) -> ResultadoLogin:
    email_validado = validar_email(email)

    falhas_recentes = contar_falhas_recentes_por_ip(
        ip_origem=ip_origem,
        janela_minutos=int(config["LOGIN_FAIL_WINDOW_MIN"]),
    )
    if falhas_recentes >= int(config["LOGIN_FAIL_LIMIT"]):
        registrar_tentativa_login(
            email=email_validado,
            ip_origem=ip_origem,
            user_agent=user_agent,
            sucesso=False,
            motivo_falha="IP_BLOQUEADO_TEMPORARIAMENTE",
        )
        raise AuthError("IP temporariamente bloqueado por tentativas excessivas.")

    usuario = User.query.filter_by(email=email_validado).first()
    if not usuario:
        registrar_tentativa_login(email=email_validado, ip_origem=ip_origem,
                                  user_agent=user_agent, sucesso=False,
                                  motivo_falha="USUARIO_NAO_ENCONTRADO")
        raise AuthError("Credenciais invalidas.")

    if not usuario.ativo:
        registrar_tentativa_login(email=email_validado, ip_origem=ip_origem,
                                  user_agent=user_agent, sucesso=False,
                                  motivo_falha="USUARIO_INATIVO",
                                  usuario_id=usuario.usuario_id)
        raise AuthError("Usuario inativo.")

    if not verificar_senha(senha, usuario.senha_hash):
        registrar_tentativa_login(email=email_validado, ip_origem=ip_origem,
                                  user_agent=user_agent, sucesso=False,
                                  motivo_falha="SENHA_INVALIDA",
                                  usuario_id=usuario.usuario_id)
        raise AuthError("Credenciais invalidas.")

    role  = role_principal_usuario(usuario)
    token = criar_jwt(config=config, usuario_id=usuario.usuario_id,
                      email=usuario.email, role=role)

    # Atualiza os dois campos separados de último login
    usuario.ultimo_login_em_data = utcnow_date()
    usuario.ultimo_login_em_hora = utcnow_time()
    db.session.add(usuario)
    db.session.commit()

    registrar_tentativa_login(email=email_validado, ip_origem=ip_origem,
                              user_agent=user_agent, sucesso=True,
                              usuario_id=usuario.usuario_id)

    return ResultadoLogin(token=token, usuario=usuario, role=role)


def alterar_senha(
    solicitante: User,
    nova_senha: str,
    senha_atual: str | None = None,
    email_alvo: str | None = None,
    motivo: str = "ALTERACAO_MANUAL",
    profundidade_historico: int = 5,
) -> User:
    alvo = solicitante
    if email_alvo:
        email_validado = validar_email(email_alvo)
        alvo = User.query.filter_by(email=email_validado).first()
        if not alvo:
            raise AuthError("Usuario alvo nao encontrado.")

    if solicitante.usuario_id != alvo.usuario_id and not usuario_e_admin(solicitante):
        raise AuthError("Somente ADMIN pode alterar senha de outro usuario.")

    if solicitante.usuario_id == alvo.usuario_id:
        if not senha_atual:
            raise AuthError("Informe a senha atual para alterar sua senha.")
        if not verificar_senha(senha_atual, alvo.senha_hash):
            raise AuthError("Senha atual invalida.")

    senha_validada = validar_senha(nova_senha)

    ultimas_senhas = (
        PasswordHistory.query.filter_by(usuario_id=alvo.usuario_id)
        .order_by(desc(PasswordHistory.alterada_em_data),
                  desc(PasswordHistory.alterada_em_hora))
        .limit(profundidade_historico)
        .all()
    )
    for historico in ultimas_senhas:
        if verificar_senha(senha_validada, historico.senha_hash):
            raise AuthError("A nova senha nao pode repetir senhas recentes.")

    alvo.senha_hash = hash_senha(senha_validada)
    # Atualiza data e hora de modificação nos dois campos separados
    alvo.atualizado_em_data = utcnow_date()
    alvo.atualizado_em_hora = utcnow_time()

    novo_historico = PasswordHistory(
        usuario_id=alvo.usuario_id,
        senha_hash=alvo.senha_hash,
        alterada_por=solicitante.usuario_id,
        motivo=motivo,
    )
    db.session.add(alvo)
    db.session.add(novo_historico)
    db.session.commit()

    return alvo
