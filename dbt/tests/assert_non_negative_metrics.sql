-- Valida que metricas de contagem nao sao negativas.
-- Curtidas, comentarios, compartilhamentos e alcance devem ser >= 0.

select
    'stg_instagram__media' as source,
    content_id,
    'like_count' as metric,
    like_count as value
from {{ ref('stg_instagram__media') }}
where like_count < 0

union all

select
    'stg_instagram__media',
    content_id,
    'comments_count',
    comments_count
from {{ ref('stg_instagram__media') }}
where comments_count < 0

union all

select
    'stg_tiktok__posts',
    content_id,
    'likes',
    likes
from {{ ref('stg_tiktok__posts') }}
where likes < 0

union all

select
    'stg_tiktok__posts',
    content_id,
    'comments',
    comments
from {{ ref('stg_tiktok__posts') }}
where comments < 0

union all

select
    'stg_tiktok__posts',
    content_id,
    'shares',
    shares
from {{ ref('stg_tiktok__posts') }}
where shares < 0

union all

select
    'stg_tiktok__posts',
    content_id,
    'video_views',
    video_views
from {{ ref('stg_tiktok__posts') }}
where video_views < 0

union all

select
    'stg_tiktok__posts',
    content_id,
    'reach',
    reach
from {{ ref('stg_tiktok__posts') }}
where reach < 0
