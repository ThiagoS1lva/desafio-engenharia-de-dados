-- Valida que a confianca do sentimento esta entre 0 e 1.
-- Comentarios com confianca fora desse intervalo sao anomalias de classificacao.

select
    platform,
    comment_id,
    confidence_sentiment
from {{ ref('stg_instagram__comments') }}
where confidence_sentiment < 0
   or confidence_sentiment > 1

union all

select
    platform,
    comment_id,
    confidence_sentiment
from {{ ref('stg_tiktok__comments') }}
where confidence_sentiment < 0
   or confidence_sentiment > 1
