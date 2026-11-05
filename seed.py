import random

from main import Base, Doctors, Facilities, SessionLocal, engine

Base.metadata.create_all(bind=engine)

LANGUAGES = ["English", "Spanish", "Mandarin", "Hindi", "Arabic", "French", "Vietnamese", "Tagalog"]
DEPARTMENTS = [
    "Cardiology", "General Medicine", "Pediatrics", "Orthopedics",
    "Neurology", "Dermatology", "ENT", "Gynecology", "Psychiatry", "Oncology",
]
FIRST_NAMES = [
    "James", "Mary", "Robert", "Patricia", "John", "Jennifer", "Michael", "Linda",
    "William", "Elizabeth", "David", "Barbara", "Richard", "Susan", "Joseph", "Jessica",
]
LAST_NAMES = [
    "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis",
    "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson", "Thomas",
]
CITY_COORDS = {
    "Springfield": (39.7817, -89.6501),
    "Riverside": (33.9806, -117.3755),
    "Fairview": (35.0532, -85.2405),
    "Greenville": (34.8526, -82.3940),
    "Madison": (43.0731, -89.4012),
    "Georgetown": (38.2098, -84.5588),
    "Salem": (44.9429, -123.0351),
    "Clinton": (41.8459, -90.1878),
    "Franklin": (35.9251, -86.8689),
    "Arlington": (32.7357, -97.1081),
    "Centerville": (39.6295, -84.1594),
    "Burlington": (44.4759, -73.2121),
    "Manchester": (42.9956, -71.4548),
    "Kingston": (41.9270, -73.9974),
    "Oakland": (37.8044, -122.2712),
}
CITIES = list(CITY_COORDS.keys())
FACILITY_TYPES = ["General Hospital", "Medical Center", "Community Clinic", "Health Center"]
STREET_NAMES = ["Main", "Oak", "Park", "Elm", "Washington", "Maple", "Cedar"]


def random_facility(city):
    base_lat, base_lon = CITY_COORDS[city]
    return Facilities(
        name=f"{city} {random.choice(FACILITY_TYPES)}",
        address=f"{random.randint(100, 999)} {random.choice(STREET_NAMES)} St, {city}",
        languages_supported=random.sample(LANGUAGES, k=random.randint(1, 4)),
        has_wheelchair=random.choice([True, False]),
        has_visual_aids=random.choice([True, False]),
        has_hearing_aids=random.choice([True, False]),
        latitude=base_lat + random.uniform(-0.05, 0.05),
        longitude=base_lon + random.uniform(-0.05, 0.05),
    )


def random_doctor(facility_id):
    return Doctors(
        fac_id=facility_id,
        name=f"Dr. {random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}",
        department=random.choice(DEPARTMENTS),
    )


def seed():
    session = SessionLocal()
    try:
        facilities = [random_facility(city) for city in CITIES]
        session.add_all(facilities)
        session.commit()

        for facility in facilities:
            for _ in range(random.randint(1, 5)):
                session.add(random_doctor(facility.id))
        session.commit()

        doctor_count = session.query(Doctors).count()
        print(f"Seeded {len(facilities)} facilities and {doctor_count} doctors.")
    finally:
        session.close()


if __name__ == "__main__":
    seed()
