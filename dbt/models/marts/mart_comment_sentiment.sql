select
    platform,
    content_id,
    comment_id,
    comment_timestamp,
    sentiment,
    confidence_sentiment
from {{ ref('int_comments__unified') }}
