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
CITIES = [
    "Springfield", "Riverside", "Fairview", "Greenville", "Madison",
    "Georgetown", "Salem", "Clinton", "Franklin", "Arlington",
    "Centerville", "Burlington", "Manchester", "Kingston", "Oakland",
]
FACILITY_TYPES = ["General Hospital", "Medical Center", "Community Clinic", "Health Center"]
STREET_NAMES = ["Main", "Oak", "Park", "Elm", "Washington", "Maple", "Cedar"]


def random_facility(city):
    return Facilities(
        name=f"{city} {random.choice(FACILITY_TYPES)}",
        address=f"{random.randint(100, 999)} {random.choice(STREET_NAMES)} St, {city}",
        languages_supported=random.sample(LANGUAGES, k=random.randint(1, 4)),
        has_wheelchair=random.choice([True, False]),
        has_visual_aids=random.choice([True, False]),
        has_hearing_aids=random.choice([True, False]),
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
