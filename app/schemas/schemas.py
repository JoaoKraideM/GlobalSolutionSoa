from __future__ import annotations

import re


EMAIL_REGEX = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")

# CORRECAO: regex original rejeitava nomes com letras acentuadas (João, André, etc.)
# O range À-ÿ (U+00C0–U+00FF) cobre todos os caracteres latinos com diacríticos
# comuns no português brasileiro, sem precisar listar cada letra individualmente.
NAME_REGEX = re.compile(r"^[A-Za-zÀ-ÿ\s'\-]{3,140}$")


def validar_email(email: str) -> str:
    valor = (email or "").strip().lower()
    if not EMAIL_REGEX.match(valor):
        raise ValueError("E-mail invalido.")
    if len(valor) > 255:
        raise ValueError("E-mail muito longo.")
    return valor


def validar_nome(nome: str) -> str:
    valor = (nome or "").strip()
    if not NAME_REGEX.match(valor):
        # Mensagem atualizada para refletir que acentos agora são aceitos
        raise ValueError("Nome invalido. Use apenas letras (incluindo acentuadas), espacos, apostrofo e hifen.")
    return valor


def validar_senha(senha: str) -> str:
    valor = senha or ""
    if len(valor) < 8:
        raise ValueError("A senha deve ter no minimo 8 caracteres.")
    if not re.search(r"[A-Z]", valor):
        raise ValueError("A senha deve ter pelo menos 1 letra maiuscula.")
    if not re.search(r"[a-z]", valor):
        raise ValueError("A senha deve ter pelo menos 1 letra minuscula.")
    if not re.search(r"[0-9]", valor):
        raise ValueError("A senha deve ter pelo menos 1 numero.")
    if not re.search(r"[!@#$%^&*()_+\-=\[\]{};':\"\\|,.<>/?]", valor):
        raise ValueError("A senha deve ter pelo menos 1 caractere especial.")
    return valor


def validar_role(role: str) -> str:
    valor = (role or "ANALISTA").strip().upper()
    if valor not in {"ADMIN", "ANALISTA"}:
        raise ValueError("Role invalida.")
    return valor

# REMOCAO: contem_padrao_suspeito() e SQLI_REGEX foram removidos.
#
# Motivo: a função nunca era chamada em nenhum ponto do código (código morto),
# e a abordagem de detectar SQL injection via regex é fundamentalmente frágil
# — basta usar encoding, comentários SQL ou fragmentação de palavras para
# contorná-la.
#
# A proteção real contra SQL injection já está correta e ativa:
# o SQLAlchemy usa queries parametrizadas (prepared statements) em todas as
# operações de banco, o que é a defesa canônica e recomendada pela OWASP.
# O frontend ainda faz uma checagem client-side em forms.js como
# defesa-em-profundidade para UX, o que é aceitável manter lá.
