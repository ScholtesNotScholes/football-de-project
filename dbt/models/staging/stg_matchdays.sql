WITH matches_unnested AS (
    SELECT jsonb_array_elements("data") AS "match"
    FROM {{ source('raw_data', 'matches') }} 
)
SELECT DISTINCT
    (m."match" -> 'group' ->> 'groupID') :: int AS matchday_id,
    m."match" -> 'group' ->> 'groupName' AS matchday_name,
    (m."match" -> 'group' ->> 'groupOrderID') :: int AS matchday_order_id
FROM matches_unnested m