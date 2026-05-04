WITH matches_unnested AS (
    SELECT jsonb_array_elements("data") AS "match"
    FROM {{ source('raw_data', 'matches') }} 
),
home_teams AS (
    SELECT 
		(m."match" -> 'team1' ->> 'teamId') :: int AS team_id,
		m."match" -> 'team1' ->> 'teamName' AS team_name,
		m."match" -> 'team1' ->> 'shortName' AS team_name_short,
		m."match" -> 'team1' ->> 'teamIconUrl' AS team_icon_url
    FROM matches_unnested m 
),
away_teams AS (
    SELECT 
		(m."match" -> 'team2' ->> 'teamId') :: int AS team_id,
		m."match" -> 'team2' ->> 'teamName' AS team_name,
		m."match" -> 'team2' ->> 'shortName' AS team_name_short,
		m."match" -> 'team2' ->> 'teamIconUrl' AS team_icon_url
    FROM matches_unnested m 
)
SELECT DISTINCT
    team_id,
    team_name,
    team_name_short,
    team_icon_url
FROM (
	SELECT *
	FROM home_teams
    UNION ALL
	SELECT *
	FROM away_teams
)