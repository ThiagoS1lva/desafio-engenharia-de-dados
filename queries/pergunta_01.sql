-- Pergunta 1: Para cada conta, qual e o melhor dia da semana para publicar,
-- considerando o engajamento medio por conteudo?

with content_engagement as (
    select
        account_name,
        weekday,
        case weekday
            when 0 then 'domingo'
            when 1 then 'segunda-feira'
            when 2 then 'terca-feira'
            when 3 then 'quarta-feira'
            when 4 then 'quinta-feira'
            when 5 then 'sexta-feira'
            when 6 then 'sabado'
        end as weekday_name,
        avg(engagement_rate) as avg_engagement_rate
    from marts.mart_content_performance
    where engagement_rate is not null
      and published_at >= '2025-03-01'::timestamptz
      and published_at < '2026-04-01'::timestamptz
    group by account_name, weekday
),

ranked as (
    select
        account_name,
        weekday,
        weekday_name,
        avg_engagement_rate,
        row_number() over (
            partition by account_name
            order by avg_engagement_rate desc, weekday asc
        ) as rn
    from content_engagement
)

select
    account_name,
    weekday_name,
    weekday,
    round(avg_engagement_rate, 2) as avg_engagement_rate
from ranked
where rn = 1
order by account_name
