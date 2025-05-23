-- Drop and recreate the database
DROP DATABASE IF EXISTS pulse_university;
CREATE DATABASE IF NOT EXISTS pulse_university;
USE pulse_university;

-- Drop all tables
DROP TABLE IF EXISTS Continent;
DROP TABLE IF EXISTS Staff_Role;
DROP TABLE IF EXISTS Experience_Level;
DROP TABLE IF EXISTS Performance_Type;
DROP TABLE IF EXISTS Ticket_Type;
DROP TABLE IF EXISTS Payment_Method;
DROP TABLE IF EXISTS Ticket_Status;
DROP TABLE IF EXISTS Genre;
DROP TABLE IF EXISTS SubGenre;
DROP TABLE IF EXISTS Location;
DROP TABLE IF EXISTS Festival;
DROP TABLE IF EXISTS Stage;
DROP TABLE IF EXISTS Equipment;
DROP TABLE IF EXISTS Stage_Equipment;
DROP TABLE IF EXISTS Event;
DROP TABLE IF EXISTS Staff;
DROP TABLE IF EXISTS Works_On;
DROP TABLE IF EXISTS Performance;
DROP TABLE IF EXISTS Artist;
DROP TABLE IF EXISTS Artist_Genre;
DROP TABLE IF EXISTS Artist_SubGenre;
DROP TABLE IF EXISTS Band;
DROP TABLE IF EXISTS Band_Genre;
DROP TABLE IF EXISTS Band_SubGenre;
DROP TABLE IF EXISTS Band_Member;
DROP TABLE IF EXISTS Performance_Band;
DROP TABLE IF EXISTS Performance_Artist;
DROP TABLE IF EXISTS Attendee;
DROP TABLE IF EXISTS Ticket;
DROP TABLE IF EXISTS Review;
DROP TABLE IF EXISTS Resale_Offer;
DROP TABLE IF EXISTS Resale_Interest;
DROP TABLE IF EXISTS Resale_Interest_Type;
DROP TABLE IF EXISTS Resale_Match_Log;

-- Lookup Tables
CREATE TABLE Continent (
    continent_id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(50) NOT NULL UNIQUE,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

INSERT INTO Continent (name) VALUES
('Africa'),
('Asia'),
('Europe'),
('North America'),
('South America'),
('Oceania');

CREATE TABLE Staff_Role (
    role_id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(50) NOT NULL UNIQUE,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

INSERT INTO Staff_Role (name) VALUES
('security'),
('support'),
('sound engineer'),
('light technician'),
('stagehand'),
('medic'),
('cleaning'),
('backstage assistant');

CREATE TABLE Experience_Level (
    level_id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(50) NOT NULL UNIQUE,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

INSERT INTO Experience_Level (name) VALUES
('intern'),
('beginner'),
('intermediate'),
('experienced'),
('expert');

CREATE TABLE Performance_Type (
    type_id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(50) NOT NULL UNIQUE,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

INSERT INTO Performance_Type (name) VALUES
('warm up'),
('headline'),
('special guest'),
('encore'),
('other');

CREATE TABLE Ticket_Type (
    type_id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(50) NOT NULL UNIQUE,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

INSERT INTO Ticket_Type (name) VALUES
('general'),
('VIP'),
('backstage'),
('early bird'),
('student');

CREATE TABLE Payment_Method (
    method_id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(50) NOT NULL UNIQUE,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

INSERT INTO Payment_Method (name) VALUES
('credit card'),
('debit card'),
('bank transfer');

CREATE TABLE Ticket_Status (
    status_id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(20) NOT NULL UNIQUE,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

INSERT INTO Ticket_Status (name) VALUES
('active'),
('used'),
('on offer'),
('unused');

CREATE TABLE Genre (
    genre_id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE
);

INSERT INTO Genre (name) VALUES
('Rock'),
('Pop'),
('Jazz'),
('Hip Hop'),
('Electronic'),
('Classical'),
('Reggae'),
('Latin'),
('Metal'),
('Funk');

CREATE TABLE SubGenre (
    sub_genre_id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    genre_id INT UNSIGNED NOT NULL,
    FOREIGN KEY (genre_id) REFERENCES Genre(genre_id) ON DELETE CASCADE
);

INSERT INTO SubGenre (name, genre_id) VALUES
('Hard Rock',         (SELECT genre_id FROM Genre WHERE name='Rock')),
('Progressive Rock',  (SELECT genre_id FROM Genre WHERE name='Rock')),
('Punk Rock',         (SELECT genre_id FROM Genre WHERE name='Rock')),
('Synthpop',          (SELECT genre_id FROM Genre WHERE name='Pop')),
('Electropop',        (SELECT genre_id FROM Genre WHERE name='Pop')),
('Dance Pop',         (SELECT genre_id FROM Genre WHERE name='Pop')),
('Bebop',             (SELECT genre_id FROM Genre WHERE name='Jazz')),
('Smooth Jazz',       (SELECT genre_id FROM Genre WHERE name='Jazz')),
('Free Jazz',         (SELECT genre_id FROM Genre WHERE name='Jazz')),
('Trap',              (SELECT genre_id FROM Genre WHERE name='Hip Hop')),
('Boom Bap',          (SELECT genre_id FROM Genre WHERE name='Hip Hop')),
('Lo-fi Hip Hop',     (SELECT genre_id FROM Genre WHERE name='Hip Hop')),
('Techno',            (SELECT genre_id FROM Genre WHERE name='Electronic')),
('House',             (SELECT genre_id FROM Genre WHERE name='Electronic')),
('Trance',            (SELECT genre_id FROM Genre WHERE name='Electronic')),
('Baroque',           (SELECT genre_id FROM Genre WHERE name='Classical')),
('Romantic',          (SELECT genre_id FROM Genre WHERE name='Classical')),
('Contemporary Classical',(SELECT genre_id FROM Genre WHERE name='Classical')),
('Dub',               (SELECT genre_id FROM Genre WHERE name='Reggae')),
('Dancehall',         (SELECT genre_id FROM Genre WHERE name='Reggae')),
('Roots Reggae',      (SELECT genre_id FROM Genre WHERE name='Reggae')),
('Salsa',             (SELECT genre_id FROM Genre WHERE name='Latin')),
('Reggaeton',         (SELECT genre_id FROM Genre WHERE name='Latin')),
('Bachata',           (SELECT genre_id FROM Genre WHERE name='Latin')),
('Death Metal',       (SELECT genre_id FROM Genre WHERE name='Metal')),
('Black Metal',       (SELECT genre_id FROM Genre WHERE name='Metal')),
('Thrash Metal',      (SELECT genre_id FROM Genre WHERE name='Metal')),
('Afrofunk',          (SELECT genre_id FROM Genre WHERE name='Funk')),
('P-Funk',            (SELECT genre_id FROM Genre WHERE name='Funk')),
('Jazz-Funk',         (SELECT genre_id FROM Genre WHERE name='Funk'));

-- Main Tables
CREATE TABLE Location (
    loc_id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    street_name  VARCHAR(255) NOT NULL,
    street_number VARCHAR(20) NOT NULL,
    zip_code VARCHAR(10) NOT NULL,
    city VARCHAR(100) NOT NULL,
    country VARCHAR(100) NOT NULL,
    continent_id INT UNSIGNED NOT NULL,
    latitude  DECIMAL(9,6) NOT NULL,
    longitude DECIMAL(9,6) NOT NULL,
    image   VARCHAR(100) NOT NULL CHECK (image LIKE 'https://%'),
    caption VARCHAR(100) NOT NULL,
    FOREIGN KEY (continent_id) REFERENCES Continent(continent_id)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

CREATE TABLE Festival (
    fest_year INT UNSIGNED PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    start_date DATE NOT NULL,
    end_date   DATE NOT NULL,
    image   VARCHAR(100) NOT NULL CHECK (image LIKE 'https://%'),
    caption VARCHAR(100) NOT NULL,
    loc_id INT UNSIGNED NOT NULL,
    FOREIGN KEY (loc_id) REFERENCES Location(loc_id)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

CREATE TABLE Stage (
    stage_id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    name     VARCHAR(255) NOT NULL,
    capacity INT NOT NULL CHECK (capacity > 0),
    image   VARCHAR(100) NOT NULL CHECK (image LIKE 'https://%'),
    caption VARCHAR(100) NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

CREATE TABLE Equipment (
    equip_id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    name   VARCHAR(255) NOT NULL,
    image  VARCHAR(100) NOT NULL CHECK (image LIKE 'https://%'),
    caption VARCHAR(100) NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

CREATE TABLE Stage_Equipment (
    stage_id INT UNSIGNED,
    equip_id INT UNSIGNED,
    PRIMARY KEY(stage_id, equip_id),
    FOREIGN KEY(stage_id) REFERENCES Stage(stage_id)
        ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY(equip_id) REFERENCES Equipment(equip_id)
        ON DELETE CASCADE ON UPDATE CASCADE,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

CREATE TABLE Event (
    event_id  INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    title     VARCHAR(255) NOT NULL,
    is_full   BOOLEAN NOT NULL DEFAULT FALSE,
    start_dt  DATETIME NOT NULL,
    end_dt    DATETIME NOT NULL,
    image     VARCHAR(100) NOT NULL CHECK (image LIKE 'https://%'),
    caption   VARCHAR(100) NOT NULL,
    fest_year INT UNSIGNED NOT NULL,
    stage_id  INT UNSIGNED NOT NULL,
    generated_date DATE NOT NULL,                       -- updated via trigger
    UNIQUE KEY uq_event_stage (event_id, stage_id),
    UNIQUE KEY uq_start_date (generated_date),
    FOREIGN KEY (fest_year) REFERENCES Festival(fest_year)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    FOREIGN KEY (stage_id) REFERENCES Stage(stage_id)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

CREATE TABLE Staff (
    staff_id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    first_name VARCHAR(100) NOT NULL,
    last_name  VARCHAR(100) NOT NULL,
    date_of_birth DATE NOT NULL,
    role_id   INT UNSIGNED NOT NULL,
    experience_id INT UNSIGNED NOT NULL,
    image   VARCHAR(100) NOT NULL CHECK (image LIKE 'https://%'),
    caption VARCHAR(100) NOT NULL,
    FOREIGN KEY (role_id)      REFERENCES Staff_Role(role_id)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    FOREIGN KEY (experience_id) REFERENCES Experience_Level(level_id)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

CREATE TABLE Works_On (
    staff_id INT UNSIGNED,
    event_id INT UNSIGNED,
    PRIMARY KEY(staff_id, event_id),
    FOREIGN KEY(staff_id) REFERENCES Staff(staff_id)
        ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY(event_id) REFERENCES Event(event_id)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

CREATE TABLE Performance (
    perf_id  INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    type_id  INT UNSIGNED NOT NULL,
    datetime DATETIME NOT NULL,
    duration TINYINT UNSIGNED NOT NULL CHECK (duration BETWEEN 1 AND 180),
    break_duration TINYINT CHECK (break_duration BETWEEN 5 AND 30),
    stage_id INT UNSIGNED NOT NULL,
    event_id INT UNSIGNED NOT NULL,
    sequence_number TINYINT UNSIGNED NOT NULL CHECK (sequence_number > 0),
    UNIQUE KEY uq_event_seq (event_id, sequence_number),
    CONSTRAINT fk_perf_event_stage
        FOREIGN KEY (event_id, stage_id)
        REFERENCES Event(event_id, stage_id)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    FOREIGN KEY(stage_id) REFERENCES Stage(stage_id)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    FOREIGN KEY(type_id)  REFERENCES Performance_Type(type_id)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

CREATE TABLE Artist (
    artist_id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    first_name VARCHAR(100) NOT NULL,
    last_name  VARCHAR(100) NOT NULL,
    nickname   VARCHAR(100),
    date_of_birth DATE NOT NULL,
    webpage   VARCHAR(100) CHECK (webpage LIKE 'https://%'),
    instagram VARCHAR(100) CHECK (instagram LIKE '@%'),
    image   VARCHAR(100) NOT NULL CHECK (image LIKE 'https://%'),
    caption VARCHAR(100) NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

CREATE TABLE Artist_Genre (
    artist_id INT UNSIGNED,
    genre_id  INT UNSIGNED,
    PRIMARY KEY (artist_id, genre_id),
    FOREIGN KEY (artist_id) REFERENCES Artist(artist_id) ON DELETE CASCADE,
    FOREIGN KEY (genre_id)  REFERENCES Genre(genre_id)  ON DELETE CASCADE
);

CREATE TABLE Artist_SubGenre (
    artist_id INT UNSIGNED,
    sub_genre_id INT UNSIGNED,
    PRIMARY KEY (artist_id, sub_genre_id),
    FOREIGN KEY (artist_id)     REFERENCES Artist(artist_id) ON DELETE CASCADE,
    FOREIGN KEY (sub_genre_id)  REFERENCES SubGenre(sub_genre_id) ON DELETE CASCADE
);

CREATE TABLE Band (
    band_id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    formation_date DATE,
    webpage   VARCHAR(100) CHECK (webpage LIKE 'https://%'),
    instagram VARCHAR(100) CHECK (instagram LIKE '@%'),
    image   VARCHAR(100) NOT NULL CHECK (image LIKE 'https://%'),
    caption VARCHAR(100) NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

CREATE TABLE Band_Genre (
    band_id INT UNSIGNED,
    genre_id INT UNSIGNED,
    PRIMARY KEY (band_id, genre_id),
    FOREIGN KEY (band_id) REFERENCES Band(band_id)   ON DELETE CASCADE,
    FOREIGN KEY (genre_id) REFERENCES Genre(genre_id) ON DELETE CASCADE
);

CREATE TABLE Band_SubGenre (
    band_id INT UNSIGNED,
    sub_genre_id INT UNSIGNED,
    PRIMARY KEY (band_id, sub_genre_id),
    FOREIGN KEY (band_id)      REFERENCES Band(band_id)      ON DELETE CASCADE,
    FOREIGN KEY (sub_genre_id) REFERENCES SubGenre(sub_genre_id) ON DELETE CASCADE
);

CREATE TABLE Band_Member (
    band_id INT UNSIGNED,
    artist_id INT UNSIGNED,
    PRIMARY KEY(band_id, artist_id),
    FOREIGN KEY(band_id)  REFERENCES Band(band_id)
        ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY(artist_id) REFERENCES Artist(artist_id)
        ON DELETE CASCADE ON UPDATE CASCADE,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

CREATE TABLE Performance_Band (
    perf_id INT UNSIGNED PRIMARY KEY,
    band_id INT UNSIGNED NOT NULL,
    FOREIGN KEY(perf_id) REFERENCES Performance(perf_id)
        ON DELETE CASCADE ON UPDATE RESTRICT,
    FOREIGN KEY(band_id) REFERENCES Band(band_id)
        ON DELETE CASCADE ON UPDATE CASCADE,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

CREATE TABLE Performance_Artist (
    perf_id INT UNSIGNED,
    artist_id INT UNSIGNED,
    PRIMARY KEY(perf_id, artist_id),
    FOREIGN KEY(perf_id) REFERENCES Performance(perf_id)
        ON DELETE CASCADE ON UPDATE RESTRICT,
    FOREIGN KEY(artist_id) REFERENCES Artist(artist_id)
        ON DELETE CASCADE ON UPDATE CASCADE,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

CREATE TABLE Attendee (
    attendee_id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    first_name VARCHAR(100) NOT NULL,
    last_name  VARCHAR(100) NOT NULL,
    date_of_birth DATE NOT NULL,
    phone_number VARCHAR(20),
    email VARCHAR(255),
    CHECK (phone_number IS NOT NULL OR email IS NOT NULL),
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

CREATE TABLE Ticket (
    ticket_id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    type_id INT UNSIGNED NOT NULL,
    purchase_date DATE NOT NULL,
    cost DECIMAL(7,2) NOT NULL,
    method_id INT UNSIGNED NOT NULL,
    ean_number BIGINT NOT NULL UNIQUE,
    status_id INT UNSIGNED NOT NULL,
    attendee_id INT UNSIGNED NOT NULL,
    event_id INT UNSIGNED NOT NULL,
    UNIQUE(attendee_id, event_id),
    FOREIGN KEY(type_id) REFERENCES Ticket_Type(type_id)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    FOREIGN KEY(status_id) REFERENCES Ticket_Status(status_id)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    FOREIGN KEY(method_id) REFERENCES Payment_Method(method_id)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    FOREIGN KEY(attendee_id) REFERENCES Attendee(attendee_id)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    FOREIGN KEY(event_id) REFERENCES Event(event_id)
        ON DELETE RESTRICT  ON UPDATE CASCADE,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

CREATE TABLE Review (
    review_id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    interpretation     TINYINT NOT NULL CHECK (interpretation BETWEEN 1 AND 5),
    sound_and_visuals  TINYINT NOT NULL CHECK (sound_and_visuals BETWEEN 1 AND 5),
    stage_presence     TINYINT NOT NULL CHECK (stage_presence  BETWEEN 1 AND 5),
    organization       TINYINT NOT NULL CHECK (organization    BETWEEN 1 AND 5),
    overall            TINYINT NOT NULL CHECK (overall         BETWEEN 1 AND 5),
    attendee_id INT UNSIGNED NOT NULL,
    perf_id     INT UNSIGNED NOT NULL,
    UNIQUE(perf_id, attendee_id),
    FOREIGN KEY(attendee_id) REFERENCES Attendee(attendee_id)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    FOREIGN KEY(perf_id) REFERENCES Performance(perf_id)
        ON DELETE CASCADE  ON UPDATE RESTRICT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

CREATE TABLE Resale_Offer (
    offer_id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    ticket_id INT UNSIGNED NOT NULL UNIQUE,
    event_id  INT UNSIGNED NOT NULL,
    seller_id INT UNSIGNED NOT NULL,
    offer_timestamp DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(ticket_id) REFERENCES Ticket(ticket_id)
        ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY(event_id) REFERENCES Event(event_id)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    FOREIGN KEY(seller_id) REFERENCES Attendee(attendee_id)
        ON DELETE CASCADE ON UPDATE CASCADE,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

CREATE TABLE Resale_Interest (
    request_id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    buyer_id INT UNSIGNED NOT NULL,
    event_id INT UNSIGNED NOT NULL,
    interest_timestamp DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(buyer_id) REFERENCES Attendee(attendee_id)
        ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY(event_id) REFERENCES Event(event_id)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    UNIQUE(buyer_id, event_id),
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

CREATE TABLE Resale_Interest_Type (
    request_id INT UNSIGNED NOT NULL,
    type_id INT UNSIGNED NOT NULL,
    PRIMARY KEY(request_id, type_id),
    FOREIGN KEY(request_id) REFERENCES Resale_Interest(request_id)
        ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY(type_id) REFERENCES Ticket_Type(type_id)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

CREATE TABLE Resale_Match_Log (
    match_id           INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    match_type         ENUM('offer', 'interest') NOT NULL,
    ticket_id          INT UNSIGNED NOT NULL,
    offered_type_id    INT UNSIGNED NOT NULL,
    requested_type_id  INT UNSIGNED NOT NULL,
    buyer_id           INT UNSIGNED NOT NULL,
    seller_id          INT UNSIGNED NOT NULL,
    match_time         DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (ticket_id) REFERENCES Ticket(ticket_id)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    FOREIGN KEY (offered_type_id) REFERENCES Ticket_Type(type_id)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    FOREIGN KEY (requested_type_id) REFERENCES Ticket_Type(type_id)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    FOREIGN KEY (buyer_id) REFERENCES Attendee(attendee_id)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    FOREIGN KEY (seller_id) REFERENCES Attendee(attendee_id)
        ON DELETE RESTRICT ON UPDATE CASCADE
);
