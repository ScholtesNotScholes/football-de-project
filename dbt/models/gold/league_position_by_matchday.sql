WITH home_record AS (
	SELECT 
		sm.home_team_id AS team_id,
		sm.matchday_id,
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
		sm.matchday_id,
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
 
running_record AS (
	SELECT 
		r.team_id,
		sm.matchday_order_id,
		sm.matchday_name,
		sum(r.points) 			                OVER (PARTITION BY r.team_id ORDER BY sm.matchday_order_id) AS running_points,
		sum(r.goals_scored) 	                OVER (PARTITION BY r.team_id ORDER BY sm.matchday_order_id) AS running_goals_scored,
		sum(r.goals_conceded) 	                OVER (PARTITION BY r.team_id ORDER BY sm.matchday_order_id) AS running_goals_conceded,
		sum(r.goals_scored - r.goals_conceded)  OVER (PARTITION BY r.team_id ORDER BY sm.matchday_order_id) AS running_goal_difference
	FROM (
		SELECT *
		FROM home_record 
		UNION ALL 
		SELECT *
		FROM away_record 
	) r
	JOIN {{ source('staging', 'stg_matchdays') }} sm 
        ON r.matchday_id = sm.matchday_id 
	GROUP BY 
        r.team_id, 
        sm.matchday_order_id, 
        sm.matchday_name, 
        r.points, 
        r.goals_scored, 
        r.goals_conceded 
)

SELECT 
	ROW_NUMBER() OVER (
        PARTITION BY r.matchday_order_id 
        ORDER BY 
            r.running_points DESC, 
            r.running_goal_difference DESC,
            r.running_goals_scored DESC
    ) AS running_league_position,
    r.matchday_order_id,
	r.matchday_name,
	st.team_name,
	r.running_points,
	r.running_goals_scored,
	r.running_goals_conceded,
	r.running_goal_difference
FROM running_record r
LEFT JOIN {{ source('staging', 'stg_teams') }} st 
	ON r.team_id = st.team_id
ORDER BY 
    r.matchday_order_id, 
    r.running_points DESC, 
    r.running_goal_difference DESC