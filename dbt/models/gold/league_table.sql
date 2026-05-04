WITH home_record AS (
	SELECT 
		sm.home_team_id AS team_id,
		CASE
			WHEN sm.home_team_goals > sm.away_team_goals THEN 3
			WHEN sm.home_team_goals < sm.away_team_goals THEN 0
			WHEN sm.home_team_goals = sm.away_team_goals THEN 1
			ELSE NULL
		END AS points,
		sm.home_team_goals AS goals_scored,
		sm.away_team_goals AS goals_conceded
	FROM {{ source('staging', 'stg_matches') }} sm 
),
away_record AS (
	SELECT 
		sm.away_team_id AS team_id,
		CASE
			WHEN sm.away_team_goals > sm.home_team_goals THEN 3
			WHEN sm.away_team_goals < sm.home_team_goals THEN 0
			WHEN sm.away_team_goals = sm.home_team_goals THEN 1
			ELSE NULL
		END AS points,
		sm.away_team_goals AS goals_scored,
		sm.home_team_goals AS goals_conceded
	FROM {{ source('staging', 'stg_matches') }} sm 
),
total_record AS (
	SELECT 
		r.team_id, 
		sum(r.points) AS points_sum,
		sum(r.goals_scored) AS goals_scored_sum, 
		sum(r.goals_conceded) AS goals_conceded_sum
	FROM (
		SELECT *
		FROM home_record 
		UNION ALL 
		SELECT *
		FROM away_record 
	) r
	GROUP BY r.team_id
)
SELECT 
	ROW_NUMBER() OVER (ORDER BY r.points_sum DESC) AS league_position,
	st.team_name,
	r.points_sum,
	r.goals_scored_sum,
	r.goals_conceded_sum,
	r.goals_scored_sum - r.goals_conceded_sum AS goal_difference
FROM total_record r
LEFT JOIN {{ source('staging', 'stg_teams') }} st 
	ON r.team_id = st.team_id
ORDER BY r.points_sum DESC 