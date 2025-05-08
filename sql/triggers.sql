-- --------------
-- - Triggers ---
-- --------------

USE pulse_university;

-- Drop all triggers
DROP TRIGGER IF EXISTS trg_band_validate_before_ins;
DROP TRIGGER IF EXISTS trg_band_sync_members_after_ins;
DROP TRIGGER IF EXISTS trg_artist_validate_before_ins;
DROP TRIGGER IF EXISTS trg_auto_assign_band_after_artist_ins;
DROP TRIGGER IF EXISTS trg_no_double_stage_artist;
DROP TRIGGER IF EXISTS trg_no_double_stage_band;
DROP TRIGGER IF EXISTS trg_no_stage_overlap;
DROP TRIGGER IF EXISTS trg_max_consecutive_years_artist;
DROP TRIGGER IF EXISTS trg_max_consecutive_years_band;
DROP TRIGGER IF EXISTS trg_event_within_festival_dates;
DROP TRIGGER IF EXISTS trg_performance_inside_event;
DROP TRIGGER IF EXISTS trg_safe_festival_date_update;
DROP TRIGGER IF EXISTS trg_safe_event_date_update;
DROP TRIGGER IF EXISTS trg_delete_band_if_no_members;
DROP TRIGGER IF EXISTS trg_staff_ratio_after_delete;
DROP TRIGGER IF EXISTS trg_staff_ratio_after_update;
DROP TRIGGER IF EXISTS trg_ticket_capacity_check;
DROP TRIGGER IF EXISTS trg_check_vip_ticket_limit;
DROP TRIGGER IF EXISTS trg_validate_ticket_ean;
DROP TRIGGER IF EXISTS trg_validate_ticket_ean_upd;
DROP TRIGGER IF EXISTS trg_resale_offer_only_active;
DROP TRIGGER IF EXISTS trg_review_only_with_used_ticket;
DROP TRIGGER IF EXISTS trg_resale_offer_timestamp;
DROP TRIGGER IF EXISTS trg_resale_interest_timestamp;
DROP TRIGGER IF EXISTS trg_stage_capacity_update;
DROP TRIGGER IF EXISTS trg_block_purchase_date_update;
DROP TRIGGER IF EXISTS trg_validate_ticket_purchase_date;
DROP TRIGGER IF EXISTS trg_artist_subgenre_consistency;
DROP TRIGGER IF EXISTS trg_band_subgenre_consistency;
DROP TRIGGER IF EXISTS trg_delete_attendee_cleanup;
DROP TRIGGER IF EXISTS trg_match_resale_interest;
DROP TRIGGER IF EXISTS trg_match_resale_offer;

-- ===========================================================
-- 1. Performance-assignment rules (solo / band)
-- ===========================================================

-- 1. BEFORE INSERT on Performance_Band – validate band insertion
CREATE TRIGGER trg_band_validate_before_ins
BEFORE INSERT ON Performance_Band
FOR EACH ROW
BEGIN
    -- 1.a  allow **only one** band per performance
    IF (SELECT COUNT(*) FROM Performance_Band WHERE perf_id = NEW.perf_id) > 0 THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'A band is already assigned to this performance.';
    END IF;

    -- 1.b  if artists already exist, they **must** belong to that band
    IF EXISTS (
        SELECT 1
        FROM   Performance_Artist pa
        WHERE  pa.perf_id = NEW.perf_id
            AND  pa.artist_id NOT IN
                (SELECT artist_id FROM Band_Member WHERE band_id = NEW.band_id)
    ) THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Existing artist is not a member of this band.';
    END IF;
END;

-- 2. AFTER INSERT on Performance_Band – auto‑insert every band member into Performance_Artist
CREATE TRIGGER trg_band_sync_members_after_ins
AFTER INSERT ON Performance_Band
FOR EACH ROW
BEGIN
    -- INSERT IGNORE avoids duplicates thanks to (perf_id,artist_id) PK
    INSERT IGNORE INTO Performance_Artist (perf_id, artist_id)
    SELECT NEW.perf_id, bm.artist_id
    FROM   Band_Member bm
    WHERE  bm.band_id = NEW.band_id;
END;

-- 3. BEFORE INSERT on Performance_Artist – validate artist insertion
CREATE TRIGGER trg_artist_validate_before_ins
BEFORE INSERT ON Performance_Artist
FOR EACH ROW
BEGIN
    -- 3.a  If a band is already set, artist must be a member
    DECLARE v_band INT;
    SELECT band_id INTO v_band
    FROM   Performance_Band
    WHERE  perf_id = NEW.perf_id
    LIMIT  1;

    IF v_band IS NOT NULL
        AND NOT EXISTS (
            SELECT 1
            FROM   Band_Member
            WHERE  band_id = v_band
                AND  artist_id = NEW.artist_id)
    THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Artist is not a member of the assigned band.';
    END IF;

    -- 3.b  If NO band yet, but other artists exist ⇒ they must all share at least one common band with the newcomer
    IF v_band IS NULL
        AND (SELECT COUNT(*) FROM Performance_Artist WHERE perf_id = NEW.perf_id) > 0
        AND NOT EXISTS (
            SELECT 1
            FROM   Band_Member bm_new                -- bands of the new artist
            WHERE  bm_new.artist_id = NEW.artist_id
                -- every existing artist must also be member of bm_new.band_id
                AND NOT EXISTS (
                    SELECT 1
                    FROM   Performance_Artist pa
                    WHERE  pa.perf_id = NEW.perf_id         -- existing artists
                        AND NOT EXISTS (
                            SELECT 1
                            FROM   Band_Member bm_old
                            WHERE  bm_old.band_id  = bm_new.band_id
                                AND  bm_old.artist_id = pa.artist_id))
        )
    THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Artists do not share a common band.';
    END IF;
END;

-- 4. AFTER INSERT on Performance_Artist – when every member of some band is now present
-- insert that band into Performance_Band (rule 5)
CREATE TRIGGER trg_auto_assign_band_after_artist_ins
AFTER INSERT ON Performance_Artist
FOR EACH ROW
BEGIN
    -- Only act if no band yet
    IF (SELECT COUNT(*) FROM Performance_Band WHERE perf_id = NEW.perf_id) = 0 THEN
        DECLARE target_band INT;

        --find a band of the new artist whose EVERY member is already in Performance_Artist for that performance
        SELECT bm.band_id INTO target_band
        FROM   Band_Member bm
        WHERE  bm.artist_id = NEW.artist_id
        GROUP BY bm.band_id
        HAVING COUNT(*) = (
                    SELECT COUNT(*)         -- #members of that band
                    FROM Band_Member
                    WHERE band_id = bm.band_id)
            AND  COUNT(*) = (               -- equals #artists on the stage
                    SELECT COUNT(DISTINCT artist_id)
                    FROM   Performance_Artist
                    WHERE  perf_id = NEW.perf_id)
        LIMIT 1;

        IF target_band IS NOT NULL THEN
            INSERT IGNORE INTO Performance_Band (perf_id, band_id)
            VALUES (NEW.perf_id, target_band);
        END IF;
    END IF;
END;

-- ===========================================================
-- 2. Scheduling & participation (time / dates)
-- ===========================================================

-- 5. Same artist cannot play two stages at the same time
CREATE TRIGGER trg_no_double_stage_artist
BEFORE INSERT ON Performance_Artist
FOR EACH ROW
BEGIN
	DECLARE d DATETIME; DECLARE s INT;
	SELECT datetime, stage_id INTO d, s FROM Performance WHERE perf_id = NEW.perf_id;
	IF EXISTS (
		SELECT 1
		FROM   Performance p
		    JOIN Performance_Artist pa ON p.perf_id = pa.perf_id
		WHERE  pa.artist_id = NEW.artist_id
			AND  p.datetime  = d
			AND  p.stage_id <> s )
	THEN
		SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Artist already on another stage at that time.';
	END IF;
END;

-- 6. Same band cannot play two stages at the same time
CREATE TRIGGER trg_no_double_stage_band
BEFORE INSERT ON Performance_Band
FOR EACH ROW
BEGIN
	DECLARE d DATETIME; DECLARE s INT;
	SELECT datetime, stage_id INTO d, s FROM Performance WHERE perf_id = NEW.perf_id;
	IF EXISTS (
		SELECT 1
		FROM   Performance p
		    JOIN Performance_Band pb ON p.perf_id = pb.perf_id
		WHERE  pb.band_id = NEW.band_id
			AND  p.datetime = d
			AND  p.stage_id <> s )
	THEN
		SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Band already on another stage at that time.';
	END IF;
END;

-- 7. One performance per stage at any moment on insert
CREATE TRIGGER trg_no_stage_overlap
BEFORE INSERT ON Performance
FOR EACH ROW
BEGIN
    IF EXISTS (
        SELECT 1
        FROM   Performance
        WHERE  stage_id = NEW.stage_id
            AND  perf_id <> NEW.perf_id
            AND  NEW.datetime < ADDDATE(datetime, INTERVAL duration MINUTE)
            AND  ADDDATE(NEW.datetime, INTERVAL NEW.duration MINUTE) > datetime
    ) THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Stage already booked for that time-slot.';
    END IF;
END;

-- 8. Check if an artist has performed for more than 3 consecutive years
CREATE TRIGGER trg_max_consecutive_years_artist
BEFORE INSERT ON Performance_Artist
FOR EACH ROW
BEGIN
    DECLARE y INT;

    -- Find the year for the new performance
    SELECT f.fest_year INTO y
    FROM   Performance p
        JOIN Event    e ON p.event_id = e.event_id
        JOIN Festival f ON e.fest_year = f.fest_year
    WHERE  p.perf_id = NEW.perf_id;

    -- Now check whether adding this year would cause 4+ consecutive years
    IF EXISTS (
        SELECT 1
        FROM (
            SELECT f.fest_year
            FROM   Performance p
                JOIN Performance_Artist pa ON p.perf_id = pa.perf_id
                JOIN Event    e ON p.event_id = e.event_id
                JOIN Festival f ON e.fest_year = f.fest_year
            WHERE  pa.artist_id = NEW.artist_id
            UNION
            SELECT y  -- include the new year
        ) AS all_years
        GROUP BY fest_year
        HAVING EXISTS (
            SELECT 1
            FROM (
                SELECT a1.fest_year + 1 AS y2, a1.fest_year + 2 AS y3, a1.fest_year + 3 AS y4
                FROM   (SELECT DISTINCT fest_year FROM all_years) a1
            ) AS seq
            WHERE seq.y2 IN (SELECT fest_year FROM all_years)
                AND seq.y3 IN (SELECT fest_year FROM all_years)
                AND seq.y4 IN (SELECT fest_year FROM all_years)
        )
    ) THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Artist exceeds 3-year consecutive limit.';
    END IF;
END;

-- 9. Check if any of the members of the band has performed for more than 3 consecutive years => don't insert the band
CREATE TRIGGER trg_max_consecutive_years_band
BEFORE INSERT ON Performance_Band
FOR EACH ROW
BEGIN
    DECLARE perf_year INT;

    -- 1. Get the year of the performance we're assigning the band to
    SELECT f.fest_year INTO perf_year
    FROM   Performance p
        JOIN Event e ON p.event_id = e.event_id
        JOIN Festival f ON e.fest_year = f.fest_year
    WHERE  p.perf_id = NEW.perf_id;

    -- 2. Now check each member:
    --    Would adding `perf_year` cause any artist to exceed 3 consecutive years?
    IF EXISTS (
        SELECT 1
        FROM Band_Member bm
        WHERE bm.band_id = NEW.band_id
            AND EXISTS (
                SELECT 1
                FROM (
                    SELECT f.fest_year
                    FROM Performance p2
                    JOIN Performance_Artist pa ON p2.perf_id = pa.perf_id
                    JOIN Event e ON p2.event_id = e.event_id
                    JOIN Festival f ON e.fest_year = f.fest_year
                    WHERE pa.artist_id = bm.artist_id
                    UNION
                    SELECT perf_year  -- simulate adding the new year
                ) AS all_years
                GROUP BY 1
                HAVING EXISTS (
                    SELECT 1
                    FROM (
                        SELECT a.fest_year + 1 AS y2, a.fest_year + 2 AS y3, a.fest_year + 3 AS y4
                        FROM (SELECT DISTINCT fest_year FROM all_years) a
                    ) AS seq
                    WHERE seq.y2 IN (SELECT fest_year FROM all_years)
                    AND seq.y3 IN (SELECT fest_year FROM all_years)
                    AND seq.y4 IN (SELECT fest_year FROM all_years)
                )
            )
    ) THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'One or more band members exceed 3-year consecutive limit.';
    END IF;
END;

-- 10. An event must start only in the days of the festival
CREATE TRIGGER trg_event_within_festival_dates
BEFORE INSERT ON Event
FOR EACH ROW
BEGIN
	DECLARE s DATE; DECLARE e DATE;
	SELECT start_date, end_date INTO s, e
	FROM   Festival
	WHERE  fest_year = NEW.fest_year;

	IF DATE(NEW.start_dt) < s OR DATE(NEW.start_dt) > e THEN
		SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Event dates outside festival.';
	END IF;
END;

-- 11. Performance must fit inside its parent event window
CREATE TRIGGER trg_performance_inside_event
BEFORE INSERT ON Performance
FOR EACH ROW
BEGIN
	DECLARE eStart DATETIME; DECLARE eEnd DATETIME;
	SELECT start_dt, end_dt INTO eStart, eEnd
	FROM   Event
	WHERE  event_id = NEW.event_id;

	IF NEW.datetime < eStart
		OR ADDDATE(NEW.datetime, INTERVAL NEW.duration MINUTE) > eEnd THEN
		SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Performance outside its event window.';
	END IF;
END;

-- 12. Allow change of dates of festival, only if events are still in bounds
CREATE TRIGGER trg_safe_festival_date_update
BEFORE UPDATE ON Festival
FOR EACH ROW
BEGIN
    -- Only run check if dates are changing
    IF NEW.start_date <> OLD.start_date OR NEW.end_date <> OLD.end_date THEN
        -- Block if any event for this festival falls outside new bounds
        IF EXISTS (
            SELECT 1
            FROM   Event
            WHERE  fest_year = NEW.fest_year
                AND (DATE(start_dt) < NEW.start_date OR DATE(start_dt) > NEW.end_date)
        ) THEN
            SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Cannot change festival dates: some events would be out of bounds.';
        END IF;
    END IF;
END;

-- 13. Allow change of dates of event, only if performances are still in bounds
CREATE TRIGGER trg_safe_event_date_update
BEFORE UPDATE ON Event
FOR EACH ROW
BEGIN
    -- Only proceed if event window changes
    IF NEW.start_dt <> OLD.start_dt OR NEW.end_dt <> OLD.end_dt THEN
        -- Block update if any performance starts before or ends after the new window
        IF EXISTS (
            SELECT 1
            FROM   Performance
            WHERE  event_id = NEW.event_id
                AND (
                    datetime < NEW.start_dt
               OR ADDTIME(datetime, SEC_TO_TIME(duration * 60)) > NEW.end_dt
                )
        ) THEN
            SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Cannot update event dates: some performances would fall outside the new window.';
        END IF;
    END IF;
END;

-- ===========================================================
-- 3. Band membership clean-up
-- ===========================================================

-- 14. Delete band when it has no members
CREATE TRIGGER trg_delete_band_if_no_members
AFTER DELETE ON Band_Member
FOR EACH ROW
BEGIN
    IF (SELECT COUNT(*) FROM Band_Member WHERE band_id = OLD.band_id) = 0 THEN
        DELETE FROM Band WHERE band_id = OLD.band_id;
    END IF;
END;

-- ===========================================================
-- 4. Staffing ratio (≥5 % security, ≥2 % support)
-- ===========================================================

-- 15. Check ratios after DELETE on Works_On
CREATE TRIGGER trg_staff_ratio_after_delete
AFTER DELETE ON Works_On
FOR EACH ROW
BEGIN
    CALL check_staff_ratio(OLD.event_id);
END;

-- 16. check ratios after UPDATE on Works_On
CREATE TRIGGER trg_staff_ratio_after_update
AFTER UPDATE ON Works_On
FOR EACH ROW
BEGIN
    IF OLD.event_id <> NEW.event_id THEN
        CALL check_staff_ratio(OLD.event_id);
        CALL check_staff_ratio(NEW.event_id);
    ELSE
        CALL check_staff_ratio(NEW.event_id);
    END IF;
END;

-- ===========================================================
-- 5. Ticket capacity / selling
-- ===========================================================

-- 17. Block overselling and mark event full (all statuses)
CREATE TRIGGER trg_ticket_capacity_check
BEFORE INSERT ON Ticket
FOR EACH ROW
BEGIN
    DECLARE cap INT;
    DECLARE sold INT;

    -- Capacity of event's stage
    SELECT s.capacity INTO cap
    FROM   Event e
    JOIN   Stage s ON e.stage_id = s.stage_id
    WHERE  e.event_id = NEW.event_id;

    -- Count all tickets for this event, regardless of status
    SELECT COUNT(*) INTO sold
    FROM   Ticket
    WHERE  event_id = NEW.event_id;

    -- Block if full
    IF sold >= cap THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Capacity reached for this event.';
    END IF;

    -- If this insert fills the event exactly, mark it as full
    IF sold + 1 = cap THEN
        UPDATE Event SET is_full = TRUE WHERE event_id = NEW.event_id;
    END IF;
END;

-- 18. VIP tickets ≤10 % of capacity
CREATE TRIGGER trg_check_vip_ticket_limit
BEFORE INSERT ON Ticket
FOR EACH ROW
BEGIN
    DECLARE cap INT; DECLARE vip INT; DECLARE vipType INT;

    SELECT type_id INTO vipType FROM Ticket_Type WHERE name='VIP' LIMIT 1;

    SELECT s.capacity INTO cap
    FROM   Event e
        	JOIN Stage s ON e.stage_id = s.stage_id
    WHERE  e.event_id = NEW.event_id;

    SELECT COUNT(*) INTO vip
    FROM   Ticket
    WHERE  event_id = NEW.event_id
    	AND type_id  = vipType;

    IF NEW.type_id = vipType AND vip >= CEIL(cap * 0.10) THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'VIP ticket cap exceeded.';
    END IF;
END;

-- 19. Confirm EAN format on insert
CREATE TRIGGER trg_validate_ticket_ean
BEFORE INSERT ON Ticket
FOR EACH ROW
BEGIN
    DECLARE ean_str CHAR(13);
    DECLARE sum INT DEFAULT 0;
    DECLARE i INT DEFAULT 1;
    DECLARE digit INT;
    DECLARE checksum INT;

    -- Convert to 13-digit string
    SET ean_str = LPAD(NEW.ean_number, 13, '0');

    -- Must be 13 numeric characters
    IF ean_str NOT REGEXP '^[0-9]{13}$' THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'EAN must be a 13-digit number.';
    END IF;

    -- Calculate EAN-13 checksum: use digits 1–12
    WHILE i <= 12 DO
        SET digit = CAST(SUBSTRING(ean_str, i, 1) AS UNSIGNED);
        SET sum = sum + digit * IF(MOD(i, 2) = 0, 3, 1);
        SET i = i + 1;
    END WHILE;

    SET checksum = (10 - (sum MOD 10)) MOD 10;

    -- Validate against 13th digit
    IF checksum <> CAST(SUBSTRING(ean_str, 13, 1) AS UNSIGNED) THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Invalid EAN-13 checksum.';
    END IF;
END;

-- 20. Confirm EAN format on update
CREATE TRIGGER trg_validate_ticket_ean_upd
BEFORE UPDATE ON Ticket
FOR EACH ROW
BEGIN
    DECLARE ean_str CHAR(13);
    DECLARE sum INT DEFAULT 0;
    DECLARE i INT DEFAULT 1;
    DECLARE digit INT;
    DECLARE checksum INT;

    -- Convert to 13-digit string
    SET ean_str = LPAD(NEW.ean_number, 13, '0');

    -- Must be 13 numeric characters
    IF ean_str NOT REGEXP '^[0-9]{13}$' THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'EAN must be a 13-digit number.';
    END IF;

    -- Calculate EAN-13 checksum: use digits 1–12
    WHILE i <= 12 DO
        SET digit = CAST(SUBSTRING(ean_str, i, 1) AS UNSIGNED);
        SET sum = sum + digit * IF(MOD(i, 2) = 0, 3, 1);
        SET i = i + 1;
    END WHILE;

    SET checksum = (10 - (sum MOD 10)) MOD 10;

    -- Validate against 13th digit
    IF checksum <> CAST(SUBSTRING(ean_str, 13, 1) AS UNSIGNED) THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Invalid EAN-13 checksum.';
    END IF;
END;

-- ===========================================================
-- 6. Resale & ticket status
-- ===========================================================

-- 21. Only ACTIVE tickets can be offered for resale
CREATE TRIGGER trg_resale_offer_only_active
BEFORE INSERT ON Resale_Offer
FOR EACH ROW
BEGIN
    IF (SELECT status_id FROM Ticket WHERE ticket_id = NEW.ticket_id) <>
    	(SELECT status_id FROM Ticket_Status WHERE name='active' LIMIT 1) THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Ticket not eligible for resale.';
    END IF;
END;

-- 22. Review allowed only with USED ticket
CREATE TRIGGER trg_review_only_with_used_ticket
BEFORE INSERT ON Review
FOR EACH ROW
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM   Ticket t
            	JOIN Performance p ON p.event_id = t.event_id
        WHERE  t.attendee_id = NEW.attendee_id
        	AND p.perf_id     = NEW.perf_id
        	AND t.status_id   = (SELECT status_id FROM Ticket_Status WHERE name='used' LIMIT 1)
    ) THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Must have USED ticket to review.';
    END IF;
END;

-- 23. Protect resale-offer timestamp
CREATE TRIGGER trg_resale_offer_timestamp
BEFORE UPDATE ON Resale_Offer
FOR EACH ROW
BEGIN
    IF NEW.offer_timestamp <> OLD.offer_timestamp THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'offer_timestamp is immutable.';
    END IF;
END;

--24. Protect resale-interest timestamp
CREATE TRIGGER trg_resale_interest_timestamp
BEFORE UPDATE ON Resale_Interest
FOR EACH ROW
BEGIN
    IF NEW.interest_timestamp <> OLD.interest_timestamp THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'interest_timestamp is immutable.';
    END IF;
END;

-- 25. Allow capacity to only be increased and mark full events as not full.
CREATE TRIGGER trg_stage_capacity_update
BEFORE UPDATE ON Stage
FOR EACH ROW
BEGIN
    -- 1. Block capacity decrease
    IF NEW.capacity < OLD.capacity THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Cannot decrease stage capacity.';
    END IF;

    -- 2. If capacity is increased, unmark full events on this stage
    IF NEW.capacity > OLD.capacity THEN
        UPDATE Event
        SET    is_full = FALSE
        WHERE  stage_id = NEW.stage_id
            AND  is_full = TRUE;
    END IF;
END;

-- 26. Prevent purchase data of ticket to change
CREATE TRIGGER trg_block_purchase_date_update
BEFORE UPDATE ON Ticket
FOR EACH ROW
BEGIN
    IF NEW.purchase_date <> OLD.purchase_date THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'purchase_date cannot be modified after insertion.';
    END IF;
END;

-- 27. Prevent ticket to be purchased after the starte date of the event
CREATE TRIGGER trg_validate_ticket_purchase_date
BEFORE INSERT ON Ticket
FOR EACH ROW
BEGIN
    DECLARE ev_start DATETIME;

    SELECT start_dt INTO ev_start
    FROM   Event
    WHERE  event_id = NEW.event_id;

    IF NEW.purchase_date >= ev_start THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Ticket must be purchased before the event starts.';
    END IF;
END;

-- ===========================================================
-- 7. Genre / sub-genre consistency
-- ===========================================================

-- 28. Artist sub-genre must match an artist genre
CREATE TRIGGER trg_artist_subgenre_consistency
BEFORE INSERT ON Artist_SubGenre
FOR EACH ROW
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM   SubGenre sg
            	JOIN Artist_Genre ag ON ag.genre_id = sg.genre_id
        WHERE  sg.sub_genre_id = NEW.sub_genre_id
        	AND ag.artist_id    = NEW.artist_id
    ) THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Artist sub-genre inconsistent.';
    END IF;
END;

-- 29. Band sub-genre must match a band genre
CREATE TRIGGER trg_band_subgenre_consistency
BEFORE INSERT ON Band_SubGenre
FOR EACH ROW
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM   SubGenre sg
            	JOIN Band_Genre bg ON bg.genre_id = sg.genre_id
        WHERE  sg.sub_genre_id = NEW.sub_genre_id
        	AND bg.band_id      = NEW.band_id
    ) THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Band sub-genre inconsistent.';
    END IF;
END;

-- ===========================================================
-- 8. Cascade clean-ups
-- ===========================================================

-- 30. Delete attendee ⇒ purge tickets / resale / reviews
CREATE TRIGGER trg_delete_attendee_cleanup
AFTER DELETE ON Attendee
FOR EACH ROW
BEGIN
    DELETE FROM Ticket          WHERE attendee_id = OLD.attendee_id;
    DELETE FROM Resale_Offer    WHERE seller_id   = OLD.attendee_id;
    DELETE FROM Resale_Interest WHERE buyer_id    = OLD.attendee_id;
    DELETE FROM Review          WHERE attendee_id = OLD.attendee_id;
END;

-- ===========================================================
-- 9. Auto-match offers 
-- ===========================================================

-- 31. Match one resale interest with the FIFO offer queue (auto-buy ticket if seller exists)
CREATE TRIGGER trg_match_resale_interest
AFTER INSERT ON Resale_Interest
FOR EACH ROW
BEGIN
    DECLARE v_event  INT;
    DECLARE v_type   INT;
    DECLARE v_ticket INT;
    DECLARE v_buyer  INT;
    DECLARE v_offer  INT;
    DECLARE v_seller INT;
    DECLARE sActive  INT;

    -- status id for 'active'
    SELECT status_id INTO sActive
    FROM   Ticket_Status
    WHERE  name = 'active'
    LIMIT  1;

    -- interest details
    SET v_event = NEW.event_id;
    SET v_buyer = NEW.buyer_id;

    -- find earliest matching offer (FIFO)
    SELECT ro.offer_id, ro.ticket_id, t.type_id, ro.seller_id
    INTO   v_offer, v_ticket, v_type, v_seller
    FROM   Resale_Interest_Type rit
            JOIN Ticket       t  ON t.type_id    = rit.type_id
            JOIN Resale_Offer ro ON ro.ticket_id = t.ticket_id
    WHERE  rit.request_id = NEW.request_id
        AND  ro.event_id    = v_event
    ORDER BY ro.offer_timestamp
    LIMIT 1;

    -- if offer found, perform transaction
    IF v_offer IS NOT NULL THEN

        -- transfer ticket
        UPDATE Ticket
        SET     attendee_id = v_buyer,
                status_id   = sActive        -- ensure ticket is active
        WHERE  ticket_id   = v_ticket;

        -- remove offer and interest
        DELETE FROM Resale_Offer    WHERE offer_id   = v_offer;
        DELETE FROM Resale_Interest WHERE request_id = NEW.request_id;

        -- log match
        INSERT INTO Resale_Match_Log (match_type, ticket_id, buyer_id, seller_id)
        VALUES ('interest', v_ticket, v_buyer, v_seller);
    END IF;
END;

-- 32. Match one resale offer with the FIFO interest queue (auto-sell ticket if buyer exists)
CREATE TRIGGER trg_match_resale_offer
AFTER INSERT ON Resale_Offer
FOR EACH ROW
BEGIN
    DECLARE v_ticket   INT;
    DECLARE v_event    INT;
    DECLARE v_type     INT;
    DECLARE v_buyer    INT;
    DECLARE v_interest INT;
    DECLARE sActive    INT;

    -- status id for 'active'
    SELECT status_id INTO sActive
    FROM   Ticket_Status
    WHERE  name = 'active'
    LIMIT  1;

    -- offer details
    SELECT t.ticket_id, t.event_id, t.type_id
    INTO   v_ticket, v_event, v_type
    FROM   Ticket t
    WHERE  t.ticket_id = NEW.ticket_id;

    -- find earliest matching interest (FIFO)
    SELECT ri.request_id, ri.buyer_id
    INTO   v_interest, v_buyer
    FROM   Resale_Interest ri
            JOIN Resale_Interest_Type rit ON ri.request_id = rit.request_id
    WHERE  ri.event_id  = v_event
        AND  rit.type_id  = v_type
    ORDER BY ri.interest_timestamp
    LIMIT 1;

    -- if buyer found, perform transaction
    IF v_buyer IS NOT NULL THEN

        -- transfer ticket
        UPDATE Ticket
        SET     attendee_id = v_buyer,
                status_id   = sActive        -- ensure ticket is active
        WHERE  ticket_id   = v_ticket;

        -- remove interest and offer
        DELETE FROM Resale_Offer    WHERE offer_id   = NEW.offer_id;
        DELETE FROM Resale_Interest WHERE request_id = v_interest;

        -- log match
        INSERT INTO Resale_Match_Log (match_type, ticket_id, buyer_id, seller_id)
        VALUES ('offer', v_ticket, v_buyer, NEW.seller_id);
    END IF;
END;
