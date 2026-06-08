CREATE DATABASE IF NOT EXISTS mineracao_espacial_viabilidade
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE mineracao_espacial_viabilidade;

-- ─────────────────────────────────────────────────────────────────────────────
-- NOTA DE DESIGN: colunas de data e hora separadas
-- ─────────────────────────────────────────────────────────────────────────────
-- Cada campo que seria DATETIME foi dividido em dois campos distintos:
--   _data  DATE  — facilita filtros por intervalo de datas (ex: todas as
--                  tentativas de login em 15/06/2025)
--   _hora  TIME  — facilita filtros por janela horária (ex: atividade
--                  suspeita após meia-noite)
-- Isso permite queries altamente eficientes como:
--   WHERE ocorreu_em_data BETWEEN '2025-06-01' AND '2025-06-30'
--   WHERE ocorreu_em_hora BETWEEN '00:00:00' AND '06:00:00'
-- sem precisar extrair partes de um DATETIME com funções como DATE() ou TIME(),
-- o que evitaria o uso de índices.
-- ─────────────────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS roles (
  role_id   INT AUTO_INCREMENT PRIMARY KEY,
  codigo    VARCHAR(40)  NOT NULL UNIQUE,
  nome      VARCHAR(80)  NOT NULL,
  descricao VARCHAR(200) NULL,
  criado_em_data DATE NOT NULL DEFAULT (CURDATE()),
  criado_em_hora TIME NOT NULL DEFAULT (CURTIME())
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS usuarios (
  usuario_id         CHAR(36)     PRIMARY KEY,
  nome_completo      VARCHAR(140) NOT NULL,
  email              VARCHAR(255) NOT NULL UNIQUE,
  senha_hash         VARCHAR(255) NOT NULL,
  ativo              TINYINT(1)   NOT NULL DEFAULT 1,
  -- Nullable: preenchido apenas no primeiro login com sucesso
  ultimo_login_em_data DATE NULL,
  ultimo_login_em_hora TIME NULL,
  criado_por         CHAR(36)     NULL,
  criado_em_data     DATE         NOT NULL DEFAULT (CURDATE()),
  criado_em_hora     TIME         NOT NULL DEFAULT (CURTIME()),
  -- Atualizado via ORM (onupdate) a cada UPDATE na linha
  atualizado_em_data DATE         NOT NULL DEFAULT (CURDATE()),
  atualizado_em_hora TIME         NOT NULL DEFAULT (CURTIME()),
  INDEX ix_usuarios_email (email),
  CONSTRAINT fk_usuarios_criado_por FOREIGN KEY (criado_por) REFERENCES usuarios(usuario_id)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS usuario_roles (
  usuario_id    CHAR(36) NOT NULL,
  role_id       INT      NOT NULL,
  atribuido_em_data DATE NOT NULL DEFAULT (CURDATE()),
  atribuido_em_hora TIME NOT NULL DEFAULT (CURTIME()),
  PRIMARY KEY (usuario_id, role_id),
  CONSTRAINT fk_usuario_roles_usuario FOREIGN KEY (usuario_id) REFERENCES usuarios(usuario_id),
  CONSTRAINT fk_usuario_roles_role    FOREIGN KEY (role_id)    REFERENCES roles(role_id)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS senha_historico (
  historico_id  BIGINT AUTO_INCREMENT PRIMARY KEY,
  usuario_id    CHAR(36)     NOT NULL,
  senha_hash    VARCHAR(255) NOT NULL,
  alterada_por  CHAR(36)     NULL,
  motivo        VARCHAR(120) NULL,
  alterada_em_data DATE NOT NULL DEFAULT (CURDATE()),
  alterada_em_hora TIME NOT NULL DEFAULT (CURTIME()),
  -- Índice composto: filtra histórico por usuário em um intervalo de datas
  INDEX ix_senha_historico_usuario_data (usuario_id, alterada_em_data, alterada_em_hora),
  CONSTRAINT fk_senha_historico_usuario     FOREIGN KEY (usuario_id)   REFERENCES usuarios(usuario_id),
  CONSTRAINT fk_senha_historico_alterada_por FOREIGN KEY (alterada_por) REFERENCES usuarios(usuario_id)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS auth_tentativas_login (
  tentativa_id   BIGINT AUTO_INCREMENT PRIMARY KEY,
  usuario_id     CHAR(36)     NULL,
  email_informado VARCHAR(255) NOT NULL,
  ip_origem      VARCHAR(64)  NOT NULL,
  user_agent     VARCHAR(300) NULL,
  sucesso        TINYINT(1)   NOT NULL DEFAULT 0,
  motivo_falha   VARCHAR(120) NULL,
  ocorreu_em_data DATE        NOT NULL DEFAULT (CURDATE()),
  ocorreu_em_hora TIME        NOT NULL DEFAULT (CURTIME()),
  -- Índice por IP + data: detecta brute-force em dias específicos
  INDEX ix_auth_tentativas_ip_data   (ip_origem, ocorreu_em_data, ocorreu_em_hora),
  -- Índice por email + data: rastreia ataques direcionados a um e-mail
  INDEX ix_auth_tentativas_email_data (email_informado, ocorreu_em_data),
  CONSTRAINT fk_auth_tentativas_login_usuario FOREIGN KEY (usuario_id) REFERENCES usuarios(usuario_id)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS dashboard_arquivo_logs (
  log_arquivo_id  BIGINT AUTO_INCREMENT PRIMARY KEY,
  usuario_id      CHAR(36)     NOT NULL,
  operacao        VARCHAR(20)  NOT NULL,
  formato         VARCHAR(10)  NOT NULL,
  nome_arquivo    VARCHAR(180) NULL,
  total_registros INT          NULL,
  status          VARCHAR(20)  NOT NULL DEFAULT 'SUCESSO',
  ip_origem       VARCHAR(64)  NULL,
  ocorreu_em_data DATE         NOT NULL DEFAULT (CURDATE()),
  ocorreu_em_hora TIME         NOT NULL DEFAULT (CURTIME()),
  INDEX ix_dashboard_arquivo_logs_data (ocorreu_em_data),
  CONSTRAINT fk_dashboard_arquivo_logs_usuario FOREIGN KEY (usuario_id) REFERENCES usuarios(usuario_id)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS admin_contas_criadas_logs (
  log_id           BIGINT AUTO_INCREMENT PRIMARY KEY,
  admin_usuario_id CHAR(36)    NOT NULL,
  novo_usuario_id  CHAR(36)    NOT NULL,
  novo_usuario_role VARCHAR(40) NOT NULL,
  ip_origem        VARCHAR(64) NULL,
  ocorreu_em_data  DATE        NOT NULL DEFAULT (CURDATE()),
  ocorreu_em_hora  TIME        NOT NULL DEFAULT (CURTIME()),
  INDEX ix_admin_contas_criadas_logs_data (ocorreu_em_data),
  CONSTRAINT fk_admin_contas_admin        FOREIGN KEY (admin_usuario_id) REFERENCES usuarios(usuario_id),
  CONSTRAINT fk_admin_contas_novo_usuario FOREIGN KEY (novo_usuario_id)  REFERENCES usuarios(usuario_id)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS asteroides (
  asteroide_id     INT AUTO_INCREMENT PRIMARY KEY,
  codigo           VARCHAR(40)    NOT NULL UNIQUE,
  nome             VARCHAR(120)   NOT NULL,
  classe_espectral VARCHAR(20)    NULL,
  diametro_km      DECIMAL(10,3)  NULL,
  delta_v_kms      DECIMAL(10,3)  NULL,
  mineral_destaque VARCHAR(80)    NULL,
  valor_estimado_usd DECIMAL(18,2) NULL,
  score_viabilidade  DECIMAL(5,2) NOT NULL DEFAULT 0,
  -- Atualizado automaticamente via ORM (onupdate) a cada PUT
  atualizado_em_data DATE         NOT NULL DEFAULT (CURDATE()),
  atualizado_em_hora TIME         NOT NULL DEFAULT (CURTIME())
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS analises_viabilidade (
  analise_id              BIGINT AUTO_INCREMENT PRIMARY KEY,
  asteroide_id            INT           NOT NULL,
  versao_modelo           VARCHAR(80)   NOT NULL,
  custo_extracao_usd      DECIMAL(18,2) NOT NULL,
  custo_transporte_usd    DECIMAL(18,2) NOT NULL,
  custo_processamento_usd DECIMAL(18,2) NOT NULL,
  receita_estimada_usd    DECIMAL(18,2) NOT NULL,
  roi_percentual          DECIMAL(8,2)  NULL,
  score_viabilidade       DECIMAL(5,2)  NOT NULL,
  classificacao           VARCHAR(20)   NOT NULL,
  gerado_em_data          DATE          NOT NULL DEFAULT (CURDATE()),
  gerado_em_hora          TIME          NOT NULL DEFAULT (CURTIME()),
  gerado_por_usuario_id   CHAR(36)      NULL,
  -- Índice composto: filtra análises de um asteroide em uma data específica
  INDEX ix_analises_asteroide_data (asteroide_id, gerado_em_data),
  CONSTRAINT fk_analises_viabilidade_asteroide FOREIGN KEY (asteroide_id)          REFERENCES asteroides(asteroide_id),
  CONSTRAINT fk_analises_viabilidade_usuario   FOREIGN KEY (gerado_por_usuario_id) REFERENCES usuarios(usuario_id)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS recomendacoes_ia (
  recomendacao_id      BIGINT AUTO_INCREMENT PRIMARY KEY,
  analise_id           BIGINT        NOT NULL,
  modelo_ia            VARCHAR(80)   NOT NULL,
  resumo_recomendacao  VARCHAR(500)  NOT NULL,
  plano_acao           TEXT          NULL,
  confianca            DECIMAL(5,2)  NULL,
  criado_em_data       DATE          NOT NULL DEFAULT (CURDATE()),
  criado_em_hora       TIME          NOT NULL DEFAULT (CURTIME()),
  INDEX ix_recomendacoes_ia_data (criado_em_data),
  CONSTRAINT fk_recomendacoes_ia_analise FOREIGN KEY (analise_id) REFERENCES analises_viabilidade(analise_id)
) ENGINE=InnoDB;

-- Seed: roles e asteroides (sem seed de datetime — o banco usa os defaults)
INSERT IGNORE INTO roles (codigo, nome, descricao)
VALUES
  ('ADMIN',    'Administrador', 'Acesso total ao ambiente interno'),
  ('ANALISTA', 'Analista',      'Acesso ao dashboard e recomendacoes');

INSERT INTO asteroides (codigo, nome, classe_espectral, diametro_km, delta_v_kms, mineral_destaque, valor_estimado_usd, score_viabilidade)
VALUES
  ('2025-QA1', 'Atena Prime', 'M', 1.340, 4.800, 'Platina',              4500000000.00, 87.20),
  ('2024-KR9', 'Helios Ridge', 'S', 0.920, 5.200, 'Niquel',               980000000.00, 74.60),
  ('2031-ZT3', 'Orion Dust',   'C', 1.880, 6.100, 'Agua para propelente', 1240000000.00, 69.40)
ON DUPLICATE KEY UPDATE
  nome              = VALUES(nome),
  classe_espectral  = VALUES(classe_espectral),
  diametro_km       = VALUES(diametro_km),
  delta_v_kms       = VALUES(delta_v_kms),
  mineral_destaque  = VALUES(mineral_destaque),
  valor_estimado_usd = VALUES(valor_estimado_usd),
  score_viabilidade = VALUES(score_viabilidade);

-- Seed: 2 asteroides adicionais
INSERT INTO asteroides (codigo, nome, classe_espectral, diametro_km, delta_v_kms, mineral_destaque, valor_estimado_usd, score_viabilidade)
VALUES
  ('2028-NX7', 'Vega Shard',   'M', 0.650, 3.900, 'Ferro-Niquel', 720000000.00,   61.80),
  ('2033-PL2', 'Kronos Belt',  'X', 2.100, 7.400, 'Iridio',       9800000000.00,  55.30)
ON DUPLICATE KEY UPDATE
  nome              = VALUES(nome),
  classe_espectral  = VALUES(classe_espectral),
  diametro_km       = VALUES(diametro_km),
  delta_v_kms       = VALUES(delta_v_kms),
  mineral_destaque  = VALUES(mineral_destaque),
  valor_estimado_usd = VALUES(valor_estimado_usd),
  score_viabilidade = VALUES(score_viabilidade);

-- Seed: análises de viabilidade (referencia asteroides pelos IDs esperados após seed acima)
INSERT IGNORE INTO analises_viabilidade
  (asteroide_id, versao_modelo, custo_extracao_usd, custo_transporte_usd, custo_processamento_usd, receita_estimada_usd, roi_percentual, score_viabilidade, classificacao)
SELECT a.asteroide_id, v.versao_modelo, v.custo_ext, v.custo_transp, v.custo_proc, v.receita, v.roi, v.score, v.classif
FROM asteroides a
JOIN (
  SELECT '2025-QA1' AS cod, 'v2.4' AS versao_modelo, 950000000 AS custo_ext, 320000000 AS custo_transp, 140000000 AS custo_proc, 4500000000 AS receita, 216.50 AS roi, 87.20 AS score, 'ALTA'  AS classif UNION ALL
  SELECT '2024-KR9',        'v2.4',                   410000000,             270000000,             115000000,            980000000,            23.20,        74.60,        'MEDIA' UNION ALL
  SELECT '2031-ZT3',        'v2.4',                   310000000,             205000000,              88000000,           1240000000,           148.90,        69.40,        'MEDIA' UNION ALL
  SELECT '2028-NX7',        'v2.4',                   180000000,             140000000,              62000000,            720000000,            88.60,        61.80,        'MEDIA' UNION ALL
  SELECT '2033-PL2',        'v2.4',                  2100000000,             890000000,             540000000,           9800000000,           181.40,        55.30,        'BAIXA'
) v ON a.codigo = v.cod
WHERE NOT EXISTS (
  SELECT 1 FROM analises_viabilidade av WHERE av.asteroide_id = a.asteroide_id
);

-- Seed: recomendações da IA
INSERT IGNORE INTO recomendacoes_ia (analise_id, modelo_ia, resumo_recomendacao, plano_acao, confianca)
SELECT av.analise_id, r.modelo_ia, r.resumo, r.plano, r.confianca
FROM analises_viabilidade av
JOIN asteroides a ON a.asteroide_id = av.asteroide_id
JOIN (
  SELECT '2025-QA1' AS cod, 'astro-rank-gpt' AS modelo_ia,
    'Iniciar missao de validacao orbital com foco em extracao de metais raros.' AS resumo,
    'Fase 1: sonda de prospeccao. Fase 2: modulo de extracao automatizada. Fase 3: retorno amostral.' AS plano,
    91.30 AS confianca
  UNION ALL
  SELECT '2024-KR9', 'astro-rank-gpt',
    'Priorizar estudo de rota para reduzir delta-v e renegociar janela de lancamento.',
    'Executar simulacao de transferencia Hohmann em 3 cenarios de janela.',
    82.70
  UNION ALL
  SELECT '2031-ZT3', 'astro-rank-gpt',
    'Alta concentracao de volateis util para producao de propelente in-situ (ISRU).',
    'Avaliar instalacao de reator de eletrolise na superficie para producao de H2/O2.',
    76.10
  UNION ALL
  SELECT '2028-NX7', 'astro-rank-gpt',
    'Candidato secundario para missao combinada com Atena Prime — delta-v favoravel.',
    'Incluir como ponto de escala na rota de retorno da missao principal.',
    68.40
  UNION ALL
  SELECT '2033-PL2', 'astro-rank-gpt',
    'Alto potencial economico mas delta-v elevado torna missao tecnicamente arriscada no horizonte atual.',
    'Aguardar maturidade de propulsao ionica de alta impulso especifico. Reavaliar em 2035.',
    54.90
) r ON a.codigo = r.cod
WHERE NOT EXISTS (
  SELECT 1 FROM recomendacoes_ia rec WHERE rec.analise_id = av.analise_id
);
