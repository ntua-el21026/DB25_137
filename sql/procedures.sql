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

	SELECT	status_id INTO sActive  FROM Ticket_Status WHERE name='active'   LIMIT 1;
	SELECT	status_id INTO sOffer   FROM Ticket_Status WHERE name='on offer' LIMIT 1;
	SELECT	status_id INTO sUnused  FROM Ticket_Status WHERE name='unused'   LIMIT 1;

	UPDATE	Ticket t
			JOIN Event    e ON t.event_id = e.event_id
			JOIN Festival f ON e.fest_year = f.fest_year
	SET		t.status_id = sUnused
	WHERE	CURDATE() > f.end_date
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
			JOIN Event    e ON ro.event_id = e.event_id
			JOIN Festival f ON e.fest_year = f.fest_year
	WHERE	CURDATE() > f.end_date;
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
			JOIN Event    e ON ri.event_id = e.event_id
			JOIN Festival f ON e.fest_year = f.fest_year
	WHERE	CURDATE() > f.end_date;
END;
//
DELIMITER ;

-- ===========================================================
-- Procedure 4: Match one resale offer with the FIFO interest queue
--               (auto-sell ticket if buyer exists)
-- ===========================================================
DELIMITER //
CREATE PROCEDURE MatchResaleOffer(IN p_offer_id INT)
BEGIN
	DECLARE v_ticket     INT;	DECLARE v_event     INT;	DECLARE v_type   INT;
	DECLARE v_buyer      INT;	DECLARE v_interest  INT;
	DECLARE sActive INT;

	/* status id for 'active' */
	SELECT	status_id INTO sActive
	FROM	Ticket_Status
	WHERE	name = 'active'
	LIMIT	1;

	/* offer details */
	SELECT	t.ticket_id, t.event_id, t.type_id
	INTO	v_ticket,  v_event,    v_type
	FROM	Resale_Offer ro
			JOIN Ticket t ON ro.ticket_id = t.ticket_id
	WHERE	ro.offer_id = p_offer_id;

	/* find earliest matching interest (FIFO) */
	SELECT	ri.request_id, ri.buyer_id
	INTO	v_interest, v_buyer
	FROM	Resale_Interest ri
			JOIN Resale_Interest_Type rit ON ri.request_id = rit.request_id
	WHERE	ri.event_id      = v_event
		AND	ri.fulfilled    = FALSE
		AND	rit.type_id     = v_type
	ORDER BY ri.interest_timestamp
	LIMIT 1;

	/* if buyer found, perform transaction */
	IF v_buyer IS NOT NULL THEN

		/* transfer ticket */
		UPDATE	Ticket
		SET		attendee_id = v_buyer,
				status_id   = sActive        -- ensure ticket is active
		WHERE	ticket_id   = v_ticket;

		/* mark interest fulfilled & remove offer */
		UPDATE	Resale_Interest
		SET		fulfilled = TRUE
		WHERE	request_id = v_interest;

		DELETE FROM Resale_Offer WHERE offer_id = p_offer_id;
	END IF;
END;
//
DELIMITER ;

-- ===========================================================
-- Procedure 5: Scan ticket at entrance (active → used)
-- ===========================================================
DELIMITER //
CREATE PROCEDURE ScanTicket(IN p_ean BIGINT)
BEGIN
	DECLARE v_status INT;	DECLARE sActive INT;	DECLARE sUsed INT;

	SELECT	status_id INTO sActive FROM Ticket_Status WHERE name='active' LIMIT 1;
	SELECT	status_id INTO sUsed   FROM Ticket_Status WHERE name='used'   LIMIT 1;

	SELECT	status_id INTO v_status
	FROM	Ticket
	WHERE	ean_number = p_ean;

	IF v_status IS NULL THEN
		SIGNAL SQLSTATE '45000'
		SET MESSAGE_TEXT = 'Ticket not found.';
	ELSEIF v_status <> sActive THEN
		SIGNAL SQLSTATE '45000'
		SET MESSAGE_TEXT = 'Ticket already used or inactive.';
	ELSE
		UPDATE	Ticket
		SET		status_id = sUsed
		WHERE	ean_number = p_ean;
	END IF;
END;
//
DELIMITER ;

-- ===========================================================
-- Procedure 6: Run daily maintenance (expire tickets/offers/interests)
--               — schedule this once per night
-- ===========================================================
DELIMITER //
CREATE PROCEDURE RunDailyMaintenance()
BEGIN
	CALL UpdateExpiredTickets();
	CALL ExpireResaleOffers();
	CALL ExpireResaleInterests();
END;
//
DELIMITER ;
