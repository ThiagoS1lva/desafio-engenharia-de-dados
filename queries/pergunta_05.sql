-- Pergunta 5: Para cada conta, qual formato de conteudo apresenta
-- o melhor desempenho medio de engajamento?

with format_engagement as (
    select
        account_name,
        content_format,
        avg(engagement_rate) as avg_engagement_rate
    from marts.mart_content_performance
    where engagement_rate is not null
      and published_at >= '2025-03-01'::timestamptz
      and published_at < '2026-04-01'::timestamptz
    group by account_name, content_format
),

ranked as (
    select
        account_name,
        content_format,
        avg_engagement_rate,
        row_number() over (
            partition by account_name
            order by avg_engagement_rate desc
        ) as rn
    from format_engagement
)

select
    account_name,
    content_format,
    round(avg_engagement_rate, 2) as avg_engagement_rate
from ranked
where rn = 1
order by account_name
