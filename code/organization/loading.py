import random
from faker import Faker
from datetime import datetime, timedelta

fake = Faker()
random.seed(42)  # For reproducible results

# Configuration for the number of records to generate
N_LOCATIONS = 20
N_FESTIVALS = 5
N_STAGES = 10
N_EQUIPMENT = 15
N_EVENTS = 30
N_STAFF = 50
N_ARTISTS = 50
N_BANDS = 20
N_ATTENDEES = 1000
N_TICKETS = 2000
N_REVIEWS = 500
N_RESALE_OFFERS = 100
N_RESALE_REQUESTS = 150
N_PERFORMANCES = 300  # Estimated based on events
EQUIPMENT_TYPES = [
    "PA System", "Mixer", "Microphone", "Monitor", "Amplifier", 
    "Drum Kit", "Keyboard", "Guitar", "Bass", "Lights", 
    "Fog Machine", "Projector", "Screen", "Camera", "Speaker"
]
# Helper functions
def get_random_date(start_year=2010, end_year=2023):
    return fake.date_between_dates(
        date_start=datetime(start_year, 1, 1),
        date_end=datetime(end_year, 12, 31)
    )

def get_random_datetime(start_year=2010, end_year=2023):
    return fake.date_time_between_dates(
        datetime_start=datetime(start_year, 1, 1),
        datetime_end=datetime(end_year, 12, 31)
    )

def generate_image_url():
    return f"https://picsum.photos/seed/{fake.uuid4()}/600/400"

def generate_caption():
    return fake.sentence(nb_words=6)

def write_sql_header(f):
    f.write("-- MySQL Script to populate pulse_university database with junk data\n")
    f.write("-- Generated automatically with Python and Faker\n\n")
    f.write("-- First, make sure to run your schema creation script before this one\n\n")
    f.write("BEGIN;\n\n")

def write_sql_footer(f):
    f.write("\nCOMMIT;\n")

# Table generation functions
def generate_locations(f):
    f.write("-- Location data\n")
    continents = [1, 2, 3, 4, 5, 6]  # Africa, Asia, Europe, North America, South America, Oceania
    
    for i in range(1, N_LOCATIONS + 1):
        street_name = fake.street_name()
        street_number = fake.building_number()
        zip_code = fake.postcode()
        city = fake.city()
        country = fake.country()
        continent_id = random.choice(continents)
        latitude = fake.latitude()
        longitude = fake.longitude()
        image = generate_image_url()
        caption = generate_caption()
        
        f.write(f"INSERT INTO Location (street_name, street_number, zip_code, city, country, ")
        f.write(f"continent_id, latitude, longitude, image, caption) VALUES (")
        f.write(f"'{street_name}', '{street_number}', '{zip_code}', '{city}', '{country}', ")
        f.write(f"{continent_id}, {latitude}, {longitude}, '{image}', '{caption}');\n")
    f.write("\n")

def generate_festivals(f):
    f.write("-- Festival data\n")
    loc_ids = list(range(1, N_LOCATIONS + 1))
    
    for year in range(2019, 2024):  # Festivals from 2019 to 2023
        name = f"{fake.word().capitalize()} Festival {year}"
        start_date = datetime(year, random.randint(5, 8), random.randint(1, 28))  # Summer months
        end_date = start_date + timedelta(days=random.randint(2, 5))
        image = generate_image_url()
        caption = generate_caption()
        loc_id = random.choice(loc_ids)
        
        f.write(f"INSERT INTO Festival (fest_year, name, start_date, end_date, image, caption, loc_id) VALUES (")
        f.write(f"{year}, '{name}', '{start_date}', '{end_date}', '{image}', '{caption}', {loc_id});\n")
    f.write("\n")

def generate_stages(f):
    f.write("-- Stage data\n")
    for i in range(1, N_STAGES + 1):
        name = f"{fake.word().capitalize()} Stage"
        capacity = random.randint(100, 10000)
        image = generate_image_url()
        caption = generate_caption()
        
        f.write(f"INSERT INTO Stage (name, capacity, image, caption) VALUES (")
        f.write(f"'{name}', {capacity}, '{image}', '{caption}');\n")
    f.write("\n")

def generate_equipment(f):
    f.write("-- Equipment data\n")
    for i, equip in enumerate(EQUIPMENT_TYPES, 1):
        image = generate_image_url()
        caption = generate_caption()
        
        f.write(f"INSERT INTO Equipment (equip_id, name, image, caption) VALUES (")
        f.write(f"{i}, '{equip}', '{image}', '{caption}');\n")
    f.write("\n")
def generate_stage_equipment(f):
    f.write("-- Stage_Equipment data\n")
    stage_ids = list(range(1, N_STAGES + 1))
    equip_ids = list(range(1, len(EQUIPMENT_TYPES) + 1))  
    for stage_id in stage_ids:
        num_equip = random.randint(3, 8)
        selected_equip = random.sample(equip_ids, num_equip)
        
        for equip_id in selected_equip:
            f.write(f"INSERT INTO Stage_Equipment (stage_id, equip_id) VALUES (")
            f.write(f"{stage_id}, {equip_id});\n")
    f.write("\n")

def generate_events(f):
    f.write("-- Event data\n")
    fest_years = list(range(2019, 2024))
    stage_ids = list(range(1, N_STAGES + 1))
    
    for i in range(1, N_EVENTS + 1):
        title = f"{fake.word().capitalize()} {fake.word().capitalize()} Event"
        is_full = random.choice([0, 1])
        image = generate_image_url()
        caption = generate_caption()
        fest_year = random.choice(fest_years)
        stage_id = random.choice(stage_ids)
        
        f.write(f"INSERT INTO Event (event_id, title, is_full, image, caption, fest_year, stage_id) VALUES (")
        f.write(f"{i}, '{title}', {is_full}, '{image}', '{caption}', {fest_year}, {stage_id});\n")
    f.write("\n")

def generate_staff(f):
    f.write("-- Staff data\n")
    role_ids = list(range(1, 9))
    level_ids = list(range(1, 6))
    
    for i in range(1, N_STAFF + 1):
        first_name = fake.first_name()
        last_name = fake.last_name()
        date_of_birth = get_random_date(1960, 2000)
        role_id = random.choice(role_ids)
        experience_id = random.choice(level_ids)
        image = generate_image_url()
        caption = generate_caption()
        
        f.write(f"INSERT INTO Staff (staff_id, first_name, last_name, date_of_birth, role_id, experience_id, image, caption) VALUES (")
        f.write(f"{i}, '{first_name}', '{last_name}', '{date_of_birth}', {role_id}, {experience_id}, '{image}', '{caption}');\n")
    f.write("\n")

def generate_works_on(f):
    f.write("-- Works_On data\n")
    staff_ids = list(range(1, N_STAFF + 1))
    event_ids = list(range(1, N_EVENTS + 1))
    
    for event_id in event_ids:
        num_staff = random.randint(5, 15)
        selected_staff = random.sample(staff_ids, num_staff)
        
        for staff_id in selected_staff:
            f.write(f"INSERT INTO Works_On (staff_id, event_id) VALUES (")
            f.write(f"{staff_id}, {event_id});\n")
    f.write("\n")

def generate_performances(f):
    f.write("-- Performance data\n")
    type_ids = list(range(1, 6))
    stage_ids = list(range(1, N_STAGES + 1))
    event_ids = list(range(1, N_EVENTS + 1))
    perf_counter = 1
    
    for event_id in event_ids:
        num_performances = random.randint(3, 10)
        event_year = 2019 + (event_id % 5)  # Distribute across festival years
        
        for seq in range(1, num_performances + 1):
            type_id = random.choice(type_ids)
            perf_datetime = get_random_datetime(event_year, event_year)
            duration = random.randint(20, 120)
            break_duration = random.randint(5, 30)
            stage_id = random.choice(stage_ids)
            
            f.write(f"INSERT INTO Performance (perf_id, type_id, datetime, duration, break_duration, stage_id, event_id, sequence_number) VALUES (")
            f.write(f"{perf_counter}, {type_id}, '{perf_datetime}', {duration}, {break_duration}, {stage_id}, {event_id}, {seq});\n")
            perf_counter += 1
    f.write("\n")

def generate_artists(f):
    f.write("-- Artist data\n")
    for i in range(1, N_ARTISTS + 1):
        first_name = fake.first_name() if random.random() > 0.3 else None
        last_name = fake.last_name() if random.random() > 0.3 else None
        nickname = fake.word() if random.random() > 0.5 else None
        date_of_birth = get_random_date(1950, 2000) if random.random() > 0.3 else None
        main_genre = fake.word()
        sub_genre = fake.word()
        webpage = fake.url() if random.random() > 0.5 else None
        instagram = f"@{fake.user_name()}" if random.random() > 0.5 else None
        image = generate_image_url()
        caption = generate_caption()
        
        f.write(f"INSERT INTO Artist (artist_id, first_name, last_name, nickname, date_of_birth, main_genre, sub_genre, ")
        f.write(f"webpage, instagram, image, caption) VALUES (")
        f.write(f"{i}, ")
        f.write(f"'{first_name}'" if first_name else "NULL")
        f.write(f", '{last_name}'" if last_name else ", NULL")
        f.write(f", '{nickname}'" if nickname else ", NULL")
        f.write(f", '{date_of_birth}'" if date_of_birth else ", NULL")
        f.write(f", '{main_genre}', '{sub_genre}', ")
        f.write(f"'{webpage}'" if webpage else "NULL")
        f.write(f", '{instagram}'" if instagram else ", NULL")
        f.write(f", '{image}', '{caption}');\n")
    f.write("\n")

def generate_bands(f):
    f.write("-- Band data\n")
    for i in range(1, N_BANDS + 1):
        name = f"The {fake.word().capitalize()} {fake.word().capitalize()}"
        formation_date = get_random_date(1960, 2020) if random.random() > 0.3 else None
        main_genre = fake.word()
        sub_genre = fake.word()
        webpage = fake.url() if random.random() > 0.5 else None
        instagram = f"@{fake.user_name()}" if random.random() > 0.5 else None
        image = generate_image_url()
        caption = generate_caption()
        
        f.write(f"INSERT INTO Band (band_id, name, formation_date, main_genre, sub_genre, ")
        f.write(f"webpage, instagram, image, caption) VALUES (")
        f.write(f"{i}, '{name}', ")
        f.write(f"'{formation_date}'" if formation_date else "NULL")
        f.write(f", '{main_genre}', '{sub_genre}', ")
        f.write(f"'{webpage}'" if webpage else "NULL")
        f.write(f", '{instagram}'" if instagram else ", NULL")
        f.write(f", '{image}', '{caption}');\n")
    f.write("\n")

def generate_band_members(f):
    f.write("-- Band_Member data\n")
    artist_ids = list(range(1, N_ARTISTS + 1))
    band_ids = list(range(1, N_BANDS + 1))
    
    for band_id in band_ids:
        num_members = random.randint(3, 8)
        selected_artists = random.sample(artist_ids, num_members)
        
        for artist_id in selected_artists:
            f.write(f"INSERT INTO Band_Member (band_id, artist_id) VALUES (")
            f.write(f"{band_id}, {artist_id});\n")
    f.write("\n")

def generate_performance_bands(f):
    f.write("-- Performance_Band data\n")
    perf_ids = list(range(1, N_PERFORMANCES + 1))
    band_ids = list(range(1, N_BANDS + 1))
    num_perf_with_bands = int(len(perf_ids) * 0.7)
    selected_perfs = random.sample(perf_ids, num_perf_with_bands)
    
    for perf_id in selected_perfs:
        band_id = random.choice(band_ids)
        f.write(f"INSERT INTO Performance_Band (perf_id, band_id) VALUES (")
        f.write(f"{perf_id}, {band_id});\n")
    f.write("\n")

def generate_performance_artists(f):
    f.write("-- Performance_Artist data\n")
    perf_ids = list(range(1, N_PERFORMANCES + 1))
    artist_ids = list(range(1, N_ARTISTS + 1))
    
    # Get performances without bands (approx 30%)
    solo_perfs = [pid for pid in perf_ids if pid % 3 == 0]
    
    for perf_id in solo_perfs:
        num_artists = random.randint(1, 3)
        selected_artists = random.sample(artist_ids, num_artists)
        
        for artist_id in selected_artists:
            f.write(f"INSERT INTO Performance_Artist (perf_id, artist_id) VALUES (")
            f.write(f"{perf_id}, {artist_id});\n")
    f.write("\n")

def generate_attendees(f):
    f.write("-- Attendee data\n")
    for i in range(1, N_ATTENDEES + 1):
        first_name = fake.first_name()
        last_name = fake.last_name()
        date_of_birth = get_random_date(1950, 2010) if random.random() > 0.1 else None
        phone_number = fake.phone_number() if random.random() > 0.5 else None
        email = fake.email() if random.random() > 0.8 else None
        
        f.write(f"INSERT INTO Attendee (attendee_id, first_name, last_name, date_of_birth, phone_number, email) VALUES (")
        f.write(f"{i}, '{first_name}', '{last_name}', ")
        f.write(f"'{date_of_birth}'" if date_of_birth else "NULL")
        f.write(f", '{phone_number}'" if phone_number else ", NULL")
        f.write(f", '{email}'" if email else ", NULL")
        f.write(");\n")
    f.write("\n")

def generate_tickets(f):
    f.write("-- Ticket data\n")
    type_ids = list(range(1, 6))
    method_ids = list(range(1, 4))
    status_ids = list(range(1, 4))
    attendee_ids = list(range(1, N_ATTENDEES + 1))
    event_ids = list(range(1, N_EVENTS + 1))
    
    for i in range(1, N_TICKETS + 1):
        type_id = random.choice(type_ids)
        purchase_date = get_random_date(2019, 2023)
        
        # Set cost based on ticket type
        if type_id == 1:  # general
            cost = round(random.uniform(50, 100), 2)
        elif type_id == 2:  # VIP
            cost = round(random.uniform(150, 300), 2)
        elif type_id == 3:  # backstage
            cost = round(random.uniform(200, 400), 2)
        elif type_id == 4:  # early bird
            cost = round(random.uniform(30, 70), 2)
        else:  # student
            cost = round(random.uniform(20, 50), 2)
        
        method_id = random.choice(method_ids)
        ean_number = fake.ean13() if random.random() > 0.3 else None
        status_id = random.choice(status_ids)
        attendee_id = random.choice(attendee_ids)
        event_id = random.choice(event_ids)
        
        f.write(f"INSERT INTO Ticket (ticket_id, type_id, purchase_date, cost, method_id, ean_number, ")
        f.write(f"status_id, attendee_id, event_id) VALUES (")
        f.write(f"{i}, {type_id}, '{purchase_date}', {cost}, {method_id}, ")
        f.write(f"'{ean_number}'" if ean_number else "NULL")
        f.write(f", {status_id}, {attendee_id}, {event_id});\n")
    f.write("\n")

def generate_reviews(f):
    f.write("-- Review data\n")
    attendee_ids = list(range(1, N_ATTENDEES + 1))
    perf_ids = list(range(1, N_PERFORMANCES + 1))
    
    for i in range(1, N_REVIEWS + 1):
        interpretation = random.randint(1, 5)
        sound_and_visuals = random.randint(1, 5)
        stage_presence = random.randint(1, 5)
        organization = random.randint(1, 5)
        overall = random.randint(1, 5)
        attendee_id = random.choice(attendee_ids)
        perf_id = random.choice(perf_ids)
        
        f.write(f"INSERT INTO Review (review_id, interpretation, sound_and_visuals, stage_presence, ")
        f.write(f"organization, overall, attendee_id, perf_id) VALUES (")
        f.write(f"{i}, {interpretation}, {sound_and_visuals}, {stage_presence}, ")
        f.write(f"{organization}, {overall}, {attendee_id}, {perf_id});\n")
    f.write("\n")

def generate_resale_offers(f):
    f.write("-- Resale_Offer data\n")
    ticket_ids = random.sample(range(1, N_TICKETS + 1), N_RESALE_OFFERS)
    event_ids = list(range(1, N_EVENTS + 1))
    attendee_ids = list(range(1, N_ATTENDEES + 1))
    
    for i, ticket_id in enumerate(ticket_ids, 1):
        event_id = random.choice(event_ids)
        seller_id = random.choice(attendee_ids)
        timestamp = get_random_datetime()
        
        f.write(f"INSERT INTO Resale_Offer (offer_id, ticket_id, event_id, seller_id, timestamp) VALUES (")
        f.write(f"{i}, {ticket_id}, {event_id}, {seller_id}, '{timestamp}');\n")
    f.write("\n")

def generate_resale_interest_requests(f):
    f.write("-- Resale_Interest_Request data\n")
    attendee_ids = list(range(1, N_ATTENDEES + 1))
    event_ids = list(range(1, N_EVENTS + 1))
    
    for i in range(1, N_RESALE_REQUESTS + 1):
        buyer_id = random.choice(attendee_ids)
        event_id = random.choice(event_ids)
        expressed_at = get_random_datetime()
        fulfilled = random.choice([0, 1])
        
        f.write(f"INSERT INTO Resale_Interest_Request (request_id, buyer_id, event_id, expressed_at, fulfilled) VALUES (")
        f.write(f"{i}, {buyer_id}, {event_id}, '{expressed_at}', {fulfilled});\n")
    f.write("\n")

def generate_resale_interest_types(f):
    f.write("-- Resale_Interest_Type data\n")
    request_ids = list(range(1, N_RESALE_REQUESTS + 1))
    type_ids = list(range(1, 6))
    
    for request_id in request_ids:
        num_types = random.randint(1, 3)
        selected_types = random.sample(type_ids, num_types)
        
        for type_id in selected_types:
            f.write(f"INSERT INTO Resale_Interest_Type (request_id, type_id) VALUES (")
            f.write(f"{request_id}, {type_id});\n")
    f.write("\n")

def main():
    with open("pulse_university_data.sql", "w") as f:
        write_sql_header(f)
        
        # Generate data for each table
        generate_locations(f)
        generate_festivals(f)
        generate_stages(f)
        generate_equipment(f)
        generate_stage_equipment(f)
        generate_events(f)
        generate_staff(f)
        generate_works_on(f)
        generate_performances(f)
        generate_artists(f)
        generate_bands(f)
        generate_band_members(f)
        generate_performance_bands(f)
        generate_performance_artists(f)
        generate_attendees(f)
        generate_tickets(f)
        generate_reviews(f)
        generate_resale_interest_requests(f)
        generate_resale_interest_types(f)
        generate_resale_offers(f)
        
        write_sql_footer(f)

if __name__ == "__main__":
    main()