-- Pergunta 4: Quais sao os 3 conteudos com maior taxa de engajamento
-- por conta no periodo, considerando Instagram e TikTok?

with ranked as (
    select
        mcp.platform,
        mcp.content_id,
        mcp.account_name,
        mcp.content_format,
        mcp.published_at,
        mcp.engagement_total,
        mcp.reach,
        round(mcp.engagement_rate, 2) as engagement_rate,
        row_number() over (
            partition by mcp.account_name
            order by mcp.engagement_rate desc, mcp.published_at desc, mcp.platform asc, mcp.content_id asc
        ) as rn
    from marts.mart_content_performance mcp
    where mcp.engagement_rate is not null
      and mcp.published_at >= '2025-03-01'::timestamptz
      and mcp.published_at < '2026-04-01'::timestamptz
)

select
    platform,
    content_id,
    account_name,
    content_format,
    published_at,
    engagement_total,
    reach,
    engagement_rate
from ranked
where rn <= 3
order by account_name, rn
