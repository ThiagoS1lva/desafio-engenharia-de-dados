import os
from pathlib import Path

import pandas as pd
import plotly.express as px
import psycopg2
import streamlit as st
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

QUERIES_DIR = Path(__file__).resolve().parents[1] / "queries"

PAGES = [
    {
        "title": "Melhor dia da semana para publicar",
        "file": "pergunta_01.sql",
        "description": "Para cada conta, qual é o melhor dia da semana para publicar, considerando o engajamento médio por conteúdo?",
        "chart_type": "bar",
        "x": "weekday_name",
        "y": "avg_engagement_rate",
        "color": "account_name",
        "labels": {"weekday_name": "Dia da Semana", "avg_engagement_rate": "Engajamento Médio (%)", "account_name": "Conta"},
    },
    {
        "title": "Plataforma com mais comentários negativos",
        "file": "pergunta_02.sql",
        "description": "Para cada conta, qual plataforma apresentou a maior proporção de comentários negativos no período analisado?",
        "chart_type": "barh",
        "x": "negative_comment_rate",
        "y": "account_name",
        "color": "platform",
        "labels": {"negative_comment_rate": "Taxa de Comentários Negativos", "account_name": "Conta", "platform": "Plataforma"},
    },
    {
        "title": "Top 10 conteúdos com maior engajamento",
        "file": "pergunta_03.sql",
        "description": "Quais são os 10 conteúdos com maior taxa de engajamento no período, considerando Instagram e TikTok?",
        "chart_type": "barh",
        "x": "engagement_rate",
        "y": "content_id",
        "color": "platform",
        "labels": {"engagement_rate": "Taxa de Engajamento (%)", "content_id": "Conteúdo", "platform": "Plataforma"},
    },
    {
        "title": "Top 3 conteúdos por conta",
        "file": "pergunta_04.sql",
        "description": "Quais são os 3 conteúdos com maior taxa de engajamento por conta no período?",
        "chart_type": "bar",
        "x": "content_id",
        "y": "engagement_rate",
        "color": "account_name",
        "facet_col": "account_name",
        "labels": {"engagement_rate": "Taxa de Engajamento (%)", "content_id": "Conteúdo", "account_name": "Conta"},
    },
    {
        "title": "Melhor formato de conteúdo por conta",
        "file": "pergunta_05.sql",
        "description": "Para cada conta, qual formato de conteúdo apresenta o melhor desempenho médio de engajamento?",
        "chart_type": "bar",
        "x": "content_format",
        "y": "avg_engagement_rate",
        "color": "account_name",
        "labels": {"content_format": "Formato", "avg_engagement_rate": "Engajamento Médio (%)", "account_name": "Conta"},
    },
]


@st.cache_data(ttl=60)
def run_query(sql_file: str) -> pd.DataFrame:
    conn = psycopg2.connect(
        host=os.getenv("POSTGRES_HOST", "localhost"),
        port=int(os.getenv("POSTGRES_PORT", "5432")),
        dbname=os.getenv("POSTGRES_DB", "retize_social"),
        user=os.getenv("POSTGRES_USER", "retize_user"),
        password=os.getenv("POSTGRES_PASSWORD", "retize_password"),
    )
    sql = (QUERIES_DIR / sql_file).read_text(encoding="utf-8")
    df = pd.read_sql(sql, conn)
    conn.close()
    return df


st.set_page_config(page_title="Retize — Dashboard", layout="wide")

st.title("Retize — Dashboard de Performance")
st.caption("Resultados das análises de engajamento e sentimento das redes sociais")

page = st.sidebar.selectbox("Selecione a análise", [p["title"] for p in PAGES])
cfg = next(p for p in PAGES if p["title"] == page)

st.subheader(cfg["title"])
st.info(cfg["description"])

df = run_query(cfg["file"])

if df.empty:
    st.warning("Nenhum dado encontrado. Execute o pipeline antes.")
    st.stop()

st.dataframe(df, use_container_width=True, hide_index=True)

if cfg["chart_type"] == "bar":
    fig = px.bar(
        df,
        x=cfg["x"],
        y=cfg["y"],
        color=cfg.get("color"),
        facet_col=cfg.get("facet_col"),
        labels=cfg.get("labels", {}),
        template="plotly_white",
    )
elif cfg["chart_type"] == "barh":
    fig = px.bar(
        df,
        x=cfg["x"],
        y=cfg["y"],
        color=cfg.get("color"),
        orientation="h",
        labels=cfg.get("labels", {}),
        template="plotly_white",
    )
else:
    fig = None

if fig:
    st.plotly_chart(fig, use_container_width=True)
