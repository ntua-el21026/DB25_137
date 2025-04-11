-- Drop and recreate the database
DROP DATABASE IF EXISTS pulse_university;
CREATE DATABASE pulse_university;
USE pulse_university;

-- Drop all tables
DROP TABLE IF EXISTS Continent;
DROP TABLE IF EXISTS Staff_Role;
DROP TABLE IF EXISTS Experience_Level;
DROP TABLE IF EXISTS Performance_Type;
DROP TABLE IF EXISTS Ticket_Type;
DROP TABLE IF EXISTS Payment_Method;
DROP TABLE IF EXISTS Ticket_Status;
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
DROP TABLE IF EXISTS Band;
DROP TABLE IF EXISTS Band_Member;
DROP TABLE IF EXISTS Performance_Band;
DROP TABLE IF EXISTS Performance_Artist;
DROP TABLE IF EXISTS Attendee;
DROP TABLE IF EXISTS Ticket;
DROP TABLE IF EXISTS Review;
DROP TABLE IF EXISTS Resale_Offer;
DROP TABLE IF EXISTS Resale_Interest_Request;
DROP TABLE IF EXISTS Resale_Interest_Type;

-- Lookup Tables
CREATE TABLE Continent (
    continent_id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL
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
    name VARCHAR(50) NOT NULL UNIQUE
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
    name VARCHAR(50) NOT NULL UNIQUE
);

INSERT INTO Experience_Level (name) VALUES
('intern'),
('beginner'),
('intermediate'),
('experienced'),
('expert');

CREATE TABLE Performance_Type (
    type_id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(50) NOT NULL UNIQUE
);

INSERT INTO Performance_Type (name) VALUES
('warm up'),
('headline'),
('special guest'),
('encore'),
('other');

CREATE TABLE Ticket_Type (
    type_id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(50) NOT NULL UNIQUE
);

INSERT INTO Ticket_Type (name) VALUES
('general'),
('VIP'),
('backstage'),
('early bird'),
('student');

CREATE TABLE Payment_Method (
    method_id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(50) NOT NULL UNIQUE
);

INSERT INTO Payment_Method (name) VALUES
('credit card'),
('debit card'),
('bank transfer');

CREATE TABLE Ticket_Status (
    status_id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(20) UNIQUE NOT NULL
);

INSERT INTO Ticket_Status (name) VALUES
('active'),
('used'),
('on offer');

-- Main Tables
CREATE TABLE Location (
    loc_id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    street_name VARCHAR(255) NOT NULL,
    street_number VARCHAR(20),
    zip_code VARCHAR(10),
    city VARCHAR(100) NOT NULL,
    country VARCHAR(100) NOT NULL,
    continent_id INT UNSIGNED NOT NULL,
    latitude DECIMAL(9,6),
    longitude DECIMAL(9,6),
    image VARCHAR(100) NOT NULL CHECK (image LIKE 'https://%'),
    caption VARCHAR(100) NOT NULL,
    FOREIGN KEY (continent_id) REFERENCES Continent(continent_id)
);

CREATE TABLE Festival (
    fest_year INT UNSIGNED PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    image VARCHAR(100) NOT NULL CHECK (image LIKE 'https://%'),
    caption VARCHAR(100) NOT NULL,
    loc_id INT UNSIGNED NOT NULL,
    FOREIGN KEY (loc_id) REFERENCES Location(loc_id)
);

CREATE TABLE Stage (
    stage_id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    capacity INT NOT NULL CHECK (capacity > 0),
    image VARCHAR(100) NOT NULL CHECK (image LIKE 'https://%'),
    caption VARCHAR(100) NOT NULL
);

CREATE TABLE Equipment (
    equip_id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    image VARCHAR(100) NOT NULL CHECK (image LIKE 'https://%'),
    caption VARCHAR(100) NOT NULL
);

CREATE TABLE Stage_Equipment (
    stage_id INT UNSIGNED,
    equip_id INT UNSIGNED,
    PRIMARY KEY(stage_id, equip_id),
    FOREIGN KEY(stage_id) REFERENCES Stage(stage_id),
    FOREIGN KEY(equip_id) REFERENCES Equipment(equip_id)
);

CREATE TABLE Event (
    event_id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    is_full BOOLEAN NOT NULL DEFAULT FALSE,
    image VARCHAR(100) NOT NULL CHECK (image LIKE 'https://%'),
    caption VARCHAR(100) NOT NULL,
    fest_year INT UNSIGNED NOT NULL,
    stage_id INT UNSIGNED NOT NULL,
    FOREIGN KEY(fest_year) REFERENCES Festival(fest_year),
    FOREIGN KEY(stage_id) REFERENCES Stage(stage_id)
);

CREATE TABLE Staff (
    staff_id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    date_of_birth DATE,
    role_id INT UNSIGNED NOT NULL,
    experience_id INT UNSIGNED NOT NULL,
    image VARCHAR(100) NOT NULL CHECK (image LIKE 'https://%'),
    caption VARCHAR(100) NOT NULL,
    FOREIGN KEY (role_id) REFERENCES Staff_Role(role_id),
    FOREIGN KEY (experience_id) REFERENCES Experience_Level(level_id)
);

CREATE TABLE Works_On (
    staff_id INT UNSIGNED,
    event_id INT UNSIGNED,
    PRIMARY KEY(staff_id, event_id),
    FOREIGN KEY(staff_id) REFERENCES Staff(staff_id),
    FOREIGN KEY(event_id) REFERENCES Event(event_id)
);

CREATE TABLE Performance (
    perf_id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    type_id INT UNSIGNED NOT NULL,
    datetime DATETIME NOT NULL,
    duration INT CHECK (duration <= 180),
    break_duration INT CHECK (break_duration BETWEEN 5 AND 30),
    stage_id INT UNSIGNED NOT NULL,
    event_id INT UNSIGNED NOT NULL,
    sequence_number INT NOT NULL CHECK (sequence_number > 0),
    FOREIGN KEY(type_id) REFERENCES Performance_Type(type_id),
    FOREIGN KEY(stage_id) REFERENCES Stage(stage_id),
    FOREIGN KEY(event_id) REFERENCES Event(event_id),
    UNIQUE(event_id, sequence_number)
);

CREATE TABLE Artist (
    artist_id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    nickname VARCHAR(100),
    date_of_birth DATE,
    main_genre VARCHAR(100),
    sub_genre VARCHAR(100),
    webpage TEXT,
    instagram TEXT,
    image VARCHAR(100) NOT NULL CHECK (image LIKE 'https://%'),
    caption VARCHAR(100) NOT NULL
);

CREATE TABLE Band (
    band_id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    formation_date DATE,
    main_genre VARCHAR(100),
    sub_genre VARCHAR(100),
    webpage VARCHAR(100) CHECK (webpage LIKE 'https://%'),
    instagram VARCHAR(100),
    image VARCHAR(100) NOT NULL CHECK (image LIKE 'https://%'),
    caption VARCHAR(100) NOT NULL
);

CREATE TABLE Band_Member (
    band_id INT UNSIGNED,
    artist_id INT UNSIGNED,
    PRIMARY KEY(band_id, artist_id),
    FOREIGN KEY(band_id) REFERENCES Band(band_id),
    FOREIGN KEY(artist_id) REFERENCES Artist(artist_id)
);

CREATE TABLE Performance_Band (
    perf_id INT UNSIGNED PRIMARY KEY,
    band_id INT UNSIGNED NOT NULL,
    FOREIGN KEY(perf_id) REFERENCES Performance(perf_id),
    FOREIGN KEY(band_id) REFERENCES Band(band_id)
);

CREATE TABLE Performance_Artist (
    perf_id INT UNSIGNED NOT NULL,
    artist_id INT UNSIGNED NOT NULL,
    PRIMARY KEY(perf_id, artist_id),
    FOREIGN KEY(perf_id) REFERENCES Performance(perf_id),
    FOREIGN KEY(artist_id) REFERENCES Artist(artist_id)
);

CREATE TABLE Attendee (
    attendee_id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    date_of_birth DATE,
    phone_number VARCHAR(20),
    email VARCHAR(255)
);

CREATE TABLE Ticket (
    ticket_id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    type_id INT UNSIGNED NOT NULL,
    purchase_date DATE,
    cost DECIMAL(10, 2),
    method_id INT UNSIGNED NOT NULL,
    ean_number BIGINT,
    status_id INT UNSIGNED NOT NULL,
    attendee_id INT UNSIGNED NOT NULL,
    event_id INT UNSIGNED NOT NULL,
    UNIQUE(attendee_id, event_id),
    FOREIGN KEY(type_id) REFERENCES Ticket_Type(type_id),
    FOREIGN KEY(status_id) REFERENCES Ticket_Status(status_id),
    FOREIGN KEY(method_id) REFERENCES Payment_Method(method_id),
    FOREIGN KEY(attendee_id) REFERENCES Attendee(attendee_id),
    FOREIGN KEY(event_id) REFERENCES Event(event_id)
);

CREATE TABLE Review (
    review_id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    interpretation TINYINT CHECK (interpretation BETWEEN 1 AND 5),
    sound_and_visuals TINYINT CHECK (sound_and_visuals BETWEEN 1 AND 5),
    stage_presence TINYINT CHECK (stage_presence BETWEEN 1 AND 5),
    organization TINYINT CHECK (organization BETWEEN 1 AND 5),
    overall TINYINT CHECK (overall BETWEEN 1 AND 5),
    attendee_id INT UNSIGNED NOT NULL,
    perf_id INT UNSIGNED NOT NULL,
    FOREIGN KEY(attendee_id) REFERENCES Attendee(attendee_id),
    FOREIGN KEY(perf_id) REFERENCES Performance(perf_id)
);

CREATE TABLE Resale_Offer (
    offer_id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    ticket_id INT UNSIGNED NOT NULL,
    event_id INT UNSIGNED NOT NULL,
    seller_id INT UNSIGNED NOT NULL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(ticket_id) REFERENCES Ticket(ticket_id),
    FOREIGN KEY(event_id) REFERENCES Event(event_id),
    FOREIGN KEY(seller_id) REFERENCES Attendee(attendee_id),
    UNIQUE(ticket_id)
);

CREATE TABLE Resale_Interest_Request (
    request_id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    buyer_id INT UNSIGNED NOT NULL,
    event_id INT UNSIGNED NOT NULL,
    expressed_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    fulfilled BOOLEAN DEFAULT FALSE,
    FOREIGN KEY(buyer_id) REFERENCES Attendee(attendee_id),
    FOREIGN KEY(event_id) REFERENCES Event(event_id),
    UNIQUE(buyer_id, event_id)
);

CREATE TABLE Resale_Interest_Type (
    request_id INT UNSIGNED NOT NULL,
    type_id INT UNSIGNED NOT NULL,
    PRIMARY KEY(request_id, type_id),
    FOREIGN KEY(request_id) REFERENCES Resale_Interest_Request(request_id) ON DELETE CASCADE,
    FOREIGN KEY(type_id) REFERENCES Ticket_Type(type_id)
);
