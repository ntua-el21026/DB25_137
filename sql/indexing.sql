----------------
--- Indexing ---
----------------

USE pulse_university;

-- Ticket indexes
CREATE INDEX idx_ticket_event_date_payment ON Ticket (event_id, purchase_date, method_id);
CREATE INDEX idx_ticket_attendee_event ON Ticket (attendee_id, event_id);

-- Genre and subgenre indexes
CREATE INDEX idx_artist_genre ON Artist_Genre (genre_id, artist_id);
CREATE INDEX idx_artist_subgenre ON Artist_SubGenre (sub_genre_id, artist_id);

CREATE INDEX idx_band_genre ON Band_Genre (genre_id, band_id);
CREATE INDEX idx_band_subgenre ON Band_SubGenre (sub_genre_id, band_id);

-- Performance indexes
CREATE INDEX idx_perf_event_type ON Performance (event_id, type_id);
CREATE INDEX idx_perf_datetime ON Performance (datetime);

-- Performance_Artist / Performance_Band
CREATE INDEX idx_perf_artist ON Performance_Artist (artist_id, perf_id);
CREATE INDEX idx_perf_band ON Performance_Band (band_id, perf_id);

-- Review indexes
CREATE INDEX idx_review_attendee_overall ON Review (attendee_id, overall);
CREATE INDEX idx_review_perf ON Review (perf_id);  -- for joins with Performance in Q4, Q15

-- Staff indexes
CREATE INDEX idx_staff_role ON Staff (role_id);
CREATE INDEX idx_staff_experience ON Staff (experience_id);

-- Location index
CREATE INDEX idx_location_continent ON Location (continent_id);
