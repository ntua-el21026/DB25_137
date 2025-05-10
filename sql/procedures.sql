-- --------------
-- Procedures --
-- --------------

USE pulse_university;

-- Drop all procedures
DROP PROCEDURE IF EXISTS UpdateExpiredTickets;
DROP PROCEDURE IF EXISTS ExpireResaleOffers;
DROP PROCEDURE IF EXISTS ExpireResaleInterests;
DROP PROCEDURE IF EXISTS ScanTicket;
DROP PROCEDURE IF EXISTS RunMaintenance;
DROP PROCEDURE IF EXISTS sp_rename_self;
DROP PROCEDURE IF EXISTS check_staff_ratio;

-- ===========================================================
-- Procedure 1: Update expired tickets (active / on offer → unused)
-- ===========================================================
CREATE PROCEDURE UpdateExpiredTickets()
BEGIN
    DECLARE sActive  INT;
    DECLARE sOffer   INT;
    DECLARE sUnused  INT;

    SELECT status_id INTO sActive  FROM Ticket_Status WHERE name = 'active'   LIMIT 1;
    SELECT status_id INTO sOffer   FROM Ticket_Status WHERE name = 'on offer' LIMIT 1;
    SELECT status_id INTO sUnused  FROM Ticket_Status WHERE name = 'unused'   LIMIT 1;

    UPDATE Ticket t
        JOIN Event e ON t.event_id = e.event_id
    SET t.status_id = sUnused
    WHERE CURDATE() > e.end_dt
    	AND t.status_id IN (sActive, sOffer);
END;

-- ===========================================================
-- Procedure 2: Expire resale offers after event end
-- ===========================================================
CREATE PROCEDURE ExpireResaleOffers()
BEGIN
    DELETE ro
    FROM   Resale_Offer ro
        	JOIN Event e ON ro.event_id = e.event_id
    WHERE  CURDATE() > e.end_dt;
END;

-- ===========================================================
-- Procedure 3: Expire resale interests after event end
-- ===========================================================
CREATE PROCEDURE ExpireResaleInterests()
BEGIN
    DELETE ri
    FROM   Resale_Interest ri
        	JOIN Event e ON ri.event_id = e.event_id
    WHERE  CURDATE() > e.end_dt;
END;

-- ===========================================================
-- Procedure 4: Scan ticket at entrance (active → used)
-- ===========================================================
CREATE PROCEDURE ScanTicket(IN p_ean BIGINT)
BEGIN
    DECLARE v_status INT;
    DECLARE sActive  INT;
    DECLARE sUsed    INT;

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

-- ========================================================================
-- Procedure 5: Run maintenance (expire tickets/offers/interests + ratios)
-- ========================================================================
CREATE PROCEDURE RunMaintenance()
BEGIN
    DECLARE done INT DEFAULT 0;
    DECLARE ev_id INT;

    -- cursor must be before handler
    DECLARE cur CURSOR FOR
        SELECT DISTINCT event_id FROM Works_On;

    -- handler after cursor
    DECLARE CONTINUE HANDLER FOR NOT FOUND SET done = 1;

    -- 1. Run expiration subprocedures
    CALL UpdateExpiredTickets();
    CALL ExpireResaleOffers();
    CALL ExpireResaleInterests();

    -- 2. Loop through all events to validate staff ratios
    OPEN cur;
    read_loop: LOOP
        FETCH cur INTO ev_id;
        IF done THEN
            LEAVE read_loop;
        END IF;

        BEGIN
            DECLARE ratio_error CONDITION FOR SQLSTATE '45000';
            DECLARE CONTINUE HANDLER FOR ratio_error
                SELECT CONCAT('⚠ Event ', ev_id, ' fails staff ratio check') AS warning;

            CALL check_staff_ratio(ev_id);
        END;
    END LOOP;
    CLOSE cur;
END;

-- ===========================================================
-- Procedure 6: Rename the currently connected user (self)
-- ===========================================================
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
END;

-- ===========================================================
-- Procedure 7: Check staff ratios (≥5% security, ≥2% support)
-- ===========================================================
DROP PROCEDURE IF EXISTS check_staff_ratio;
CREATE PROCEDURE check_staff_ratio(IN ev INT)
BEGIN
    DECLARE cap INT DEFAULT NULL;
    DECLARE sec INT;
    DECLARE sup INT;

    -- Get the capacity of the event's stage
    SELECT s.capacity INTO cap
    FROM   Event e
    JOIN   Stage s ON e.stage_id = s.stage_id
    WHERE  e.event_id = ev
    LIMIT 1;

    -- If event not found, raise error
    IF cap IS NULL THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Invalid event ID: no matching event found.';
    END IF;

    -- Count security staff
    SELECT COUNT(*) INTO sec
    FROM   Works_On wo
    JOIN   Staff st ON wo.staff_id = st.staff_id
    WHERE  wo.event_id = ev
        AND  st.role_id = (
        SELECT role_id FROM Staff_Role WHERE name = 'security' LIMIT 1
    );

    -- Count support staff
    SELECT COUNT(*) INTO sup
    FROM   Works_On wo
    JOIN   Staff st ON wo.staff_id = st.staff_id
    WHERE  wo.event_id = ev
        AND  st.role_id = (
        SELECT role_id FROM Staff_Role WHERE name = 'support' LIMIT 1
    );

    -- Check if staffing ratios are met
    IF sec < CEIL(cap * 0.05) OR sup < CEIL(cap * 0.02) THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Staffing below required ratio.';
    END IF;
END;
