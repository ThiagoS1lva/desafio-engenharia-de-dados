-- Pergunta 2: Para cada conta, qual plataforma apresentou a maior proporcao
-- de comentarios negativos no periodo analisado?

with account_platform_sentiment as (
    select
        c.account_name,
        c.platform,
        sum(cs.total_comments_with_sentiment) as total_comments,
        sum(cs.negative_comments) as negative_comments,
        case
            when sum(cs.total_comments_with_sentiment) = 0 then null
            else sum(cs.negative_comments)::numeric / sum(cs.total_comments_with_sentiment)
        end as negative_comment_rate
    from marts.mart_content_with_sentiment cs
    join marts.mart_content_performance c
        on cs.platform = c.platform
        and cs.content_id = c.content_id
    where c.published_at >= '2025-03-01'::timestamptz
      and c.published_at < '2026-04-01'::timestamptz
      and cs.total_comments_with_sentiment > 0
    group by c.account_name, c.platform
),

ranked as (
    select
        account_name,
        platform,
        total_comments,
        negative_comments,
        round(negative_comment_rate, 4) as negative_comment_rate,
        row_number() over (
            partition by account_name
            order by negative_comment_rate desc nulls last
        ) as rn
    from account_platform_sentiment
)

select
    account_name,
    platform,
    total_comments,
    negative_comments,
    negative_comment_rate
from ranked
where rn = 1
order by account_name
