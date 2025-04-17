----------------
--- Triggers ---
----------------

USE pulse_university;

-- Performance assignment constraints

-- Trigger 1: Ensure a solo performance has only one artist and no band
DELIMITER //
CREATE TRIGGER trg_solo_artist_limit
BEFORE INSERT ON Performance_Artist
FOR EACH ROW
BEGIN
	DECLARE artist_count INT;
	DECLARE band_count INT;

	SELECT COUNT(*) INTO artist_count
	FROM Performance_Artist
	WHERE perf_id = NEW.perf_id;

	SELECT COUNT(*) INTO band_count
	FROM Performance_Band
	WHERE perf_id = NEW.perf_id;

	IF artist_count >= 1 OR band_count > 0 THEN
		SIGNAL SQLSTATE '45000'
		SET MESSAGE_TEXT = 'A solo performance can only include one artist and not be mixed with a band.';
	END IF;
END;
//
DELIMITER ;

-- Trigger 2: Prevent assigning a band to a performance that already has artists
DELIMITER //
CREATE TRIGGER trg_no_band_if_artist_exists
BEFORE INSERT ON Performance_Band
FOR EACH ROW
BEGIN
	DECLARE artist_count INT;

	SELECT COUNT(*) INTO artist_count
	FROM Performance_Artist
	WHERE perf_id = NEW.perf_id;

	IF artist_count > 0 THEN
		SIGNAL SQLSTATE '45000'
		SET MESSAGE_TEXT = 'This performance already has artists. Cannot mix artist and band.';
	END IF;
END;
//
DELIMITER ;

-- Trigger 3: Ensure all artists in the same performance belong to the same band
DELIMITER //
CREATE TRIGGER trg_artists_must_share_band
BEFORE INSERT ON Performance_Artist
FOR EACH ROW
BEGIN
	DECLARE existing_artist INT;
	DECLARE shared_band_count INT;

	SELECT artist_id INTO existing_artist
	FROM Performance_Artist
	WHERE perf_id = NEW.perf_id
	LIMIT 1;

	IF existing_artist IS NOT NULL THEN
		SELECT COUNT(*) INTO shared_band_count
		FROM Band_Member bm1
			JOIN Band_Member bm2 ON bm1.band_id = bm2.band_id
		WHERE bm1.artist_id = NEW.artist_id
			AND bm2.artist_id = existing_artist;

		IF shared_band_count = 0 THEN
			SIGNAL SQLSTATE '45000'
			SET MESSAGE_TEXT = 'All artists in a performance must belong to the same band.';
		END IF;
	END IF;
END;
//
DELIMITER ;

-- Trigger 4: Prevent assigning an artist who already participates via their band
DELIMITER //
CREATE TRIGGER trg_artist_redundant_if_band_performing
BEFORE INSERT ON Performance_Artist
FOR EACH ROW
BEGIN
	DECLARE conflict_count INT;

	SELECT COUNT(*) INTO conflict_count
	FROM Performance_Band pb
		JOIN Band_Member bm ON pb.band_id = bm.band_id
	WHERE pb.perf_id = NEW.perf_id
		AND bm.artist_id = NEW.artist_id;

	IF conflict_count > 0 THEN
		SIGNAL SQLSTATE '45000'
		SET MESSAGE_TEXT = 'Artist is already participating via their band in this performance.';
	END IF;
END;
//
DELIMITER ;

-- Trigger 5: Prevent inserting an artist into a performance with a band unless they're a member
DELIMITER //
CREATE TRIGGER trg_artist_same_band
BEFORE INSERT ON Performance_Artist
FOR EACH ROW
BEGIN
	DECLARE perfBand INT;
	DECLARE memberCount INT;

	SELECT band_id INTO perfBand
	FROM Performance_Band
	WHERE perf_id = NEW.perf_id
	LIMIT 1;

	IF perfBand IS NOT NULL THEN
		SELECT COUNT(*) INTO memberCount
		FROM Band_Member
		WHERE band_id = perfBand
			AND artist_id = NEW.artist_id;

		IF memberCount = 0 THEN
			SIGNAL SQLSTATE '45000'
			SET MESSAGE_TEXT = 'Artist does not belong to the band performing in this performance.';
		END IF;
	END IF;
END;
//
DELIMITER ;

-- Trigger 6: Prevent an artist from being scheduled on two different stages at the same time
DELIMITER //
CREATE TRIGGER trg_no_double_stage_artist
BEFORE INSERT ON Performance_Artist
FOR EACH ROW
BEGIN
	DECLARE currentDate DATETIME;
	DECLARE currentStage INT;
	DECLARE conflictCount INT;

	SELECT datetime, stage_id INTO currentDate, currentStage
	FROM Performance
	WHERE perf_id = NEW.perf_id;

	SELECT COUNT(*) INTO conflictCount
	FROM Performance p
		JOIN Performance_Artist pa ON p.perf_id = pa.perf_id
	WHERE pa.artist_id = NEW.artist_id
		AND p.datetime = currentDate
		AND p.stage_id <> currentStage;

	IF conflictCount > 0 THEN
		SIGNAL SQLSTATE '45000'
		SET MESSAGE_TEXT = 'Artist already scheduled on another stage at the same time.';
	END IF;
END;
//
DELIMITER ;

-- Trigger 7: Prevent a band from being scheduled on two different stages at the same time
DELIMITER //
CREATE TRIGGER trg_no_double_stage_band
BEFORE INSERT ON Performance_Band
FOR EACH ROW
BEGIN
	DECLARE currentDate DATETIME;
	DECLARE currentStage INT;
	DECLARE conflictCount INT;

	SELECT datetime, stage_id INTO currentDate, currentStage
	FROM Performance
	WHERE perf_id = NEW.perf_id;

	SELECT COUNT(*) INTO conflictCount
	FROM Performance p
		JOIN Performance_Band pb ON p.perf_id = pb.perf_id
	WHERE pb.band_id = NEW.band_id
		AND p.datetime = currentDate
		AND p.stage_id <> currentStage;

	IF conflictCount > 0 THEN
		SIGNAL SQLSTATE '45000'
		SET MESSAGE_TEXT = 'Band already scheduled on another stage at the same time.';
	END IF;
END;
//
DELIMITER ;

-- Trigger 8: Prevent an artist from participating in more than 3 consecutive years
DELIMITER //
CREATE TRIGGER trg_max_consecutive_years_artist
BEFORE INSERT ON Performance_Artist
FOR EACH ROW
BEGIN
	DECLARE currentYear INT;
	DECLARE minYear INT;
	DECLARE maxYear INT;

	SELECT fest_year INTO currentYear
	FROM Event
	WHERE event_id = (
		SELECT event_id
		FROM Performance
		WHERE perf_id = NEW.perf_id
	);

	SELECT MIN(f.fest_year), MAX(f.fest_year)
	INTO minYear, maxYear
	FROM Performance p
		JOIN Performance_Artist pa ON p.perf_id = pa.perf_id
		JOIN Event e ON p.event_id = e.event_id
		JOIN Festival f ON e.fest_year = f.fest_year
	WHERE pa.artist_id = NEW.artist_id;

	IF (currentYear - COALESCE(minYear, currentYear)) >= 3
		OR (COALESCE(maxYear, currentYear) - currentYear) >= 3 THEN
		SIGNAL SQLSTATE '45000'
		SET MESSAGE_TEXT = 'Artist cannot participate in more than 3 consecutive years.';
	END IF;
END;
//
DELIMITER ;

-- Band membership and cleanup

-- Trigger 9: Delete a band when it has no members left
DELIMITER //
CREATE TRIGGER trg_delete_band_if_no_members
AFTER DELETE ON Band_Member
FOR EACH ROW
BEGIN
	DECLARE memberCount INT;

	SELECT COUNT(*) INTO memberCount
	FROM Band_Member
	WHERE band_id = OLD.band_id;

	IF memberCount = 0 THEN
		DELETE FROM Band
		WHERE band_id = OLD.band_id;
	END IF;
END;
//
DELIMITER ;

-- Staff requirements

-- Trigger 10: Ensure required security and support staff percentages are met for an event
DELIMITER //
CREATE TRIGGER trg_check_staff_percentages
AFTER INSERT ON Works_On
FOR EACH ROW
BEGIN
	DECLARE secCount INT;
	DECLARE supCount INT;
	DECLARE capacity INT;

	SELECT s.capacity INTO capacity
	FROM Event e
		JOIN Stage s ON e.stage_id = s.stage_id
	WHERE e.event_id = NEW.event_id;

	SELECT COUNT(*) INTO secCount
	FROM Works_On wo
		JOIN Staff st ON wo.staff_id = st.staff_id
	WHERE wo.event_id = NEW.event_id
		AND st.role_id = (
			SELECT role_id
			FROM Staff_Role
			WHERE name = 'security'
			LIMIT 1
		);

	SELECT COUNT(*) INTO supCount
	FROM Works_On wo
		JOIN Staff st ON wo.staff_id = st.staff_id
	WHERE wo.event_id = NEW.event_id
		AND st.role_id = (
			SELECT role_id
			FROM Staff_Role
			WHERE name = 'support'
			LIMIT 1
		);

	IF secCount < CEIL(capacity * 0.05) THEN
		SIGNAL SQLSTATE '45000'
		SET MESSAGE_TEXT = 'Not enough security staff assigned.';
	END IF;

	IF supCount < CEIL(capacity * 0.02) THEN
		SIGNAL SQLSTATE '45000'
		SET MESSAGE_TEXT = 'Not enough support staff assigned.';
	END IF;
END;
//
DELIMITER ;

-- Ticket expiration and status enforcement

-- Trigger 11: Auto-mark unused tickets as "on offer" after the event ends
DELIMITER //
CREATE TRIGGER trg_ticket_expiry
BEFORE UPDATE ON Ticket
FOR EACH ROW
BEGIN
	DECLARE eventEnd DATE;

	SELECT f.end_date INTO eventEnd
	FROM Festival f
		JOIN Event e ON f.fest_year = e.fest_year
	WHERE e.event_id = NEW.event_id;

	IF CURDATE() > eventEnd
		AND NEW.status_id <> (
			SELECT status_id
			FROM Ticket_Status
			WHERE name = 'used'
			LIMIT 1
		) THEN
		SET NEW.status_id = (
			SELECT status_id
			FROM Ticket_Status
			WHERE name = 'on offer'
			LIMIT 1
		);
	END IF;
END;
//
DELIMITER ;

-- Review constraints

-- Trigger 12: Only allow attendees to review performances they attended
DELIMITER //
CREATE TRIGGER trg_review_attendance
BEFORE INSERT ON Review
FOR EACH ROW
BEGIN
	DECLARE ticketCount INT;

	SELECT COUNT(*) INTO ticketCount
	FROM Ticket
	WHERE attendee_id = NEW.attendee_id
		AND event_id = (
			SELECT event_id
			FROM Performance
			WHERE perf_id = NEW.perf_id
		);

	IF ticketCount = 0 THEN
		SIGNAL SQLSTATE '45000'
		SET MESSAGE_TEXT = 'Attendee did not attend the performance.';
	END IF;
END;
//
DELIMITER ;

-- Resale constraints

-- Trigger 13: Prevent editing resale offer timestamp
DELIMITER //
CREATE TRIGGER trg_resale_offer_timestamp
BEFORE UPDATE ON Resale_Offer
FOR EACH ROW
BEGIN
	IF NEW.offer_timestamp <> OLD.offer_timestamp THEN
		SIGNAL SQLSTATE '45000'
		SET MESSAGE_TEXT = 'Resale offer timestamp cannot be modified.';
	END IF;
END;
//
DELIMITER ;

-- Trigger 14: Prevent editing resale interest timestamp
DELIMITER //
CREATE TRIGGER trg_resale_interest_timestamp
BEFORE UPDATE ON Resale_Interest
FOR EACH ROW
BEGIN
	IF NEW.interest_timestamp <> OLD.interest_timestamp THEN
		SIGNAL SQLSTATE '45000'
		SET MESSAGE_TEXT = 'Resale interest timestamp cannot be modified.';
	END IF;
END;
//
DELIMITER ;

-- Genre-subgenre validation

-- Trigger 15: Ensure artist subgenre belongs to an artist's genre
DELIMITER //
CREATE TRIGGER trg_artist_subgenre_consistency
BEFORE INSERT ON Artist_SubGenre
FOR EACH ROW
BEGIN
	DECLARE expectedGenre INT;
	DECLARE matchCount INT;

	SELECT genre_id INTO expectedGenre
	FROM SubGenre
	WHERE sub_genre_id = NEW.sub_genre_id;

	SELECT COUNT(*) INTO matchCount
	FROM Artist_Genre
	WHERE artist_id = NEW.artist_id
		AND genre_id = expectedGenre;

	IF matchCount = 0 THEN
		SIGNAL SQLSTATE '45000'
		SET MESSAGE_TEXT = 'Inconsistent subgenre for artist.';
	END IF;
END;
//
DELIMITER ;

-- Trigger 16: Ensure band subgenre belongs to a band's genre
DELIMITER //
CREATE TRIGGER trg_band_subgenre_consistency
BEFORE INSERT ON Band_SubGenre
FOR EACH ROW
BEGIN
	DECLARE expectedGenre INT;
	DECLARE matchCount INT;

	SELECT genre_id INTO expectedGenre
	FROM SubGenre
	WHERE sub_genre_id = NEW.sub_genre_id;

	SELECT COUNT(*) INTO matchCount
	FROM Band_Genre
	WHERE band_id = NEW.band_id
		AND genre_id = expectedGenre;

	IF matchCount = 0 THEN
		SIGNAL SQLSTATE '45000'
		SET MESSAGE_TEXT = 'Inconsistent subgenre for band.';
	END IF;
END;
//
DELIMITER ;

-- Attendee deletion cleanup

-- Trigger 17: Delete dependent records when an attendee is deleted
DELIMITER //
CREATE TRIGGER trg_delete_attendee_cleanup
AFTER DELETE ON Attendee
FOR EACH ROW
BEGIN
	DELETE FROM Ticket
	WHERE attendee_id = OLD.attendee_id;

	DELETE FROM Resale_Offer
	WHERE seller_id = OLD.attendee_id;

	DELETE FROM Resale_Interest
	WHERE buyer_id = OLD.attendee_id;

	DELETE FROM Review
	WHERE attendee_id = OLD.attendee_id;
END;
//
DELIMITER ;
