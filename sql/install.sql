-- Drop and recreate the database
DROP DATABASE IF EXISTS pulse_festival;
CREATE DATABASE pulse_festival;
USE pulse_festival;

-- Lookup Tables
CREATE TABLE Staff_Role (
    role_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(50) NOT NULL UNIQUE
);

INSERT INTO Staff_Role (name) VALUES
('technical'),
('security'),
('support');

CREATE TABLE Experience_Level (
    level_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(50) NOT NULL UNIQUE
);

INSERT INTO Experience_Level (name) VALUES
('intern'),
('beginner'),
('intermediate'),
('experienced'),
('expert');

CREATE TABLE Performance_Type (
    type_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(50) NOT NULL UNIQUE
);

INSERT INTO Performance_Type (name) VALUES
('warm up'),
('headline'),
('special guest'),
('other');

CREATE TABLE Ticket_Type (
    type_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(50) NOT NULL UNIQUE
);

INSERT INTO Ticket_Type (name) VALUES
('general'),
('VIP'),
('backstage');

CREATE TABLE Payment_Method (
    method_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(50) NOT NULL UNIQUE
);

INSERT INTO Payment_Method (name) VALUES
('credit card'),
('debit card'),
('bank transfer');

CREATE TABLE Queue_Action (
    action_type_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(50) NOT NULL UNIQUE
);

INSERT INTO Queue_Action (name) VALUES
('buy'),
('sell');

-- Main Tables
CREATE TABLE Location (
    loc_id INT AUTO_INCREMENT PRIMARY KEY,
    street_name VARCHAR(255) NOT NULL,
    street_number VARCHAR(20),
    zip_code VARCHAR(10),
    city VARCHAR(100) NOT NULL,
    country VARCHAR(100) NOT NULL,
    continent VARCHAR(100),
    latitude DECIMAL(9,6),
    longitude DECIMAL(9,6),
    image TEXT,
    caption TEXT
);

CREATE TABLE Festival (
    fest_year INT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    image TEXT,
    caption TEXT,
    loc_id INT NOT NULL,
    FOREIGN KEY (loc_id) REFERENCES Location(loc_id)
);

CREATE TABLE Stage (
    stage_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    capacity INT NOT NULL CHECK (capacity > 0),
    image TEXT,
    caption TEXT
);

CREATE TABLE Equipment (
    equip_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    image TEXT,
    caption TEXT
);

CREATE TABLE Stage_Equipment (
    stage_id INT,
    equip_id INT,
    PRIMARY KEY(stage_id, equip_id),
    FOREIGN KEY(stage_id) REFERENCES Stage(stage_id),
    FOREIGN KEY(equip_id) REFERENCES Equipment(equip_id)
);

CREATE TABLE Event (
    event_id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    is_full BOOLEAN NOT NULL DEFAULT FALSE,
    image TEXT,
    caption TEXT,
    fest_year INT NOT NULL,
    stage_id INT NOT NULL,
    FOREIGN KEY(fest_year) REFERENCES Festival(fest_year),
    FOREIGN KEY(stage_id) REFERENCES Stage(stage_id)
);

CREATE TABLE Staff (
    staff_id INT AUTO_INCREMENT PRIMARY KEY,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    age INT CHECK (age > 0),
    role_id INT NOT NULL,
    level_id INT NOT NULL,
    image TEXT,
    caption TEXT,
    FOREIGN KEY (role_id) REFERENCES Staff_Role(role_id),
    FOREIGN KEY (level_id) REFERENCES Experience_Level(level_id)
);

CREATE TABLE Works_On (
    staff_id INT,
    event_id INT,
    PRIMARY KEY(staff_id, event_id),
    FOREIGN KEY(staff_id) REFERENCES Staff(staff_id),
    FOREIGN KEY(event_id) REFERENCES Event(event_id)
);

CREATE TABLE Performance (
    perf_id INT AUTO_INCREMENT PRIMARY KEY,
    type_id INT NOT NULL,
    datetime DATETIME NOT NULL,
    duration INT CHECK (duration <= 180),
    break_duration INT CHECK (break_duration BETWEEN 5 AND 30),
    stage_id INT NOT NULL,
    event_id INT NOT NULL,
    FOREIGN KEY(type_id) REFERENCES Performance_Type(type_id),
    FOREIGN KEY(stage_id) REFERENCES Stage(stage_id),
    FOREIGN KEY(event_id) REFERENCES Event(event_id)
);

CREATE TABLE Artist (
    artist_id INT AUTO_INCREMENT PRIMARY KEY,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    nickname VARCHAR(100),
    date_of_birth DATE,
    main_genre VARCHAR(100),
    sub_genre VARCHAR(100),
    webpage TEXT,
    instagram TEXT,
    image TEXT,
    caption TEXT
);

CREATE TABLE Band (
    band_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    formation_date DATE,
    main_genre VARCHAR(100),
    sub_genre VARCHAR(100),
    webpage TEXT,
    instagram TEXT,
    image TEXT,
    caption TEXT
);

CREATE TABLE Band_Member (
    band_id INT,
    artist_id INT,
    PRIMARY KEY(band_id, artist_id),
    FOREIGN KEY(band_id) REFERENCES Band(band_id),
    FOREIGN KEY(artist_id) REFERENCES Artist(artist_id)
);

CREATE TABLE Performance_Band (
    perf_id INT PRIMARY KEY,
    band_id INT NOT NULL,
    FOREIGN KEY(perf_id) REFERENCES Performance(perf_id),
    FOREIGN KEY(band_id) REFERENCES Band(band_id)
);

CREATE TABLE Performance_Artist (
    perf_id INT NOT NULL,
    artist_id INT NOT NULL,
    PRIMARY KEY(perf_id, artist_id),
    FOREIGN KEY(perf_id) REFERENCES Performance(perf_id),
    FOREIGN KEY(artist_id) REFERENCES Artist(artist_id)
);

CREATE TABLE Attendee (
    attendee_id INT AUTO_INCREMENT PRIMARY KEY,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    age INT,
    phone_number VARCHAR(20),
    email VARCHAR(255)
);

CREATE TABLE Ticket (
    ticket_id INT AUTO_INCREMENT PRIMARY KEY,
    type_id INT NOT NULL,
    purchase_date DATE,
    cost DECIMAL(10, 2),
    method_id INT NOT NULL,
    ean_number BIGINT,
    is_used BOOLEAN DEFAULT FALSE,
    on_offer BOOLEAN DEFAULT FALSE,
    attendee_id INT NOT NULL,
    event_id INT NOT NULL,
    UNIQUE(attendee_id, event_id),
    FOREIGN KEY(type_id) REFERENCES Ticket_Type(type_id),
    FOREIGN KEY(method_id) REFERENCES Payment_Method(method_id),
    FOREIGN KEY(attendee_id) REFERENCES Attendee(attendee_id),
    FOREIGN KEY(event_id) REFERENCES Event(event_id)
);

CREATE TABLE Review (
    review_id INT AUTO_INCREMENT PRIMARY KEY,
    artist_id INT NOT NULL,
    sound_and_visuals TINYINT CHECK (sound_and_visuals BETWEEN 1 AND 5),
    stage_presence TINYINT CHECK (stage_presence BETWEEN 1 AND 5),
    organization TINYINT CHECK (organization BETWEEN 1 AND 5),
    overall TINYINT CHECK (overall BETWEEN 1 AND 5),
    attendee_id INT NOT NULL,
    perf_id INT NOT NULL,
    FOREIGN KEY(attendee_id) REFERENCES Attendee(attendee_id),
    FOREIGN KEY(perf_id) REFERENCES Performance(perf_id),
    FOREIGN KEY(artist_id) REFERENCES Artist(artist_id)
);

-- Revised Resale Queue
-- A ticket must appear at most once in the resale queue at any time.
CREATE TABLE Resale_Queue (
    queue_id INT AUTO_INCREMENT PRIMARY KEY,
    action_type_id INT NOT NULL,
    ticket_id INT NOT NULL,
    event_id INT NOT NULL,
    seller_id INT NOT NULL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(action_type_id) REFERENCES Queue_Action(action_type_id),
    FOREIGN KEY(ticket_id) REFERENCES Ticket(ticket_id),
    FOREIGN KEY(event_id) REFERENCES Event(event_id),
    FOREIGN KEY(seller_id) REFERENCES Attendee(attendee_id),
    UNIQUE(ticket_id)
);

-- Model many buyers interested in a resale item.
-- An attendee (buyer) can appear on multiple queues (for different events).
CREATE TABLE Resale_Queue_Interest (
    queue_id INT NOT NULL,
    buyer_id INT NOT NULL,
    expressed_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY(queue_id, buyer_id),
    FOREIGN KEY(queue_id) REFERENCES Resale_Queue(queue_id),
    FOREIGN KEY(buyer_id) REFERENCES Attendee(attendee_id)
);
