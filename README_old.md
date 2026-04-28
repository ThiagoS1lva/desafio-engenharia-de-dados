# Desafio Técnico de Engenharia de Dados

## Sobre a Retize

Você acaba de ingressar no time de Engenharia de Dados da [Retize](https://retize.com.br). Parte do nosso trabalho envolve consolidar dados de performance de redes sociais para permitir análises comparáveis entre plataformas, formatos de conteúdo e contas.

## Nossa Stack

Na Retize, usamos PostgreSQL para cargas e consultas operacionais, BigQuery para análise em escala, Airflow para orquestrar pipelines, dlt para extrair e carregar dados de fontes externas e dbt para organizar transformações analíticas.

## Sobre o Desafio

O foco deste desafio está em fundamentos de Python e SQL aplicados localmente com PostgreSQL.

Você receberá arquivos CSV com uma amostra de dados brutos de Instagram e TikTok já extraída das plataformas. A proposta é construir uma solução reproduzível, da carga inicial dos arquivos até um modelo analítico capaz de responder a perguntas de negócio sobre alcance, engajamento e sentimento de comentários.

Você trabalhará com dados imperfeitos do mundo real. Esperamos uma solução clara, correta, bem justificada e fácil de executar.

## Dados Fornecidos

Os arquivos serão enviados junto com o desafio:

- `instagram_media.csv`
- `instagram_media_insights.csv`
- `instagram_comments.csv`
- `tiktok_posts.csv`
- `tiktok_comments.csv`

Os comentários já virão enriquecidos com classificação de sentimento.

Estamos disponibilizando neste repositório um dicionário de dados com as colunas disponíveis em cada tabela (dicionario.md).

## Objetivo do Desafio

Sua solução deve:

1. Carregar os arquivos CSV em tabelas brutas no PostgreSQL.
2. Tratar as inconsistências mínimas necessárias para tornar os dados utilizáveis.
3. Construir um modelo analítico que permita responder às perguntas de negócio abaixo.
4. Entregar as consultas SQL e a documentação necessária para reproduzir o resultado.

## Ambiente

Use PostgreSQL como banco local da solução.

O banco deve ser executado com Docker Compose.

## Escopo Esperado

### Parte 1. Ingestão dos dados

Desenvolva uma forma reproduzível de carregar os arquivos CSV brutos em tabelas iniciais.

Esperamos nesta etapa:

- um ou mais scripts em Python para automatizar a carga dos arquivos
- instruções claras de execução
- tratamento básico de erros
- indicação de sucesso ou falha durante a carga

### Parte 2. Transformação e modelagem

Após a ingestão, transforme os dados com SQL até chegar a um modelo analítico adequado para responder às perguntas de negócio.

Você pode organizar essa etapa da forma que considerar mais apropriada. Vale usar apenas SQL ou ferramentas como `dbt`, se desejar. O uso de `dbt` é bem-vindo, mas não é obrigatório.

Esperamos nesta etapa:

- definição clara do nível de detalhe de cada tabela final
- joins coerentes entre as tabelas de conteúdo, métricas e comentários
- padronização mínima de métricas entre Instagram e TikTok
- decisões de modelagem compatíveis com as perguntas analíticas
- documentação das principais escolhas e simplificações

Se for necessário definir uma fórmula de engajamento ou harmonizar métricas entre plataformas, explique essa escolha no README.

Preferimos um modelo analítico bem pensado e bem justificado a uma arquitetura mais complexa do que o necessário.

## Organização Sugerida

Você não precisa seguir exatamente a estrutura abaixo, mas sugerimos uma organização mínima para facilitar a avaliação:

- `src/` para scripts Python de ingestão e apoio
- `sql/` ou `transformations/` para scripts SQL de transformação, caso não use `dbt`
- `dbt/` para o projeto, caso opte por usar `dbt`
- `queries/` para as consultas finais que respondem às perguntas de negócio
- `README.md` com instruções de execução e decisões técnicas

Se fizer sentido para sua solução, sugerimos também separar tabelas ou etapas em camadas com convenções como:

- `raw_*` para carga inicial dos CSVs
- `stg_*` para padronização e limpeza
- `mart_*` para tabelas ou views analíticas finais

Essas convenções são apenas sugestões. Você pode adotar outra organização, desde que ela seja clara e consistente.

## Perguntas de Negócio

Sua solução deve responder obrigatoriamente às 5 perguntas abaixo com SQL:

1. Para cada conta, qual é o melhor dia da semana para publicar, considerando o engajamento médio por conteúdo?
2. Para cada conta, qual plataforma apresentou a maior proporção de comentários negativos no período analisado?
3. Quais são os 10 conteúdos com maior taxa de engajamento no período, considerando Instagram e TikTok?
4. Quais são os 3 conteúdos com maior taxa de engajamento por conta no período, considerando Instagram e TikTok?
5. Para cada conta, qual formato de conteúdo apresenta o melhor desempenho médio de engajamento?

## Entregáveis

### 1. Repositório no GitHub

Repositório público com todo o código da solução.

### 2. README

O README do repositório deve explicar de forma objetiva:

- visão geral da solução
- arquitetura ou fluxo adotado
- como preparar o ambiente
- como subir o PostgreSQL com Docker Compose
- como executar a ingestão
- como executar as transformações
- como rodar as queries
- principais decisões técnicas
- justificativas para escolhas de modelagem e tecnologia
- limitações, premissas e melhorias futuras

### 3. Modelagem de dados

Inclua uma representação simples do modelo proposto, contendo:

- tabelas principais
- granularidade
- principais relacionamentos

Pode ser um diagrama MER, um esquema em texto ou ambos.

### 4. Queries analíticas

Arquivos `.sql` respondendo às 5 perguntas de negócio.

## Critérios de Avaliação

O que vamos avaliar:

- corretude da carga e reprodutibilidade da solução
- clareza, organização e legibilidade do código Python
- qualidade, correção e legibilidade do SQL
- coerência entre granularidade, modelagem e perguntas de negócio
- capacidade de lidar com inconsistências entre fontes sem complexidade desnecessária
- capacidade de justificar decisões e trade-offs de forma objetiva
- clareza da documentação e facilidade de execução da solução

## Diferenciais

Os itens abaixo são diferenciais, não obrigatórios.

Diferenciais de engenharia de dados:

- uso de `dbt` para organizar transformações e testes
- orquestração simples do fluxo de ingestão e transformação
- conteinerização adicional da solução além do PostgreSQL com Docker Compose
- testes ou validações de qualidade de dados
- logging estruturado
- documentação especialmente clara de troubleshooting e decisões de modelagem

Diferenciais de apresentação:

- uma forma simples de apresentação dos dados finais, como um dashboard em Streamlit ou uma API com um endpoint de resumo

## Política de Uso de Inteligência Artificial

O uso de ferramentas de IA é permitido neste desafio.

Uso recomendado:

- apoio para debugging
- revisão de código
- esclarecimento de conceitos técnicos
- apoio na escrita de documentação

Uso não recomendado:

- delegar à IA a construção integral da solução
- copiar código sem revisar, adaptar e compreender
- entregar decisões técnicas que você não consiga justificar

Se você usar IA de forma relevante, pode incluir no README um breve resumo de como ela foi utilizada. Isso não é obrigatório, mas é bem-vindo.

A solução entregue deve refletir sua capacidade de engenharia e tomada de decisão. Durante a conversa sobre o desafio, esperamos que você consiga explicar e defender as escolhas feitas.

## Prazo de Entrega

- 7 dias corridos a partir do recebimento do desafio

## Forma de Envio

- repositório público no GitHub
- envio do link do repositório para `desafios.tech@retize.com.br`
- sugestão de assunto do e-mail: `Desafio Técnico | Engenheiro(a) de Dados | [Seu Nome]`

## Orientações Finais

Busque uma solução simples, clara e reproduzível.

Priorize correção, clareza e a capacidade de justificar suas escolhas.

Se precisar assumir simplificações, documente essas decisões no repositório.

Também é válido registrar melhorias que você implementaria em uma próxima versão.

## Execução Orquestrada com Airflow

Foi adicionado um DAG completo no Airflow com o fluxo:

- `dlt` ingestão (`src.ingestion.dlt_pipeline`)
- `dbt run`
- `dbt test`
- execução das 5 queries finais

O DAG usa `schedule="@once"`, o que significa que executa automaticamente assim que o scheduler inicializa.

### Comando único (PowerShell)

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\run.ps1
```

O script automaticamente:

- sobe o Docker Compose (com build)
- valida containers e DAG
- detecta runs finalizados e faz reset automático para permitir rerun
- aguarda o DAG run iniciar e acompanha até `success` ou `failed`
- imprime o status final de cada task
- timeout padrão: **20 minutos**

Ou simplesmente use Docker Compose diretamente:

```bash
docker compose up -d
```

O pipeline executa sozinho. Use o script apenas para monitoramento com output amigável.

### Parâmetros úteis

```powershell
# Evita rebuild de imagem
powershell -ExecutionPolicy Bypass -File .\scripts\run.ps1 -SkipBuild

# Ajusta timeout de espera do run
powershell -ExecutionPolicy Bypass -File .\scripts\run.ps1 -TimeoutMinutes 30
```

### Rerun do pipeline

O script detecta automaticamente runs finalizados e faz reset. Para rerun manual:

```bash
docker exec airflow_scheduler airflow dags delete retize_social_elt --yes
```

O scheduler recriará automaticamente um novo run `@once`.

### Airflow UI

- URL: `http://localhost:8080`
- Usuário: `airflow`
- Senha: `airflow`
