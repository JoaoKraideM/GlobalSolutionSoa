from __future__ import annotations

import uuid
from datetime import date, datetime, time
from zoneinfo import ZoneInfo

from app.db.session import db


# ─────────────────────────────────────────────────────────────────────────────
# Fuso horário brasileiro (UTC-3 / UTC-2 no horário de verão)
# ─────────────────────────────────────────────────────────────────────────────
BRT = ZoneInfo("America/Sao_Paulo")

# ─────────────────────────────────────────────────────────────────────────────
# Helpers de default para colunas DATE e TIME separadas
# ─────────────────────────────────────────────────────────────────────────────
# Por que funções separadas em vez de lambdas inline?
# O SQLAlchemy chama o callable do parâmetro `default` uma vez por INSERT.
# Usar funções nomeadas facilita o teste unitário (pode ser substituída por mock)
# e deixa o código mais legível nas definições das colunas abaixo.

def utcnow_date() -> date:
    """Retorna a data atual no horário de Brasília (America/Sao_Paulo)."""
    return datetime.now(BRT).date()

def utcnow_time() -> time:
    """Retorna o horário atual no horário de Brasília (sem fuso — MySQL TIME não armazena fuso)."""
    return datetime.now(BRT).time().replace(tzinfo=None)


# ─────────────────────────────────────────────────────────────────────────────
# Tabela de associação N:N entre Usuario e Role
# ─────────────────────────────────────────────────────────────────────────────

usuario_roles = db.Table(
    "usuario_roles",
    db.Column("usuario_id", db.String(36), db.ForeignKey("usuarios.usuario_id"), primary_key=True),
    db.Column("role_id",    db.Integer,    db.ForeignKey("roles.role_id"),        primary_key=True),
    db.Column("atribuido_em_data", db.Date, nullable=False, default=utcnow_date),
    db.Column("atribuido_em_hora", db.Time, nullable=False, default=utcnow_time),
)


class Role(db.Model):
    __tablename__ = "roles"

    role_id   = db.Column(db.Integer,     primary_key=True)
    codigo    = db.Column(db.String(40),  unique=True, nullable=False)
    nome      = db.Column(db.String(80),  nullable=False)
    descricao = db.Column(db.String(200), nullable=True)
    criado_em_data = db.Column(db.Date, nullable=False, default=utcnow_date)
    criado_em_hora = db.Column(db.Time, nullable=False, default=utcnow_time)


class User(db.Model):
    __tablename__ = "usuarios"

    usuario_id    = db.Column(db.String(36),  primary_key=True, default=lambda: str(uuid.uuid4()))
    nome_completo = db.Column(db.String(140), nullable=False)
    email         = db.Column(db.String(255), unique=True, index=True, nullable=False)
    senha_hash    = db.Column(db.String(255), nullable=False)
    ativo         = db.Column(db.Boolean,     default=True, nullable=False)
    criado_por    = db.Column(db.String(36),  db.ForeignKey("usuarios.usuario_id"), nullable=True)

    # Nullable: só é preenchido após o primeiro login com sucesso
    ultimo_login_em_data = db.Column(db.Date, nullable=True)
    ultimo_login_em_hora = db.Column(db.Time, nullable=True)

    criado_em_data = db.Column(db.Date, nullable=False, default=utcnow_date)
    criado_em_hora = db.Column(db.Time, nullable=False, default=utcnow_time)

    # onupdate: o SQLAlchemy chama utcnow_date/utcnow_time automaticamente
    # sempre que a linha é modificada via ORM — equivalente ao ON UPDATE do MySQL.
    atualizado_em_data = db.Column(db.Date, nullable=False, default=utcnow_date, onupdate=utcnow_date)
    atualizado_em_hora = db.Column(db.Time, nullable=False, default=utcnow_time, onupdate=utcnow_time)

    roles = db.relationship("Role", secondary=usuario_roles, backref=db.backref("usuarios", lazy="dynamic"))
    senha_historico = db.relationship(
        "PasswordHistory",
        back_populates="usuario",
        foreign_keys="PasswordHistory.usuario_id",
        lazy=True,
        cascade="all, delete-orphan",
    )


class PasswordHistory(db.Model):
    __tablename__ = "senha_historico"

    historico_id = db.Column(db.Integer,    primary_key=True, autoincrement=True)
    usuario_id   = db.Column(db.String(36), db.ForeignKey("usuarios.usuario_id"), nullable=False, index=True)
    senha_hash   = db.Column(db.String(255), nullable=False)
    alterada_por = db.Column(db.String(36), db.ForeignKey("usuarios.usuario_id"), nullable=True)
    motivo       = db.Column(db.String(120), nullable=True)
    alterada_em_data = db.Column(db.Date, nullable=False, default=utcnow_date, index=True)
    alterada_em_hora = db.Column(db.Time, nullable=False, default=utcnow_time)

    usuario = db.relationship("User", foreign_keys=[usuario_id], back_populates="senha_historico")


class LoginAttempt(db.Model):
    __tablename__ = "auth_tentativas_login"

    tentativa_id    = db.Column(db.Integer,    primary_key=True, autoincrement=True)
    usuario_id      = db.Column(db.String(36), db.ForeignKey("usuarios.usuario_id"), nullable=True, index=True)
    email_informado = db.Column(db.String(255), nullable=False, index=True)
    ip_origem       = db.Column(db.String(64),  nullable=False, index=True)
    user_agent      = db.Column(db.String(300), nullable=True)
    sucesso         = db.Column(db.Boolean,     nullable=False, default=False)
    motivo_falha    = db.Column(db.String(120), nullable=True)
    ocorreu_em_data = db.Column(db.Date, nullable=False, default=utcnow_date, index=True)
    ocorreu_em_hora = db.Column(db.Time, nullable=False, default=utcnow_time)


class DashboardFileLog(db.Model):
    __tablename__ = "dashboard_arquivo_logs"

    log_arquivo_id  = db.Column(db.Integer,    primary_key=True, autoincrement=True)
    usuario_id      = db.Column(db.String(36), db.ForeignKey("usuarios.usuario_id"), nullable=False, index=True)
    operacao        = db.Column(db.String(20),  nullable=False)
    formato         = db.Column(db.String(10),  nullable=False)
    nome_arquivo    = db.Column(db.String(180), nullable=True)
    total_registros = db.Column(db.Integer,     nullable=True)
    status          = db.Column(db.String(20),  nullable=False, default="SUCESSO")
    ip_origem       = db.Column(db.String(64),  nullable=True)
    ocorreu_em_data = db.Column(db.Date, nullable=False, default=utcnow_date, index=True)
    ocorreu_em_hora = db.Column(db.Time, nullable=False, default=utcnow_time)


class AdminAccountCreationLog(db.Model):
    __tablename__ = "admin_contas_criadas_logs"

    log_id           = db.Column(db.Integer,    primary_key=True, autoincrement=True)
    admin_usuario_id = db.Column(db.String(36), db.ForeignKey("usuarios.usuario_id"), nullable=False, index=True)
    novo_usuario_id  = db.Column(db.String(36), db.ForeignKey("usuarios.usuario_id"), nullable=False, index=True)
    novo_usuario_role = db.Column(db.String(40), nullable=False)
    ip_origem        = db.Column(db.String(64),  nullable=True)
    ocorreu_em_data  = db.Column(db.Date, nullable=False, default=utcnow_date, index=True)
    ocorreu_em_hora  = db.Column(db.Time, nullable=False, default=utcnow_time)


class Asteroide(db.Model):
    __tablename__ = "asteroides"

    asteroide_id      = db.Column(db.Integer,    primary_key=True, autoincrement=True)
    codigo            = db.Column(db.String(40),  unique=True, nullable=False)
    nome              = db.Column(db.String(120), nullable=False)
    classe_espectral  = db.Column(db.String(20),  nullable=True)
    diametro_km       = db.Column(db.Float,       nullable=True)
    delta_v_kms       = db.Column(db.Float,       nullable=True)
    mineral_destaque  = db.Column(db.String(80),  nullable=True)
    valor_estimado_usd = db.Column(db.Float,      nullable=True)
    score_viabilidade = db.Column(db.Float,       nullable=False, default=0)
    atualizado_em_data = db.Column(db.Date, nullable=False, default=utcnow_date, onupdate=utcnow_date)
    atualizado_em_hora = db.Column(db.Time, nullable=False, default=utcnow_time, onupdate=utcnow_time)


class AnaliseViabilidade(db.Model):
    __tablename__ = "analises_viabilidade"

    analise_id              = db.Column(db.Integer, primary_key=True, autoincrement=True)
    asteroide_id            = db.Column(db.Integer, db.ForeignKey("asteroides.asteroide_id"), nullable=False, index=True)
    versao_modelo           = db.Column(db.String(80),   nullable=False)
    custo_extracao_usd      = db.Column(db.Float,        nullable=False)
    custo_transporte_usd    = db.Column(db.Float,        nullable=False)
    custo_processamento_usd = db.Column(db.Float,        nullable=False)
    receita_estimada_usd    = db.Column(db.Float,        nullable=False)
    roi_percentual          = db.Column(db.Float,        nullable=True)
    score_viabilidade       = db.Column(db.Float,        nullable=False)
    classificacao           = db.Column(db.String(20),   nullable=False)
    gerado_em_data          = db.Column(db.Date, nullable=False, default=utcnow_date, index=True)
    gerado_em_hora          = db.Column(db.Time, nullable=False, default=utcnow_time)
    gerado_por_usuario_id   = db.Column(db.String(36), db.ForeignKey("usuarios.usuario_id"), nullable=True)

    asteroide = db.relationship("Asteroide", lazy="joined")


class RecomendacaoIA(db.Model):
    __tablename__ = "recomendacoes_ia"

    recomendacao_id     = db.Column(db.Integer, primary_key=True, autoincrement=True)
    analise_id          = db.Column(db.Integer, db.ForeignKey("analises_viabilidade.analise_id"), nullable=False, index=True)
    modelo_ia           = db.Column(db.String(80),  nullable=False)
    resumo_recomendacao = db.Column(db.String(500), nullable=False)
    plano_acao          = db.Column(db.Text,        nullable=True)
    confianca           = db.Column(db.Float,       nullable=True)
    criado_em_data      = db.Column(db.Date, nullable=False, default=utcnow_date, index=True)
    criado_em_hora      = db.Column(db.Time, nullable=False, default=utcnow_time)

    analise = db.relationship("AnaliseViabilidade", lazy="joined")
