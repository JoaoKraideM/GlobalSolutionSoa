from __future__ import annotations

import os
from pathlib import Path
from urllib.parse import quote_plus

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parents[2]
load_dotenv(BASE_DIR / ".env")


def _build_database_uri() -> str:
    database_url = os.getenv("DATABASE_URL")
    if database_url:
        return database_url

    db_host = os.getenv("DB_HOST")
    if db_host:
        db_user = os.getenv("DB_USER", "root")
        db_password = quote_plus(os.getenv("DB_PASSWORD", ""))
        db_port = os.getenv("DB_PORT", "3306")
        db_name = os.getenv("DB_NAME", "mineracao_espacial_viabilidade")
        return f"mysql+pymysql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}?charset=utf8mb4"

    sqlite_path = BASE_DIR / "app.db"
    return f"sqlite:///{sqlite_path.as_posix()}"


class Config:
    APP_NAME = os.getenv("APP_NAME", "Plataforma Interna de Mineracao Espacial")
    SECRET_KEY = os.getenv("SECRET_KEY", "altere-esta-chave-em-producao")
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", SECRET_KEY)
    JWT_EXP_MINUTES = int(os.getenv("JWT_EXP_MINUTES", "60"))
    PASSWORD_HISTORY_DEPTH = int(os.getenv("PASSWORD_HISTORY_DEPTH", "5"))
    LOGIN_FAIL_LIMIT = int(os.getenv("LOGIN_FAIL_LIMIT", "5"))
    LOGIN_FAIL_WINDOW_MIN = int(os.getenv("LOGIN_FAIL_WINDOW_MIN", "15"))
    SQLALCHEMY_DATABASE_URI = _build_database_uri()
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = os.getenv("SESSION_COOKIE_SECURE", "false").lower() == "true"
    DEFAULT_ADMIN_NAME = os.getenv("DEFAULT_ADMIN_NAME", "Administrador Inicial")
    DEFAULT_ADMIN_EMAIL = os.getenv("DEFAULT_ADMIN_EMAIL", "admin@mineracao.local")
    DEFAULT_ADMIN_PASSWORD = os.getenv("DEFAULT_ADMIN_PASSWORD", "Admin@123456")
