with instagram_comments as (
    select
        platform,
        content_id,
        comment_id,
        comment_timestamp,
        sentiment,
        confidence_sentiment
    from {{ ref('stg_instagram__comments') }}
),

tiktok_comments as (
    select
        platform,
        content_id,
        comment_id,
        comment_timestamp,
        sentiment,
        confidence_sentiment
    from {{ ref('stg_tiktok__comments') }}
)

select * from instagram_comments
union all
select * from tiktok_comments
