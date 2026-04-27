with content as (
    select
        platform,
        content_id,
        account_name,
        content_format,
        engagement_rate
    from {{ ref('mart_content_performance') }}
),

comment_agg as (
    select
        platform,
        content_id,
        count(*) as total_comments_with_sentiment,
        count(*) filter (where sentiment = 'positivo') as positive_comments,
        count(*) filter (where sentiment = 'neutro') as neutral_comments,
        count(*) filter (where sentiment = 'negativo') as negative_comments
    from {{ ref('mart_comment_sentiment') }}
    group by platform, content_id
)

select
    c.platform,
    c.content_id,
    c.account_name,
    c.content_format,
    c.engagement_rate,
    coalesce(ca.total_comments_with_sentiment, 0) as total_comments_with_sentiment,
    coalesce(ca.positive_comments, 0) as positive_comments,
    coalesce(ca.neutral_comments, 0) as neutral_comments,
    coalesce(ca.negative_comments, 0) as negative_comments,
    case
        when coalesce(ca.total_comments_with_sentiment, 0) = 0 then null
        else ca.negative_comments::numeric / ca.total_comments_with_sentiment
    end as negative_comment_rate
from content c
left join comment_agg ca
    on c.platform = ca.platform
    and c.content_id = ca.content_id
