import random
from datetime import date, datetime, timedelta

from main import AppointmentSlots, Base, Doctors, Facilities, SessionLocal, engine

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
    "Mumbai": (19.0760, 72.8777),
    "Delhi": (28.7041, 77.1025),
    "Bangalore": (12.9716, 77.5946),
    "Chennai": (13.0827, 80.2707),
    "Kolkata": (22.5726, 88.3639),
    "Hyderabad": (17.3850, 78.4867),
    "Pune": (18.5204, 73.8567),
    "Ahmedabad": (23.0225, 72.5714),
    "Jaipur": (26.9124, 75.7873),
    "Lucknow": (26.8467, 80.9462),
    "Chandigarh": (30.7333, 76.7794),
    "Surat": (21.1702, 72.8311),
    "Nagpur": (21.1458, 79.0882),
    "Indore": (22.7196, 75.8577),
    "Bhopal": (23.2599, 77.4126),
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
        rating=round(random.uniform(1.0, 5.0), 1),
    )


def random_doctor(facility_id, department):
    return Doctors(
        fac_id=facility_id,
        name=f"Dr. {random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}",
        department=department,
    )


SLOT_START_HOUR = 9
SLOT_END_HOUR = 17
SLOT_MINUTES = 30


def slots_for_doctor(doctor_id, day):
    current = datetime.combine(day, datetime.min.time()).replace(hour=SLOT_START_HOUR)
    end = datetime.combine(day, datetime.min.time()).replace(hour=SLOT_END_HOUR)
    slots = []
    while current < end:
        slot_end = current + timedelta(minutes=SLOT_MINUTES)
        slots.append(
            AppointmentSlots(
                doctor_id=doctor_id,
                start_time=current,
                end_time=slot_end,
                is_available=True,
            )
        )
        current = slot_end
    return slots


def seed():
    session = SessionLocal()
    try:
        facilities = [random_facility(city) for city in CITIES]
        session.add_all(facilities)
        session.commit()

        DOCTORS_PER_DEPARTMENT = 2
        for facility in facilities:
            for department in DEPARTMENTS:
                for _ in range(DOCTORS_PER_DEPARTMENT):
                    session.add(random_doctor(facility.id, department))
        session.commit()

        doctors = session.query(Doctors).order_by(Doctors.id).all()
        today = date.today()
        for doctor in doctors:
            session.add_all(slots_for_doctor(doctor.id, today))
        session.commit()

        slot_count = session.query(AppointmentSlots).count()
        print(f"Seeded {len(facilities)} facilities, {len(doctors)} doctors, and {slot_count} appointment slots.")
    finally:
        session.close()


if __name__ == "__main__":
    seed()
