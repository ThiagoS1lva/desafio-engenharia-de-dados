# Desafio Técnico de Engenharia de Dados — Retize

## Visão Geral

Solução completa de engenharia de dados para consolidar métricas de performance de redes sociais (Instagram e TikTok), desde a carga de arquivos CSV brutos até um modelo analítico capaz de responder perguntas de negócio sobre alcance, engajamento e sentimento de comentários.

O pipeline segue o fluxo **ELT**:

1. **Extract & Load** — `dlt` carrega 5 arquivos CSV em tabelas brutas no PostgreSQL
2. **Transform** — `dbt` organiza as transformações em camadas (staging → intermediate → marts)
3. **Query** — 5 consultas SQL respondem às perguntas de negócio

Todo o fluxo é orquestrado pelo **Apache Airflow**, executado via Docker Compose.

---

## Arquitetura

```
CSV files (5)
    │
    ▼
┌─────────────────┐
│  dlt pipeline   │  ← Python (pandas + dlt)
│  raw ingestion  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  PostgreSQL     │  raw.* tables
│  (Docker)       │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  dbt models     │  staging → intermediate → marts
│  (SQL + macros) │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  marts.* tables │  mart_content_performance
│  (PostgreSQL)   │  mart_content_with_sentiment
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  business       │  5 queries answering
│  queries (.sql) │  business questions
└─────────────────┘

Orchestration: Apache Airflow (DAG @once)
Containerization: Docker Compose (PostgreSQL + Airflow + Streamlit)
```

### Serviços

| Serviço | Porta | Descrição |
|---|---|---|
| PostgreSQL | `5432` | Banco de dados principal |
| Airflow UI | `8080` | Orquestração e monitoramento do pipeline |
| Streamlit | `8501` | Dashboard interativo com resultados |

### Camadas do Modelo de Dados

| Camada | Prefixo | Propósito |
|---|---|---|
| **Raw** | `raw.*` | Carga direta dos CSVs via dlt, sem transformação |
| **Staging** | `stg_*` | Limpeza, tipagem e padronização de cada fonte |
| **Intermediate** | `int_*` | Unificação de métricas entre Instagram e TikTok |
| **Marts** | `mart_*` | Tabelas analíticas finais prontas para consulta |

---

## Modelo de Dados

### Tabelas Principais

```
raw.instagram_media          ─┐
raw.instagram_media_insights ─┤──► stg_instagram__media ──► int_instagram__content_metrics ──┐
raw.instagram_comments       ─┘──► stg_instagram__comments ──► int_comments__unified ────────┤
                                                                                              ├──► int_content__unified ──► mart_content_performance
raw.tiktok_posts             ───────────────────────────► stg_tiktok__posts ──► int_tiktok__content_metrics ──┤
raw.tiktok_comments          ───────────────────────────► stg_tiktok__comments ───────────────────────────────┘
                                                                                              │
                                                                                              ├──► mart_content_with_sentiment
                                                                                              │
                                                                                              └──► mart_comment_sentiment
```

### Granularidade

| Tabela | Granularidade | Chave |
|---|---|---|
| `mart_content_performance` | 1 linha por conteúdo (post/story) | `platform + content_id` |
| `mart_content_with_sentiment` | 1 linha por conteúdo com métricas de sentimento agregadas | `platform + content_id` |
| `mart_comment_sentiment` | 1 linha por conta/plataforma com proporção de sentimentos | `account_name + platform` |

### Fórmula de Engajamento

A métrica `engagement_rate` é calculada como:

```
engagement_rate = (engagement_total / reach) * 100
```

O `engagement_total` é harmonizado entre plataformas:

- **Instagram**: usa `total_interactions` quando disponível; caso contrário, soma `likes + comments + shares + saved + profile_visits + follows`
- **TikTok**: soma `likes + comments + shares + favorites + profile_views + new_followers`

**Justificativa**: O Instagram fornece `total_interactions` como métrica consolidada pela API, então a priorizamos. Quando indisponível, usamos a soma manual das métricas disponíveis. Para o TikTok, não há equivalente direto, então somamos as interações individuais. O denominador é `reach` (alcance) por ser a métrica mais consistente entre ambas as plataformas para representar a audiência exposta.

---

## Perguntas de Negócio

| # | Pergunta | Arquivo |
|---|---|---|
| 1 | Melhor dia da semana para publicar por conta | `queries/pergunta_01.sql` |
| 2 | Plataforma com maior proporção de comentários negativos por conta | `queries/pergunta_02.sql` |
| 3 | Top 10 conteúdos com maior taxa de engajamento | `queries/pergunta_03.sql` |
| 4 | Top 3 conteúdos por conta com maior taxa de engajamento | `queries/pergunta_04.sql` |
| 5 | Melhor formato de conteúdo por conta | `queries/pergunta_05.sql` |

---

## Como Executar

### Pré-requisitos

- Docker e Docker Compose instalados
- PowerShell (Windows) ou terminal compatível

### Execução Completa (Recomendado)

Um único comando sobe todo o ambiente, executa o pipeline e monitora o resultado:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\run.ps1
```

O script automaticamente:
- Sobe o Docker Compose (com build na primeira vez)
- Valida containers e DAG
- Detecta runs finalizados e faz reset automático para permitir rerun
- Aguarda o pipeline executar e acompanha até `success` ou `failed`
- Imprime o status final de cada task
- Timeout padrão: **20 minutos**

### Execução Manual via Docker Compose

Se preferir, o pipeline executa automaticamente apenas com:

```bash
docker compose up -d
```

O DAG usa `schedule="@once"`, ou seja, dispara sozinho assim que o scheduler inicializa.

### Parâmetros do Script

```powershell
# Pular rebuild da imagem (ambiente já montado)
powershell -ExecutionPolicy Bypass -File .\scripts\run.ps1 -SkipBuild

# Ajustar timeout
powershell -ExecutionPolicy Bypass -File .\scripts\run.ps1 -TimeoutMinutes 30
```

### Rerun do Pipeline

O script detecta automaticamente runs finalizados e dispara um novo. Para rerun manual:

```bash
docker exec airflow_scheduler airflow dags delete retize_social_elt --yes
```

O scheduler recriará automaticamente um novo run.

### Airflow UI

- URL: `http://localhost:8080`
- Usuário: `airflow`
- Senha: `airflow`

### Dashboard Streamlit

Após o pipeline finalizar, acesse o dashboard interativo:

- URL: `http://localhost:8501`
- 5 páginas, uma para cada pergunta de negócio
- Tabelas com resultados e gráficos interativos (Plotly)
- Light mode, design limpo e responsivo

---

## Execução Passo a Passo (Sem Airflow)

Se quiser executar cada etapa manualmente:

### 1. Subir o PostgreSQL

```bash
docker compose up -d postgres
```

### 2. Executar a Ingestão

```bash
python -m src.ingestion.dlt_pipeline
```

Carrega os 5 CSVs em tabelas `raw.*` no PostgreSQL, com validação de contagem de linhas.

### 3. Executar as Transformações

```bash
dbt run --project-dir dbt --profiles-dir dbt --target dev
dbt test --project-dir dbt --profiles-dir dbt --target dev
```

Executa todos os modelos dbt (staging → intermediate → marts) e roda os testes de qualidade.

### 4. Rodar as Queries

```bash
psql -h localhost -U retize_user -d retize_social -f queries/pergunta_01.sql
psql -h localhost -U retize_user -d retize_social -f queries/pergunta_02.sql
psql -h localhost -U retize_user -d retize_social -f queries/pergunta_03.sql
psql -h localhost -U retize_user -d retize_social -f queries/pergunta_04.sql
psql -h localhost -U retize_user -d retize_social -f queries/pergunta_05.sql
```

---

## Principais Decisões Técnicas

### Por que dlt para ingestão?

- **Type inference automático**: infere tipos de colunas a partir dos dados
- **Write disposition `replace`**: garante idempotência — reruns substituem dados anteriores
- **Validação embutida**: contagem de linhas pós-carga garante integridade
- **Simplicidade**: menos código boilerplate comparado a scripts manuais de COPY/INSERT

### Por que dbt para transformação?

- **Organização em camadas**: staging → intermediate → marts facilita manutenção e debugging
- **Testes de qualidade**: `dbt test` valida constraints (not null, unique, accepted values)
- **Macros reutilizáveis**: fórmula de engajamento centralizada em macro, evitando duplicação
- **Linhagem de dados**: `dbt docs` gera grafo de dependências entre modelos

### Por que Airflow para orquestração?

- **Visibilidade**: UI centralizada com logs por task, estados e histórico de execuções
- **Retries automáticos**: configuração de retries com backoff exponencial
- **Diferencial do desafio**: conteinerização completa da stack (PostgreSQL + Airflow)

### Por que PostgreSQL local?

- Requisito do desafio
- Suporte nativo a tipos como `timestamptz`, funções de extração de data (`extract(dow from ...)`) e janelas analíticas (`row_number() over (...)`)

---

## Limitações e Premissas

1. **Período de dados**: as queries filtram dados entre `2025-03-01` e `2026-03-31`, conforme especificado no dicionário de dados
2. **Engajamento por reach**: a fórmula usa `reach` como denominador. Alternativas como `views` ou `total_interactions` foram consideradas, mas `reach` é a métrica mais consistente entre plataformas
3. **Stories do Instagram**: métricas como `comments_count` e `is_comment_enabled` podem ser nulas para stories. O modelo trata isso com `coalesce` e filtros apropriados
4. **Sentimento previsto**: os comentários já vêm com `predicted_sentiment` classificado. Não foi feita reclassificação ou validação adicional
5. **IDs não padronizados**: Instagram usa `id`, TikTok usa `item_id`. A harmonização ocorre na camada intermediate
6. **Escala local**: a solução foi projetada para dados de amostra. Para produção em escala, o destino de ingestão migraria para BigQuery (conforme stack da Retize)

---

## Melhorias Futuras

- **Incremental loads**: substituir `write_disposition="replace"` por `append` com detecção de duplicatas para evitar reprocessamento completo
- **Data quality avançada**: adicionar testes dbt customizados (ex: validação de ranges, consistência cross-platform)
- **CI/CD**: pipeline de testes automatizados para SQL e Python em PRs
- **Monitoramento**: alertas de falha no Airflow via Slack/email
- **Migração para BigQuery**: adaptar o destino dlt e o adapter dbt para BigQuery, alinhando à stack de produção da Retize

---

## Organização do Repositório

```
├── airflow/
│   ├── dags/           # DAG do Airflow (retize_social_elt.py)
│   └── logs/           # Logs de execução
├── dashboard/
│   ├── app.py          # Aplicação Streamlit (dashboard)
│   └── requirements.txt
├── dbt/
│   ├── models/         # Modelos SQL (staging → intermediate → marts)
│   ├── macros/         # Macros reutilizáveis (engagement calculation)
│   └── tests/          # Testes de qualidade de dados
├── queries/            # 5 queries respondendo perguntas de negócio
├── scripts/
│   └── run.ps1         # Script único de execução completa
├── src/
│   └── ingestion/      # Pipeline dlt de ingestão dos CSVs
├── sql/
│   └── bootstrap/      # Scripts de inicialização do PostgreSQL
├── docker-compose.yml  # Stack completa (PostgreSQL + Airflow + Streamlit)
├── docker/
│   ├── airflow/        # Dockerfile e requirements do Airflow
│   └── streamlit/      # Dockerfile do Streamlit
├── dicionario.md       # Dicionário de dados dos CSVs
└── requirements.txt    # Dependências Python
```

---

## Uso de IA

Este desafio utilizou ferramentas de IA como apoio em:

- Debugging de erros de build e configuração do Airflow
- Revisão de código Python e SQL
- Escrita e organização da documentação

Todas as decisões técnicas, modelagem de dados e consultas SQL foram revisadas e compreendidas antes da entrega.
