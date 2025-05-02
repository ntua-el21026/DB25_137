----------------
-- Procedures --
----------------

USE pulse_university;

-- ===========================================================
-- Procedure 1: Update expired tickets (active / on offer → unused)
-- ===========================================================
DELIMITER //
CREATE PROCEDURE UpdateExpiredTickets()
BEGIN
	DECLARE sActive  INT;	DECLARE sOffer  INT;	DECLARE sUnused INT;

	SELECT	status_id INTO sActive  FROM Ticket_Status WHERE name = 'active'   LIMIT 1;
	SELECT	status_id INTO sOffer   FROM Ticket_Status WHERE name = 'on offer' LIMIT 1;
	SELECT	status_id INTO sUnused  FROM Ticket_Status WHERE name = 'unused'   LIMIT 1;

	UPDATE	Ticket t
			JOIN Event e ON t.event_id = e.event_id
	SET		t.status_id = sUnused
	WHERE	CURDATE() > e.end_dt
		AND	t.status_id IN (sActive, sOffer);
END;
//
DELIMITER ;

-- ===========================================================
-- Procedure 2: Expire resale offers after event end
-- ===========================================================
DELIMITER //
CREATE PROCEDURE ExpireResaleOffers()
BEGIN
	DELETE	ro
	FROM	Resale_Offer ro
			JOIN Event e ON ro.event_id = e.event_id
	WHERE	CURDATE() > e.end_date;
END;
//
DELIMITER ;

-- ===========================================================
-- Procedure 3: Expire resale interests after event end
-- ===========================================================
DELIMITER //
CREATE PROCEDURE ExpireResaleInterests()
BEGIN
	DELETE	ri
	FROM	Resale_Interest ri
			JOIN Event e ON ri.event_id = e.event_id
	WHERE	CURDATE() > e.end_date;
END;
//
DELIMITER ;

-- ===========================================================
-- Procedure 4: Scan ticket at entrance (active → used)
-- ===========================================================
DELIMITER //
CREATE PROCEDURE ScanTicket(IN p_ean BIGINT)
BEGIN
	DECLARE v_status INT;
	DECLARE sActive INT;
	DECLARE sUsed INT;

	SELECT status_id INTO sActive FROM Ticket_Status WHERE name = 'active' LIMIT 1;
	SELECT status_id INTO sUsed   FROM Ticket_Status WHERE name = 'used'   LIMIT 1;

	SELECT status_id INTO v_status
	FROM   Ticket
	WHERE  ean_number = p_ean;

	IF v_status IS NULL THEN
		SIGNAL SQLSTATE '45000'
		SET MESSAGE_TEXT = 'Ticket not found.';
	ELSEIF v_status <> sActive THEN
		SIGNAL SQLSTATE '45000'
		SET MESSAGE_TEXT = 'Ticket already used or inactive.';
	ELSE
		UPDATE Ticket
		SET    status_id = sUsed
		WHERE  ean_number = p_ean;
	END IF;
END;
//
DELIMITER ;

-- ===========================================================
-- Procedure 5: Run maintenance (expire tickets/offers/interests)
-- ===========================================================
DELIMITER //
CREATE PROCEDURE RunMaintenance()
BEGIN
	CALL UpdateExpiredTickets();
	CALL ExpireResaleOffers();
	CALL ExpireResaleInterests();
END;
//
DELIMITER ;

-- ===========================================================
-- Procedure 7: Rename the currently connected user (self)
-- ===========================================================
DELIMITER //

CREATE PROCEDURE sp_rename_self(IN new_name VARCHAR(64))
SQL SECURITY DEFINER
BEGIN
	DECLARE cur_user VARCHAR(64);
	SET cur_user = SUBSTRING_INDEX(USER(), '@', 1);
	SET @sql = CONCAT(
    'ALTER USER `', cur_user, '`@''%'' RENAME TO `', new_name, '`@''%'';'
	);
	PREPARE stmt FROM @sql;
	EXECUTE stmt;
	DEALLOCATE PREPARE stmt;
END //

DELIMITER ;
