----------------
-- Procedures --
----------------

USE pulse_university;

-- Procedure 1: Update expired tickets for events that have ended
DELIMITER //
CREATE PROCEDURE UpdateExpiredTickets()
BEGIN
	DECLARE activeStatus INT;
	DECLARE onOfferStatus INT;
	DECLARE unusedStatus INT;

	-- Fetch all necessary status IDs
	SELECT status_id INTO activeStatus
	FROM Ticket_Status
	WHERE name = 'active'
	LIMIT 1;

	SELECT status_id INTO onOfferStatus
	FROM Ticket_Status
	WHERE name = 'on offer'
	LIMIT 1;

	SELECT status_id INTO unusedStatus
	FROM Ticket_Status
	WHERE name = 'unused'
	LIMIT 1;

	-- Update tickets
	UPDATE Ticket t
		JOIN Event e ON t.event_id = e.event_id
		JOIN Festival f ON e.fest_year = f.fest_year
	SET t.status_id = unusedStatus
	WHERE CURDATE() > f.end_date
		AND (t.status_id = activeStatus OR t.status_id = onOfferStatus);
END;
//
DELIMITER ;

-- Procedure 2: Expire resale offers after the related event has ended
DELIMITER //
CREATE PROCEDURE ExpireResaleOffers()
BEGIN
	DELETE FROM Resale_Offer
	WHERE event_id IN (
		SELECT e.event_id
		FROM Event e
			JOIN Festival f ON e.fest_year = f.fest_year
		WHERE CURDATE() > f.end_date
	);
END;
//
DELIMITER ;

-- Procedure 3: Expire resale interests after the related event has ended
DELIMITER //
CREATE PROCEDURE ExpireResaleInterests()
BEGIN
	DELETE FROM Resale_Interest
	WHERE event_id IN (
		SELECT e.event_id
		FROM Event e
			JOIN Festival f ON e.fest_year = f.fest_year
		WHERE CURDATE() > f.end_date
	);
END;
//
DELIMITER ;
