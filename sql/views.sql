----------------
----- Views ----
----------------

USE pulse_university;

-- View 1: Festival revenue by year and payment method
CREATE VIEW View_Festival_Revenue AS
	SELECT 
		f.fest_year,
		pm.name AS payment_method,
		SUM(t.cost) AS total_revenue
	FROM Ticket t
		JOIN Event e ON t.event_id = e.event_id
		JOIN Festival f ON e.fest_year = f.fest_year
		JOIN Payment_Method pm ON t.method_id = pm.method_id
	GROUP BY 
		f.fest_year,
		pm.name;

-- View 2: Artist performance count and average overall review
CREATE VIEW View_Artist_Performance AS
	SELECT 
		a.artist_id,
		CONCAT(a.first_name, ' ', a.last_name) AS artist_name,
		COUNT(pa.perf_id) AS performance_count,
		AVG(r.overall) AS avg_overall_rating
	FROM Artist a
		LEFT JOIN Performance_Artist pa ON a.artist_id = pa.artist_id
		LEFT JOIN Review r ON pa.perf_id = r.perf_id
	GROUP BY 
		a.artist_id,
		artist_name;

-- View 3: Event staff actuals vs required (5% security, 2% support)
CREATE VIEW View_Event_Staff AS
	SELECT 
		e.event_id,
		e.title,
		s.capacity,
		(
			SELECT COUNT(*)
			FROM Works_On wo
				JOIN Staff st ON wo.staff_id = st.staff_id
			WHERE wo.event_id = e.event_id
				AND st.role_id = (
					SELECT role_id
					FROM Staff_Role
					WHERE name = 'security'
					LIMIT 1
				)
		) AS security_count,
		(
			SELECT COUNT(*)
			FROM Works_On wo
				JOIN Staff st ON wo.staff_id = st.staff_id
			WHERE wo.event_id = e.event_id
				AND st.role_id = (
					SELECT role_id
					FROM Staff_Role
					WHERE name = 'support'
					LIMIT 1
				)
		) AS support_count,
		CEIL(s.capacity * 0.05) AS required_security,
		CEIL(s.capacity * 0.02) AS required_support
	FROM Event e
		JOIN Stage s ON e.stage_id = s.stage_id;

-- View 4: Attendee’s performances and their average review per event
CREATE VIEW View_Attendee_Performance AS
	SELECT 
		att.attendee_id,
		CONCAT(att.first_name, ' ', att.last_name) AS attendee_name,
		p.perf_id,
		e.title AS event_title,
		(
			SELECT AVG(r.overall)
			FROM Review r
			WHERE r.perf_id = p.perf_id
				AND r.attendee_id = att.attendee_id
		) AS avg_rating
	FROM Attendee att
		JOIN Ticket t ON att.attendee_id = t.attendee_id
		JOIN Event e ON t.event_id = e.event_id
		JOIN Performance p ON e.event_id = p.event_id;

-- View 5: Unique artist genre pairs and how many artists share them
CREATE VIEW View_Genre_Pairs AS
	SELECT 
		LEAST(ag1.genre_id, ag2.genre_id) AS genre_id1,
		GREATEST(ag1.genre_id, ag2.genre_id) AS genre_id2,
		COUNT(DISTINCT ag1.artist_id) AS artist_count
	FROM Artist_Genre ag1
		JOIN Artist_Genre ag2 ON ag1.artist_id = ag2.artist_id
	WHERE ag1.genre_id < ag2.genre_id
	GROUP BY 
		LEAST(ag1.genre_id, ag2.genre_id),
		GREATEST(ag1.genre_id, ag2.genre_id);

-- View 6: Artists and how many continents they’ve performed in
CREATE VIEW View_Artist_Continents AS
	SELECT 
		a.artist_id,
		CONCAT(a.first_name, ' ', a.last_name) AS artist_name,
		COUNT(DISTINCT l.continent_id) AS continents_performed
	FROM Artist a
		JOIN Performance_Artist pa ON a.artist_id = pa.artist_id
		JOIN Performance p ON pa.perf_id = p.perf_id
		JOIN Event e ON p.event_id = e.event_id
		JOIN Festival f ON e.fest_year = f.fest_year
		JOIN Location l ON f.loc_id = l.loc_id
	GROUP BY 
		a.artist_id,
		artist_name;
