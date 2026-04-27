{% macro calculate_engagement_total(platform, likes, comments, shares, saves_or_favorites, profile_visits_or_profile_views, new_followers_or_follows, total_interactions) %}
    {# Calcula o engajamento total harmonizando Instagram e TikTok #}
    case
        when {{ platform }} = 'instagram' then
            coalesce(
                {{ total_interactions }},
                {{ likes }} + {{ comments }} + {{ shares }} + {{ saves_or_favorites }} + {{ profile_visits_or_profile_views }} + {{ new_followers_or_follows }},
                0
            )
        when {{ platform }} = 'tiktok' then
            coalesce(
                {{ likes }} + {{ comments }} + {{ shares }} + {{ saves_or_favorites }} + {{ profile_visits_or_profile_views }} + {{ new_followers_or_follows }},
                0
            )
        else 0
    end
{% endmacro %}
