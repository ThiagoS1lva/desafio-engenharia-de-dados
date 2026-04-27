-- Pergunta 3: Quais sao os 10 conteudos com maior taxa de engajamento
-- no periodo, considerando Instagram e TikTok?

select
    mcp.platform,
    mcp.content_id,
    mcp.account_name,
    mcp.content_format,
    mcp.published_at,
    mcp.engagement_total,
    mcp.reach,
    round(mcp.engagement_rate, 2) as engagement_rate
from marts.mart_content_performance mcp
where mcp.engagement_rate is not null
  and mcp.published_at >= '2025-03-01'::timestamptz
  and mcp.published_at < '2026-04-01'::timestamptz
order by mcp.engagement_rate desc, mcp.published_at desc, mcp.platform asc, mcp.content_id asc
limit 10
