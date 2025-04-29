----------------
--- Triggers ---
----------------

USE pulse_university;

-- ===========================================================
-- 1. Performance-assignment rules (solo / band)
-- ===========================================================

-- Trigger 1: solo performance ⇒ one artist, no band
DELIMITER //
CREATE TRIGGER trg_solo_artist_limit
BEFORE INSERT ON Performance_Artist
FOR EACH ROW
BEGIN
	DECLARE a INT; DECLARE b INT;
	SELECT COUNT(*) INTO a FROM Performance_Artist WHERE perf_id = NEW.perf_id;
	SELECT COUNT(*) INTO b FROM Performance_Band   WHERE perf_id = NEW.perf_id;
	IF a >= 1 OR b > 0 THEN
		SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Solo performance already filled.';
	END IF;
END;
//
DELIMITER ;

-- Trigger 2: block band insert if artists already present
DELIMITER //
CREATE TRIGGER trg_no_band_if_artist_exists
BEFORE INSERT ON Performance_Band
FOR EACH ROW
BEGIN
	IF (SELECT COUNT(*) FROM Performance_Artist WHERE perf_id = NEW.perf_id) > 0 THEN
		SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Artists already assigned; cannot add band.';
	END IF;
END;
//
DELIMITER ;

-- Trigger 3: all artists in a performance must share the same band
DELIMITER //
CREATE TRIGGER trg_artists_must_share_band
BEFORE INSERT ON Performance_Artist
FOR EACH ROW
BEGIN
	DECLARE first_artist INT; DECLARE shared_cnt INT;
	SELECT artist_id INTO first_artist
	FROM   Performance_Artist
	WHERE  perf_id = NEW.perf_id
	LIMIT  1;

	IF first_artist IS NOT NULL THEN
		SELECT COUNT(*) INTO shared_cnt
		FROM   Band_Member bm1
		    	JOIN Band_Member bm2 ON bm1.band_id = bm2.band_id
		WHERE  bm1.artist_id = NEW.artist_id
			AND  bm2.artist_id = first_artist;

		IF shared_cnt = 0 THEN
			SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Artists do not belong to the same band.';
		END IF;
	END IF;
END;
//
DELIMITER ;

-- Trigger 4: prevent redundant artist if their band already performs
DELIMITER //
CREATE TRIGGER trg_artist_redundant_if_band_performing
BEFORE INSERT ON Performance_Artist
FOR EACH ROW
BEGIN
	IF EXISTS (
		SELECT 1
		FROM   Performance_Band pb
		    	JOIN Band_Member bm ON pb.band_id = bm.band_id
		WHERE  pb.perf_id   = NEW.perf_id
			AND  bm.artist_id = NEW.artist_id )
	THEN
		SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Artist already included through band.';
	END IF;
END;
//
DELIMITER ;

-- Trigger 5: artist added must belong to the performance’s band
DELIMITER //
CREATE TRIGGER trg_artist_same_band
BEFORE INSERT ON Performance_Artist
FOR EACH ROW
BEGIN
	DECLARE perfBand INT;
	SELECT band_id INTO perfBand
	FROM   Performance_Band
	WHERE  perf_id = NEW.perf_id
	LIMIT  1;

	IF perfBand IS NOT NULL
		AND NOT EXISTS (
			SELECT 1
			FROM   Band_Member
			WHERE  band_id   = perfBand
				AND  artist_id = NEW.artist_id )
	THEN
		SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Artist not a member of that band.';
	END IF;
END;
//
DELIMITER ;

-- ===========================================================
-- 2. Scheduling & participation (time / dates)
-- ===========================================================

-- Trigger 6: same artist cannot play two stages at the same time
DELIMITER //
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
//
DELIMITER ;

-- Trigger 7: same band cannot play two stages at the same time
DELIMITER //
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
//
DELIMITER ;

-- Trigger 8: one performance per stage at any moment (INSERT)
DELIMITER //
CREATE TRIGGER trg_no_stage_overlap
BEFORE INSERT ON Performance
FOR EACH ROW
BEGIN
	IF EXISTS (
		SELECT 1
		FROM   Performance
		WHERE  stage_id = NEW.stage_id
			AND  NEW.datetime <
		    	ADDDATE(datetime, INTERVAL duration MINUTE)
			AND  ADDDATE(NEW.datetime, INTERVAL NEW.duration MINUTE) > datetime )
	THEN
		SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Stage already booked for that time-slot.';
	END IF;
END;
//
DELIMITER ;

-- Trigger 9: artist max three consecutive festival years
DELIMITER //
CREATE TRIGGER trg_max_consecutive_years_artist
BEFORE INSERT ON Performance_Artist
FOR EACH ROW
BEGIN
	DECLARE y INT; DECLARE miny INT; DECLARE maxy INT;
	SELECT f.fest_year INTO y
	FROM   Performance p
	    	JOIN Event    e ON p.event_id = e.event_id
	    	JOIN Festival f ON e.fest_year = f.fest_year
	WHERE  p.perf_id = NEW.perf_id;

	SELECT MIN(f.fest_year), MAX(f.fest_year) INTO miny, maxy
	FROM   Performance p
	    	JOIN Performance_Artist pa ON p.perf_id = pa.perf_id
	    	JOIN Event    e ON p.event_id = e.event_id
	    	JOIN Festival f ON e.fest_year = f.fest_year
	WHERE  pa.artist_id = NEW.artist_id;

	IF (y - COALESCE(miny,y)) >= 3 OR (COALESCE(maxy,y) - y) >= 3 THEN
		SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Artist exceeds 3-year consecutive limit.';
	END IF;
END;
//
DELIMITER ;

-- Trigger 10: event window must lie inside festival dates
DELIMITER //
CREATE TRIGGER trg_event_within_festival_dates
BEFORE INSERT ON Event
FOR EACH ROW
BEGIN
	DECLARE s DATE; DECLARE e DATE;
	SELECT start_date, end_date INTO s, e
	FROM   Festival
	WHERE  fest_year = NEW.fest_year;

	IF DATE(NEW.start_dt) < s OR DATE(NEW.end_dt) > e THEN
		SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Event dates outside festival.';
	END IF;
END;
//
DELIMITER ;

-- Trigger 11: performance datetime must be inside festival
DELIMITER //
CREATE TRIGGER trg_performance_within_festival
BEFORE INSERT ON Performance
FOR EACH ROW
BEGIN
	DECLARE s DATE; DECLARE e DATE;
	SELECT f.start_date, f.end_date
	INTO   s, e
	FROM   Event ev
	    	JOIN Festival f ON ev.fest_year = f.fest_year
	WHERE  ev.event_id = NEW.event_id;

	IF NEW.datetime < s OR NEW.datetime > e THEN
		SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Performance outside festival dates.';
	END IF;
END;
//
DELIMITER ;

-- Trigger 12: performance must fit inside its parent event window
DELIMITER //
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
//
DELIMITER ;

-- Trigger 13: validate 5-30 min break (INSERT)
DELIMITER //
CREATE TRIGGER trg_validate_performance_break
BEFORE INSERT ON Performance
FOR EACH ROW
BEGIN
	IF NEW.sequence_number > 1 THEN
		DECLARE prevEnd DATETIME;
		SELECT ADDDATE(datetime, INTERVAL duration MINUTE)
		INTO   prevEnd
		FROM   Performance
		WHERE  event_id        = NEW.event_id
			AND  sequence_number = NEW.sequence_number - 1
		LIMIT  1;

		IF prevEnd IS NOT NULL
			AND TIMESTAMPDIFF(MINUTE, prevEnd, NEW.datetime) NOT BETWEEN 5 AND 30 THEN
			SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Break must be 5-30 minutes.';
		END IF;
	END IF;
END;
//
DELIMITER ;

-- Trigger 14: one performance per stage at any moment (UPDATE)
DELIMITER //
CREATE TRIGGER trg_no_stage_overlap_upd
BEFORE UPDATE ON Performance
FOR EACH ROW
BEGIN
	IF NEW.stage_id <> OLD.stage_id
		OR NEW.datetime <> OLD.datetime
		OR NEW.duration <> OLD.duration THEN
		IF EXISTS (
			SELECT 1
			FROM   Performance
			WHERE  stage_id = NEW.stage_id
				AND  perf_id <> NEW.perf_id
				AND  NEW.datetime <
			    	ADDDATE(datetime, INTERVAL duration MINUTE)
				AND  ADDDATE(NEW.datetime, INTERVAL NEW.duration MINUTE) > datetime )
		THEN
			SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Stage already booked for that time-slot.';
		END IF;
	END IF;
END;
//
DELIMITER ;

-- Trigger 15: validate 5-30 min break (UPDATE)
DELIMITER //
CREATE TRIGGER trg_validate_performance_break_upd
BEFORE UPDATE ON Performance
FOR EACH ROW
BEGIN
	IF NEW.sequence_number > 1
		AND (NEW.datetime <> OLD.datetime
	    	OR NEW.sequence_number <> OLD.sequence_number) THEN
		DECLARE prevEnd DATETIME;
		SELECT ADDDATE(datetime, INTERVAL duration MINUTE)
		INTO   prevEnd
		FROM   Performance
		WHERE  event_id        = NEW.event_id
			AND  sequence_number = NEW.sequence_number - 1
		LIMIT  1;

		IF prevEnd IS NOT NULL
			AND TIMESTAMPDIFF(MINUTE, prevEnd, NEW.datetime) NOT BETWEEN 5 AND 30 THEN
			SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Break must be 5-30 minutes.';
		END IF;
	END IF;
END;
//
DELIMITER ;

-- ===========================================================
-- 3. Band membership clean-up
-- ===========================================================

-- Trigger 16: delete band when it has no members
DELIMITER //
CREATE TRIGGER trg_delete_band_if_no_members
AFTER DELETE ON Band_Member
FOR EACH ROW
BEGIN
	IF (SELECT COUNT(*) FROM Band_Member WHERE band_id = OLD.band_id) = 0 THEN
		DELETE FROM Band WHERE band_id = OLD.band_id;
	END IF;
END;
//
DELIMITER ;

-- ===========================================================
-- 4. Staffing ratio (≥5 % security, ≥2 % support)
-- ===========================================================

-- Trigger 17: check ratios after INSERT on Works_On
DELIMITER //
CREATE TRIGGER trg_staff_ratio_after_insert
AFTER INSERT ON Works_On
FOR EACH ROW
BEGIN
	DECLARE rSec INT; DECLARE rSup INT; DECLARE vRole INT;
	SELECT role_id INTO rSec FROM Staff_Role WHERE name='security' LIMIT 1;
	SELECT role_id INTO rSup FROM Staff_Role WHERE name='support'  LIMIT 1;
	SELECT role_id INTO vRole FROM Staff WHERE staff_id = NEW.staff_id;

	IF vRole NOT IN (rSec, rSup) THEN
		CALL check_staff_ratio(NEW.event_id);
	END IF;
END;
//
DELIMITER ;

-- Trigger 18: check ratios after DELETE on Works_On
DELIMITER //
CREATE TRIGGER trg_staff_ratio_after_delete
AFTER DELETE ON Works_On
FOR EACH ROW
BEGIN
	CALL check_staff_ratio(OLD.event_id);
END;
//
DELIMITER ;

-- Trigger 19: check ratios after UPDATE on Works_On
DELIMITER //
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
//
DELIMITER ;

-- Helper procedure (used by triggers 17-19)
DELIMITER //
CREATE PROCEDURE check_staff_ratio(IN ev INT)
BEGIN
	DECLARE cap INT; DECLARE sec INT; DECLARE sup INT;
	SELECT s.capacity INTO cap
	FROM   Event e
	    	JOIN Stage s ON e.stage_id = s.stage_id
	WHERE  e.event_id = ev;

	SELECT COUNT(*) INTO sec
	FROM   Works_On wo
	    	JOIN Staff st ON wo.staff_id = st.staff_id
	WHERE  wo.event_id = ev
		AND  st.role_id  = (SELECT role_id FROM Staff_Role WHERE name='security' LIMIT 1);

	SELECT COUNT(*) INTO sup
	FROM   Works_On wo
	    	JOIN Staff st ON wo.staff_id = st.staff_id
	WHERE  wo.event_id = ev
		AND  st.role_id  = (SELECT role_id FROM Staff_Role WHERE name='support' LIMIT 1);

	IF sec < CEIL(cap*0.05) OR sup < CEIL(cap*0.02) THEN
		SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Staffing below required ratio.';
	END IF;
END;
//
DELIMITER ;

-- ===========================================================
-- 5. Ticket capacity / selling
-- ===========================================================

-- Trigger 20: block overselling (active + on offer)
DELIMITER //
CREATE TRIGGER trg_ticket_capacity_guard
BEFORE INSERT ON Ticket
FOR EACH ROW
BEGIN
	DECLARE cap INT; DECLARE sold INT;
	DECLARE sActive INT; DECLARE sOffer INT;
	SELECT status_id INTO sActive FROM Ticket_Status WHERE name='active'   LIMIT 1;
	SELECT status_id INTO sOffer  FROM Ticket_Status WHERE name='on offer' LIMIT 1;

	SELECT s.capacity INTO cap
	FROM   Event e
	    	JOIN Stage s ON e.stage_id = s.stage_id
	WHERE  e.event_id = NEW.event_id;

	SELECT COUNT(*) INTO sold
	FROM   Ticket
	WHERE  event_id = NEW.event_id
		AND  status_id IN (sActive, sOffer);

	IF sold >= cap THEN
		SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Capacity reached for this event.';
	END IF;
END;
//
DELIMITER ;

-- Trigger 21: mark event full when last seat sold
DELIMITER //
CREATE TRIGGER trg_mark_event_full
AFTER INSERT ON Ticket
FOR EACH ROW
BEGIN
	DECLARE cap INT; DECLARE sold INT;
	DECLARE sActive INT; DECLARE sOffer INT;
	SELECT status_id INTO sActive FROM Ticket_Status WHERE name='active'   LIMIT 1;
	SELECT status_id INTO sOffer  FROM Ticket_Status WHERE name='on offer' LIMIT 1;

	SELECT s.capacity INTO cap
	FROM   Event e
	    	JOIN Stage s ON e.stage_id = s.stage_id
	WHERE  e.event_id = NEW.event_id;

	SELECT COUNT(*) INTO sold
	FROM   Ticket
	WHERE  event_id = NEW.event_id
		AND  status_id IN (sActive, sOffer);

	IF sold >= cap THEN
		UPDATE Event SET is_full = TRUE WHERE event_id = NEW.event_id;
	END IF;
END;
//
DELIMITER ;

-- Trigger 22: VIP tickets ≤10 % of capacity
DELIMITER //
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
		AND  type_id  = vipType;

	IF NEW.type_id = vipType AND vip >= CEIL(cap*0.10) THEN
		SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'VIP ticket cap exceeded.';
	END IF;
END;
//
DELIMITER ;

-- ===========================================================
-- 6. Resale & ticket status
-- ===========================================================

-- Trigger 23: only ACTIVE tickets can be offered for resale
DELIMITER //
CREATE TRIGGER trg_resale_offer_only_active
BEFORE INSERT ON Resale_Offer
FOR EACH ROW
BEGIN
	IF (SELECT status_id FROM Ticket WHERE ticket_id = NEW.ticket_id) <>
		(SELECT status_id FROM Ticket_Status WHERE name='active' LIMIT 1) THEN
		SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Ticket not eligible for resale.';
	END IF;
END;
//
DELIMITER ;

-- Trigger 24: review allowed only with USED ticket
DELIMITER //
CREATE TRIGGER trg_review_only_with_used_ticket
BEFORE INSERT ON Review
FOR EACH ROW
BEGIN
	IF NOT EXISTS (
		SELECT 1
		FROM   Ticket t
		    	JOIN Performance p ON p.event_id = t.event_id
		WHERE  t.attendee_id = NEW.attendee_id
			AND  p.perf_id     = NEW.perf_id
			AND  t.status_id   = (SELECT status_id FROM Ticket_Status WHERE name='used' LIMIT 1) )
	THEN
		SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Must have USED ticket to review.';
	END IF;
END;
//
DELIMITER ;

-- Trigger 25: protect resale-offer timestamp
DELIMITER //
CREATE TRIGGER trg_resale_offer_timestamp
BEFORE UPDATE ON Resale_Offer
FOR EACH ROW
BEGIN
	IF NEW.offer_timestamp <> OLD.offer_timestamp THEN
		SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'offer_timestamp is immutable.';
	END IF;
END;
//
DELIMITER ;

-- Trigger 26: protect resale-interest timestamp
DELIMITER //
CREATE TRIGGER trg_resale_interest_timestamp
BEFORE UPDATE ON Resale_Interest
FOR EACH ROW
BEGIN
	IF NEW.interest_timestamp <> OLD.interest_timestamp THEN
		SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'interest_timestamp is immutable.';
	END IF;
END;
//
DELIMITER ;

-- ===========================================================
-- 7. Genre / sub-genre consistency
-- ===========================================================

-- Trigger 27: artist sub-genre must match an artist genre
DELIMITER //
CREATE TRIGGER trg_artist_subgenre_consistency
BEFORE INSERT ON Artist_SubGenre
FOR EACH ROW
BEGIN
	IF NOT EXISTS (
		SELECT 1
		FROM   SubGenre sg
		    	JOIN Artist_Genre ag ON ag.genre_id = sg.genre_id
		WHERE  sg.sub_genre_id = NEW.sub_genre_id
			AND  ag.artist_id   = NEW.artist_id )
	THEN
		SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Artist sub-genre inconsistent.';
	END IF;
END;
//
DELIMITER ;

-- Trigger 28: band sub-genre must match a band genre
DELIMITER //
CREATE TRIGGER trg_band_subgenre_consistency
BEFORE INSERT ON Band_SubGenre
FOR EACH ROW
BEGIN
	IF NOT EXISTS (
		SELECT 1
		FROM   SubGenre sg
		    	JOIN Band_Genre bg ON bg.genre_id = sg.genre_id
		WHERE  sg.sub_genre_id = NEW.sub_genre_id
			AND  bg.band_id     = NEW.band_id )
	THEN
		SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Band sub-genre inconsistent.';
	END IF;
END;
//
DELIMITER ;

-- ===========================================================
-- 8. Cascade clean-ups
-- ===========================================================

-- Trigger 29: delete attendee ⇒ purge tickets / resale / reviews
DELIMITER //
CREATE TRIGGER trg_delete_attendee_cleanup
AFTER DELETE ON Attendee
FOR EACH ROW
BEGIN
	DELETE FROM Ticket          WHERE attendee_id = OLD.attendee_id;
	DELETE FROM Resale_Offer    WHERE seller_id   = OLD.attendee_id;
	DELETE FROM Resale_Interest WHERE buyer_id    = OLD.attendee_id;
	DELETE FROM Review          WHERE attendee_id = OLD.attendee_id;
END;
//
DELIMITER ;
