----------------
-- Procedures --
----------------

USE pulse_university;

-- Procedure 1: Update expired tickets for events that have ended
DELIMITER //
CREATE PROCEDURE UpdateExpiredTickets()
BEGIN
	UPDATE Ticket t
		JOIN Event e ON t.event_id = e.event_id
		JOIN Festival f ON e.fest_year = f.fest_year
	SET t.status_id = (
			SELECT status_id
			FROM Ticket_Status
			WHERE name = 'on offer'
			LIMIT 1
		)
	WHERE CURDATE() > f.end_date
		AND t.status_id <> (
			SELECT status_id
			FROM Ticket_Status
			WHERE name = 'used'
			LIMIT 1
		);
END;
//
DELIMITER ;

-- Procedure 2: Get the top 5 attendees by total review score for a given artist
DELIMITER //
CREATE PROCEDURE GetTopAttendeesForArtist(
	IN inArtistID INT
)
BEGIN
	SELECT 
		att.attendee_id,
		CONCAT(att.first_name, ' ', att.last_name) AS attendee_name,
		SUM(r.overall) AS total_review_score
	FROM Review r
		JOIN Attendee att ON r.attendee_id = att.attendee_id
		JOIN Performance_Artist pa ON r.perf_id = pa.perf_id
	WHERE pa.artist_id = inArtistID
	GROUP BY 
		att.attendee_id, attendee_name
	ORDER BY total_review_score DESC
	LIMIT 5;
END;
//
DELIMITER ;

-- Procedure 3: Insert a new performance record
DELIMITER //
CREATE PROCEDURE AddPerformance(
	IN p_type_id INT,
	IN p_datetime DATETIME,
	IN p_duration TINYINT,
	IN p_break_duration TINYINT,
	IN p_stage_id INT,
	IN p_event_id INT,
	IN p_sequence_number TINYINT
)
BEGIN
	INSERT INTO Performance (
			type_id, 
			datetime, 
			duration, 
			break_duration, 
			stage_id, 
			event_id, 
			sequence_number
		)
	VALUES (
			p_type_id, 
			p_datetime, 
			p_duration, 
			p_break_duration, 
			p_stage_id, 
			p_event_id, 
			p_sequence_number
		);
END;
//
DELIMITER ;
