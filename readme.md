# Plataforma de Mineração Espacial — API REST

Solução desenvolvida para o **Global Solution 2026 — ODS 9 (Indústria, Inovação e Infraestrutura)** da FIAP, turma **3ESPY**.

| RM | Nome |
|----|------|
| RM556439 | Douglas dos Santos Melo |
| RM557959 | Henrique Sanches |
| RM563166 | João Pedro Kraide Máximo |
| RM556332 | Matheus Marcelino Dantas da Silva |
| RM556506 | Nicolas Caciolato Reis |

---

## Sumário

1. [Problema e Objetivo](#1-problema-e-objetivo)
2. [Alinhamento com o ODS 9](#2-alinhamento-com-o-ods-9)
3. [Stack Tecnológica](#3-stack-tecnológica)
4. [Arquitetura da Solução](#4-arquitetura-da-solução)
5. [Organização do Projeto](#5-organização-do-projeto)
6. [Endpoints da API REST](#6-endpoints-da-api-rest)
7. [Contratos Detalhados dos Endpoints](#7-contratos-detalhados-dos-endpoints)
8. [Banco de Dados](#8-banco-de-dados)
9. [Segurança Implementada](#9-segurança-implementada)
10. [Configuração Local](#10-configuração-local)
11. [Execução com Docker](#11-execução-com-docker)
12. [Como Testar a API](#12-como-testar-a-api)
13. [Perguntas Discursivas](#13-perguntas-discursivas)

---

## 1. Problema e Objetivo

A exploração de asteroides é uma das fronteiras da nova economia espacial. Identificar quais asteroides têm potencial real de mineração — considerando custo de extração, transporte, tipo de mineral e delta-v necessário — exige integração de dados científicos, análise econômica e tomada de decisão automatizada.

**O problema:** não existe uma plataforma centralizada que integre dados de asteroides, execute análises de viabilidade econômica e entregue recomendações de missão de forma padronizada e acessível via API.

**O objetivo:** construir uma plataforma REST que permita cadastrar asteroides, registrar análises de viabilidade e consultar recomendações geradas por modelos de IA — tudo organizado em camadas, com autenticação JWT, documentação Swagger e interface web interna para operadores.

---

## 2. Alinhamento com o ODS 9

O ODS 9 trata de **Indústria, Inovação e Infraestrutura**. Este projeto se alinha ao objetivo de três formas:

- **Inovação:** aplica IA e análise de dados a um problema de fronteira tecnológica (mineração espacial), antecipando infraestrutura para uma indústria emergente.
- **Infraestrutura digital:** entrega uma API REST com arquitetura em camadas, documentação OpenAPI e contêinerização Docker — infraestrutura pronta para escalar.
- **Sistemas conectados:** a arquitetura prevê um barramento de eventos (`event_bus.py`) que permite integração futura com sistemas externos de telemetria e missão.

---

## 3. Stack Tecnológica

| Tecnologia | Papel |
|---|---|
| Python 3.12 / Flask 3.1 | Framework web e API REST |
| SQLAlchemy 3.1 (ORM) | Mapeamento objeto-relacional |
| MySQL 8 | Banco de dados relacional |
| PyJWT | Autenticação stateless via JWT |
| passlib\[bcrypt\] | Hashing seguro de senhas |
| Flasgger / Swagger UI | Documentação OpenAPI automática |
| Docker + docker-compose | Contêinerização e orquestração |
| Gunicorn | Servidor WSGI de produção |

---

## 4. Arquitetura da Solução

O projeto segue a separação em **quatro camadas**, onde cada camada tem uma única responsabilidade e só se comunica com a camada imediatamente abaixo:

```
Requisição HTTP
      │
      ▼
┌─────────────────────────────────────────────────────────────┐
│  Controller  (app/api/)                                     │
│  Recebe a requisição HTTP, valida o formato do payload,     │
│  chama o serviço e serializa a resposta JSON.               │
│  Não conhece SQL. Não conhece regras de negócio.            │
├─────────────────────────────────────────────────────────────┤
│  Service  (app/services/)                                   │
│  Orquestra regras de negócio. Decide o que fazer com        │
│  os dados. Não conhece HTTP nem SQL diretamente.            │
├─────────────────────────────────────────────────────────────┤
│  Repository  (app/repositories/)                            │
│  Abstrai todo acesso ao banco de dados. Expõe métodos       │
│  semânticos (buscar_por_codigo, salvar, deletar).           │
│  O serviço não sabe que existe SQLAlchemy.                  │
├─────────────────────────────────────────────────────────────┤
│  Model / Entity  (app/models/modelos.py)                    │
│  Mapeamento objeto-relacional. Representa as tabelas        │
│  como classes Python via SQLAlchemy.                        │
└─────────────────────────────────────────────────────────────┘
      │
      ▼
   MySQL 8
```

**Justificativa da arquitetura:** a separação em camadas foi escolhida por ser o padrão da disciplina SOA e por oferecer benefícios práticos claros: o Controller pode ser trocado (ex: de Flask para FastAPI) sem mexer na lógica de negócio; o Repository pode mudar de MySQL para PostgreSQL sem afetar os serviços; e os Services são facilmente testáveis com injeção de dependência — basta passar um repositório mock no construtor.

O fluxo básico de uma requisição é:

```
Cliente → [Bearer Token] → Controller → DTO de entrada →
Service (valida, aplica regras) → Repository (CRUD no banco) →
Model → Banco → ← Model ← DTO de saída ← JSON ← Cliente
```

---

## 5. Organização do Projeto

```
GlobalSolutionSoa/
├── app/
│   ├── api/
│   │   ├── v1/                     ← API REST pública
│   │   │   ├── auth_token.py       POST /api/v1/auth/token
│   │   │   ├── asteroides.py       CRUD /api/v1/asteroides
│   │   │   ├── analises.py         CRUD /api/v1/analises
│   │   │   └── recomendacoes.py    GET  /api/v1/recomendacoes
│   │   ├── auth.py                 Interface web — autenticação
│   │   ├── main.py                 Interface web — dashboard e importação CSV/XLSX
│   │   ├── admin.py                Interface web — logs admin
│   │   └── deps.py                 Decorators: login_required, api_token_required
│   ├── repositories/               ← Camada de acesso a dados
│   │   ├── asteroide_repository.py
│   │   ├── analise_repository.py
│   │   └── recomendacao_repository.py
│   ├── schemas/
│   │   ├── dtos.py                 ← DTOs de entrada e saída tipados
│   │   └── schemas.py              Validações de campos (email, senha, nome)
│   ├── services/
│   │   ├── asteroide_service.py    ← Regras de negócio de asteroides
│   │   ├── analise_service.py      ← Regras de negócio de análises
│   │   ├── auth_service.py         Autenticação, criação de usuários, alteração de senha
│   │   ├── auditoria_service.py    Logs de segurança e auditoria
│   │   └── event_bus.py            Barramento de eventos de domínio (extensível)
│   ├── models/
│   │   └── modelos.py              Entidades SQLAlchemy (todas as tabelas)
│   ├── core/
│   │   ├── config.py               Configurações da aplicação via .env
│   │   ├── middleware.py           CSRF, headers de segurança (CSP, X-Frame-Options)
│   │   └── security.py             JWT (criar/verificar), bcrypt
│   ├── db/
│   │   ├── init_db.py              Seed inicial do banco (roles, admin, asteroides)
│   │   ├── schema.sql              DDL completo + seeds de dados
│   │   └── session.py              Instância do SQLAlchemy
│   ├── static/                     CSS e JS da interface web
│   └── templates/                  Templates HTML (Jinja2)
├── .env.example                    ← Modelo de configuração (copie para .env)
├── .gitignore
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── run.py
```

---

## 6. Endpoints da API REST

Todos os endpoints (exceto `POST /api/v1/auth/token`) exigem **Bearer Token** no header `Authorization`.

### Autenticação

| Método | Endpoint | Descrição | Auth |
|--------|----------|-----------|------|
| POST | `/api/v1/auth/token` | Autentica e retorna JWT | Não |

### Asteroides

| Método | Endpoint | Descrição | Status |
|--------|----------|-----------|--------|
| GET | `/api/v1/asteroides` | Lista paginada | 200 |
| GET | `/api/v1/asteroides/<id>` | Busca por ID | 200 / 404 |
| POST | `/api/v1/asteroides` | Cria novo asteroide | 201 / 400 |
| PUT | `/api/v1/asteroides/<id>` | Atualiza completamente | 200 / 400 / 404 |
| DELETE | `/api/v1/asteroides/<id>` | Remove | 204 / 404 |

### Análises de Viabilidade

| Método | Endpoint | Descrição | Status |
|--------|----------|-----------|--------|
| GET | `/api/v1/analises` | Lista paginada | 200 |
| GET | `/api/v1/analises/<id>` | Busca por ID | 200 / 404 |
| POST | `/api/v1/analises` | Cria nova análise | 201 / 400 / 404 |
| PUT | `/api/v1/analises/<id>` | Atualiza completamente | 200 / 400 / 404 |
| DELETE | `/api/v1/analises/<id>` | Remove | 204 / 404 |

### Recomendações IA

| Método | Endpoint | Descrição | Status |
|--------|----------|-----------|--------|
| GET | `/api/v1/recomendacoes` | Lista paginada | 200 |
| GET | `/api/v1/recomendacoes/<id>` | Busca por ID | 200 / 404 |

### Formato padrão de resposta

Todas as respostas seguem o mesmo envelope JSON:

```json
// Sucesso — item único
{ "status": "success", "data": { ... } }

// Sucesso — lista
{ "status": "success", "data": [ ... ], "total": 5, "pagina": { "limite": 100, "offset": 0 } }

// Erro
{ "status": "error", "message": "Descrição do erro.", "code": 404 }
```

### Documentação Swagger

Após subir a aplicação, acesse: **http://localhost:5000/api/v1/docs**

---

## 7. Contratos Detalhados dos Endpoints

### `POST /api/v1/auth/token`

Autentica o usuário e retorna um Bearer Token JWT para uso nos demais endpoints.

**Request body:**
```json
{
  "email": "admin@mineracao.local",
  "senha": "Admin@123456"
}
```

**Resposta `200 OK`:**
```json
{
  "status": "success",
  "data": {
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "email": "admin@mineracao.local",
    "role": "ADMIN"
  }
}
```

**Erros esperados:**
- `400 Bad Request` — body JSON ausente ou malformado
- `401 Unauthorized` — credenciais inválidas ou IP temporariamente bloqueado por tentativas excessivas

**Efeitos colaterais:** registra tentativa de login em `auth_tentativas_login`; em caso de sucesso, atualiza `ultimo_login_em_data` e `ultimo_login_em_hora` do usuário.

---

### `GET /api/v1/asteroides`

Lista asteroides com paginação por `limite` e `offset` (query params).

**Query params opcionais:**

| Parâmetro | Tipo | Padrão | Máximo | Descrição |
|-----------|------|--------|--------|-----------|
| `limite` | integer | 100 | 500 | Máximo de registros retornados |
| `offset` | integer | 0 | — | Posição de início |

**Resposta `200 OK`:**
```json
{
  "status": "success",
  "data": [
    {
      "asteroide_id": 1,
      "codigo": "2025-QA1",
      "nome": "Atena Prime",
      "classe_espectral": "M",
      "diametro_km": 1.34,
      "delta_v_kms": 4.8,
      "mineral_destaque": "Platina",
      "valor_estimado_usd": 4500000000.0,
      "score_viabilidade": 87.2,
      "atualizado_em_data": "2025-06-03",
      "atualizado_em_hora": "14:32:07"
    }
  ],
  "total": 5,
  "pagina": { "limite": 100, "offset": 0 }
}
```

---

### `GET /api/v1/asteroides/<id>`

Retorna um único asteroide pelo `asteroide_id`.

**Resposta `200 OK`:** mesmo objeto do item do array acima.

**Erros:**
- `404 Not Found` — asteroide não encontrado para o ID informado

---

### `POST /api/v1/asteroides`

Cadastra um novo asteroide.

**Request body:**
```json
{
  "codigo": "2026-AB1",
  "nome": "Nebula Core",
  "classe_espectral": "M",
  "diametro_km": 2.1,
  "delta_v_kms": 5.0,
  "mineral_destaque": "Ferro",
  "valor_estimado_usd": 800000000,
  "score_viabilidade": 72.0
}
```

**Campos:**

| Campo | Tipo | Obrigatório | Validação |
|-------|------|-------------|-----------|
| `codigo` | string | Sim | Único no banco; convertido para maiúsculas |
| `nome` | string | Sim | Não pode ser vazio |
| `classe_espectral` | string | Não | — |
| `diametro_km` | number | Não | Não pode ser negativo |
| `delta_v_kms` | number | Não | Não pode ser negativo |
| `mineral_destaque` | string | Não | — |
| `valor_estimado_usd` | number | Não | — |
| `score_viabilidade` | number | Não (padrão: 0) | Entre 0 e 100 |

**Resposta `201 Created`:**
```json
{
  "status": "success",
  "data": { /* objeto completo do asteroide criado */ }
}
```

**Erros:**
- `400 Bad Request` — campos obrigatórios ausentes, `score_viabilidade` fora de 0–100, `codigo` duplicado, ou `diametro_km`/`delta_v_kms` negativos

---

### `PUT /api/v1/asteroides/<id>`

Atualiza completamente um asteroide. Mesmos campos e validações do `POST`. Retorna o objeto atualizado com status `200`.

**Erros:**
- `400 Bad Request` — dados inválidos
- `404 Not Found` — asteroide não encontrado

---

### `DELETE /api/v1/asteroides/<id>`

Remove um asteroide. Retorna `204 No Content` (sem corpo).

**Erros:**
- `404 Not Found` — asteroide não encontrado

---

### `GET /api/v1/analises`

Lista análises de viabilidade com paginação. Mesmos query params que asteroides.

**Resposta `200 OK`:**
```json
{
  "status": "success",
  "data": [
    {
      "analise_id": 1,
      "asteroide_id": 1,
      "versao_modelo": "v2.4",
      "custo_extracao_usd": 950000000.0,
      "custo_transporte_usd": 320000000.0,
      "custo_processamento_usd": 140000000.0,
      "receita_estimada_usd": 4500000000.0,
      "roi_percentual": 216.5,
      "score_viabilidade": 87.2,
      "classificacao": "ALTA",
      "gerado_em_data": "2025-06-03",
      "gerado_em_hora": "14:32:07",
      "gerado_por_usuario_id": "uuid-do-usuario"
    }
  ],
  "total": 2,
  "pagina": { "limite": 100, "offset": 0 }
}
```

---

### `POST /api/v1/analises`

Cria uma nova análise de viabilidade para um asteroide existente.

**Request body:**
```json
{
  "asteroide_id": 1,
  "versao_modelo": "v2.5",
  "custo_extracao_usd": 950000000,
  "custo_transporte_usd": 320000000,
  "custo_processamento_usd": 140000000,
  "receita_estimada_usd": 4500000000,
  "roi_percentual": 216.5,
  "score_viabilidade": 87.2,
  "classificacao": "ALTA"
}
```

**Campos:**

| Campo | Tipo | Obrigatório | Validação |
|-------|------|-------------|-----------|
| `asteroide_id` | integer | Sim | Deve existir no banco |
| `versao_modelo` | string | Sim | Não pode ser vazio |
| `custo_extracao_usd` | number | Sim | Não pode ser negativo |
| `custo_transporte_usd` | number | Sim | Não pode ser negativo |
| `custo_processamento_usd` | number | Sim | Não pode ser negativo |
| `receita_estimada_usd` | number | Sim | Não pode ser negativo |
| `roi_percentual` | number | Não | Calculado automaticamente se omitido |
| `score_viabilidade` | number | Sim | Entre 0 e 100 |
| `classificacao` | string | Sim | Apenas `ALTA`, `MEDIA` ou `BAIXA` |

**Resposta `201 Created`:** objeto completo da análise criada.

**Efeitos colaterais:** registra o `usuario_id` do token como `gerado_por_usuario_id`.

**Erros:**
- `400 Bad Request` — validações de campo falharam
- `404 Not Found` — `asteroide_id` não encontrado no banco

---

### `PUT /api/v1/analises/<id>`

Atualiza completamente uma análise. Mesmos campos e validações do `POST`. Retorna o objeto atualizado.

---

### `DELETE /api/v1/analises/<id>`

Remove uma análise. Retorna `204 No Content`.

---

### `GET /api/v1/recomendacoes`

Lista recomendações de IA com paginação.

**Resposta `200 OK`:**
```json
{
  "status": "success",
  "data": [
    {
      "recomendacao_id": 1,
      "analise_id": 1,
      "modelo_ia": "astro-rank-gpt",
      "resumo_recomendacao": "Iniciar missão de validação orbital com foco em extração de metais raros.",
      "plano_acao": "Fase 1: sonda de prospecção. Fase 2: módulo de extração automatizada.",
      "confianca": 91.3,
      "criado_em_data": "2025-06-03",
      "criado_em_hora": "14:32:07"
    }
  ],
  "total": 5,
  "pagina": { "limite": 100, "offset": 0 }
}
```

---

### `GET /api/v1/recomendacoes/<id>`

Retorna uma única recomendação pelo ID.

**Erros:**
- `404 Not Found` — recomendação não encontrada

---

## 8. Banco de Dados

O banco é inicializado automaticamente no primeiro boot com tabelas e dados seed.

**Tabelas de domínio:**

| Tabela | Descrição |
|--------|-----------|
| `asteroides` | Dados científicos e econômicos dos asteroides |
| `analises_viabilidade` | Análises de custo, receita, ROI e score por asteroide |
| `recomendacoes_ia` | Recomendações de missão geradas por modelo de IA |

**Tabelas de segurança e auditoria:**

| Tabela | Descrição |
|--------|-----------|
| `usuarios` | Contas de acesso (admin e analista) |
| `roles` | Perfis de acesso (`ADMIN`, `ANALISTA`) |
| `usuario_roles` | Associação N:N usuário ↔ role |
| `senha_historico` | Últimas N senhas (impede reutilização) |
| `auth_tentativas_login` | Log de tentativas de login por IP e email |
| `dashboard_arquivo_logs` | Log de importações e exportações CSV/XLSX |
| `admin_contas_criadas_logs` | Log de criação de contas por administradores |

**Nota de design — campos de data e hora separados:**
Cada timestamp foi dividido em dois campos: `_data DATE` e `_hora TIME`. Isso permite queries de filtro por intervalo de datas sem usar funções como `DATE()` sobre um `DATETIME`, o que bloquearia o uso de índices no MySQL.

```sql
-- Exemplo eficiente com índice:
WHERE ocorreu_em_data BETWEEN '2025-06-01' AND '2025-06-30'
AND ocorreu_em_hora BETWEEN '08:00:00' AND '18:00:00'
```

---

## 9. Segurança Implementada

| Controle | Implementação |
|----------|--------------|
| **Autenticação** | JWT Bearer Token assinado com HS256; expiração configurável |
| **Autorização** | RBAC com roles `ADMIN` e `ANALISTA` via decorator `@login_required` e `@api_token_required` |
| **Senhas** | Hashing bcrypt; histórico das últimas N senhas para impedir reutilização |
| **Brute force** | Rate limiting por IP — bloqueia após N falhas em janela de tempo configurável |
| **CSRF** | Tokens em todos os formulários da interface web |
| **SQL Injection** | Queries ORM parametrizadas via SQLAlchemy (proteção OWASP A03) |
| **XSS** | CSP (`Content-Security-Policy`) sem `unsafe-inline` em `script-src` |
| **Headers HTTP** | `X-Frame-Options`, `X-Content-Type-Options`, `Referrer-Policy`, `Permissions-Policy` |
| **Correlação** | `correlation_id` por requisição para rastreabilidade em logs |

---

## 10. Configuração Local

### Pré-requisitos

- Python 3.12+
- MySQL 8 rodando localmente (ou usar Docker — veja seção 11)

### Passo a passo

**1. Crie e ative o ambiente virtual**

Windows (PowerShell):
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

Linux / macOS:
```bash
python -m venv .venv
source .venv/bin/activate
```

**2. Instale as dependências**
```bash
pip install -r requirements.txt
```

**3. Configure o `.env`**

Copie o arquivo de exemplo e edite com suas credenciais:
```bash
cp .env.example .env
```

Valores mínimos obrigatórios no `.env`:
```env
SECRET_KEY=troque-por-uma-chave-forte-e-aleatoria
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=sua_senha_mysql
DB_NAME=mineracao_espacial_viabilidade
DEFAULT_ADMIN_EMAIL=admin@mineracao.local
DEFAULT_ADMIN_PASSWORD=Admin@123456
```

**4. Crie o banco de dados**
```sql
CREATE DATABASE mineracao_espacial_viabilidade
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;
```

**5. Inicie a aplicação**
```bash
python run.py
```

A aplicação sobe em **http://localhost:5000**.
O banco é inicializado automaticamente na primeira execução (tabelas + seed de dados).

---

## 11. Execução com Docker

```bash
docker compose up --build
```

Serviços iniciados:

- `mineracao_espacial_viabilidade_web` — aplicação Flask na porta **5000**
- `mineracao_espacial_viabilidade_db` — MySQL 8 (porta não exposta externamente)

O banco é inicializado automaticamente via `app/db/schema.sql`.

**Credenciais padrão após o primeiro boot:**

| Campo | Valor |
|-------|-------|
| E-mail | `admin@mineracao.local` |
| Senha | `Admin@123456` |

> Altere as credenciais no `.env` antes de qualquer deploy.

---

## 12. Como Testar a API

### Via Swagger UI (recomendado)

1. Suba a aplicação
2. Acesse `http://localhost:5000/api/v1/docs`
3. Expanda `POST /api/v1/auth/token` → clique em **Try it out**
4. Envie: `{ "email": "admin@mineracao.local", "senha": "Admin@123456" }`
5. Copie o campo `token` da resposta
6. Clique em **Authorize** (cadeado no topo) → insira `Bearer SEU_TOKEN_AQUI`
7. Todos os endpoints ficam desbloqueados para teste

### Via curl

```bash
# 1. Obter token e salvar na variável TOKEN
TOKEN=$(curl -s -X POST http://localhost:5000/api/v1/auth/token \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@mineracao.local","senha":"Admin@123456"}' \
  | python -c "import sys,json; print(json.load(sys.stdin)['data']['token'])")

# 2. Listar asteroides
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:5000/api/v1/asteroides

# 3. Criar asteroide
curl -X POST http://localhost:5000/api/v1/asteroides \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "codigo": "2026-ZZ9",
    "nome": "Test Asteroid",
    "classe_espectral": "S",
    "diametro_km": 1.2,
    "delta_v_kms": 4.5,
    "mineral_destaque": "Niquel",
    "valor_estimado_usd": 500000000,
    "score_viabilidade": 75.0
  }'

# 4. Buscar asteroide por ID
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:5000/api/v1/asteroides/1

# 5. Atualizar asteroide (substitua <id>)
curl -X PUT http://localhost:5000/api/v1/asteroides/<id> \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "codigo": "2026-ZZ9",
    "nome": "Test Asteroid Updated",
    "score_viabilidade": 80.0
  }'

# 6. Criar análise de viabilidade
curl -X POST http://localhost:5000/api/v1/analises \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "asteroide_id": 1,
    "versao_modelo": "v2.5",
    "custo_extracao_usd": 950000000,
    "custo_transporte_usd": 320000000,
    "custo_processamento_usd": 140000000,
    "receita_estimada_usd": 4500000000,
    "score_viabilidade": 87.2,
    "classificacao": "ALTA"
  }'

# 7. Listar recomendações de IA
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:5000/api/v1/recomendacoes

# 8. Deletar asteroide
curl -X DELETE http://localhost:5000/api/v1/asteroides/<id> \
  -H "Authorization: Bearer $TOKEN"
```

---

## 13. Perguntas Discursivas

### 1. Quais seriam os principais desafios caso o sistema precisasse atender milhares de usuários simultaneamente?

O maior desafio seria a **escalabilidade do banco de dados**. O MySQL em instância única tem limites de conexões simultâneas; com alta concorrência, seria necessário configurar um pool de conexões robusto (o SQLAlchemy já tem um pool embutido, mas os limites precisariam ser ajustados) e eventualmente adicionar *read replicas* para distribuir carga de leitura — que representa a maioria das operações de listagem e busca.

Na **camada de aplicação**, o Gunicorn com workers síncronos processa uma requisição por vez por worker. A solução seria aumentar o número de workers, adotar workers assíncronos (Gevent ou Uvicorn+async) ou distribuir a carga entre múltiplas instâncias atrás de um load balancer (Nginx ou AWS ALB). O JWT ajuda nesse cenário: como a autenticação é *stateless*, qualquer instância valida qualquer token sem precisar consultar um cache central — ao contrário de sessões de servidor, que exigiriam Redis compartilhado.

Haveria também desafios de **contenção em banco** nas operações de escrita (criação de análises, registro de tentativas de login). Tabelas como `auth_tentativas_login` crescem rapidamente em carga alta e precisariam de política de particionamento por data ou archiving periódico.

### 2. Quais pontos da arquitetura poderiam ser melhorados futuramente?

A **camada de Repository** poderia ser aprimorada com paginação por *cursor* em vez de `OFFSET/LIMIT` — mais eficiente em tabelas grandes, pois `OFFSET` força o banco a varrer e descartar registros anteriores. Com cursor, a próxima página parte do último ID retornado, usando o índice primário diretamente.

Os **DTOs** poderiam migrar de `dataclasses` para **Pydantic**, ganhando validação automática de tipos, coerção de dados, mensagens de erro padronizadas e geração automática de *JSON Schema* para o Swagger — eliminando a redundância atual de definir validações manualmente em `validar()` e também no Flasgger.

O **tratamento de erros** poderia ser centralizado em uma hierarquia de exceções de domínio (`AsteroideDuplicadoError`, `AnaliseClassificacaoInvalidaError`, etc.) em vez de `ValueError` genérico. Isso tornaria os controllers mais expressivos, o Swagger mais preciso nos exemplos de erro e facilitaria o monitoramento por tipo de falha.

Por fim, o `event_bus.py` já existe como esboço, mas ainda não publica eventos reais. Conectá-lo a um broker leve (como Redis Pub/Sub) permitiria auditoria assíncrona e futuras integrações sem acoplar os serviços.

### 3. Como o sistema poderia evoluir para uma arquitetura distribuída?

O primeiro passo seria **extrair cada domínio** (Asteroides, Análises, Recomendações) em microsserviços independentes, cada um com seu próprio banco de dados. A comunicação síncrona entre eles usaria HTTP/gRPC; a assíncrona usaria um *message broker* como **Kafka** ou **RabbitMQ**.

O `event_bus.py` já é um esboço dessa direção: ele define a ideia de publicar eventos de domínio que outros serviços podem consumir. Em uma arquitetura distribuída real, esses eventos seriam publicados no broker e consumidos por workers independentes — desacoplando completamente os serviços e permitindo que cada um escale de forma independente.

Um **API Gateway** (Kong, AWS API Gateway) assumiria o papel de autenticação centralizada, eliminando a necessidade de cada microsserviço validar o JWT individualmente. O gateway também cuidaria de *rate limiting* global, roteamento de versões de API e observabilidade (métricas, tracing distribuído com OpenTelemetry).

A interface web interna (templates Flask) poderia ser separada em um frontend independente (React/Vue) consumindo a própria API REST — deixando o backend puramente como API, sem renderização de HTML, o que é o modelo mais adequado para uma arquitetura de microsserviços.
