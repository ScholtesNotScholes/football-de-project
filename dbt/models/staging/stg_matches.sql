WITH latest_matches_unnested AS (
    SELECT jsonb_array_elements("data") AS "match"
    FROM {{ source('raw_data', 'matches') }}
	ORDER BY created_at DESC
	LIMIT 1
)
SELECT DISTINCT
	(m."match" 				->> 'matchID') :: int AS match_id,
	(m."match" -> 'group' 	->> 'groupID') :: int AS matchday_id,
	(m."match" -> 'team1' 	->> 'teamId') :: int AS home_team_id,
	(m."match" -> 'team2' 	->> 'teamId') :: int AS away_team_id,
	COALESCE(m."match" -> 'goals' -> (jsonb_array_length(m."match" -> 'goals') - 1) ->> 'scoreTeam1', '0') :: int AS home_team_goals,
	COALESCE(m."match" -> 'goals' -> (jsonb_array_length(m."match" -> 'goals') - 1) ->> 'scoreTeam2', '0') :: int AS away_team_goals
FROM latest_matches_unnested m