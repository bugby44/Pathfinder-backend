import os
import bcrypt
from datetime import datetime
from typing import Literal
from dotenv import load_dotenv
from pydantic import BaseModel,ConfigDict,HttpUrl,field_validator
from fastapi import FastAPI,HTTPException,Header,Depends,Path,Response
from sqlalchemy import Boolean, DateTime, Float, ForeignKey, JSON, String, Text, create_engine,LargeBinary, update
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()

MOD_PASSWORD = os.environ["MOD_PASSWORD"]

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./complaints.db")

if DATABASE_URL.startswith("postgres://"):
   DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

connect_args = (
    {"check_same_thread": False}
    if DATABASE_URL.startswith("sqlite")
    else {"connect_timeout": 30}
)

engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args,
    echo=False,
    pool_pre_ping=True,
    pool_recycle=240,
)


SessionLocal = sessionmaker(bind=engine)


class Base(DeclarativeBase):
    pass

class Facilities(Base):
    __tablename__ = "facilities"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    address: Mapped[str] = mapped_column(String(500))
    languages_supported: Mapped[list] = mapped_column(JSON, default=list)
    has_wheelchair: Mapped[bool] = mapped_column(Boolean, default=False)
    has_visual_aids: Mapped[bool] = mapped_column(Boolean, default=False)
    has_hearing_aids: Mapped[bool] = mapped_column(Boolean, default=False)
    latitude: Mapped[float] = mapped_column(Float)
    longitude: Mapped[float] = mapped_column(Float)
    rating: Mapped[float] = mapped_column(Float)

class Doctors(Base):
    __tablename__ = "doctors"

    id: Mapped[int] = mapped_column(primary_key=True)
    fac_id: Mapped[int] = mapped_column(ForeignKey("facilities.id"))
    name: Mapped[str] = mapped_column(String(255))
    department: Mapped[str] = mapped_column(String(255))


class Users(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255))
    hashed_password: Mapped[str] = mapped_column(String(255))
    has_government_id: Mapped[bool] = mapped_column(Boolean, default=False)
    has_prior_prescription: Mapped[bool] = mapped_column(Boolean, default=False)
    has_referral_letter: Mapped[bool] = mapped_column(Boolean, default=False)


class AppointmentSlots(Base):
    __tablename__ = "appointment_slots"

    id: Mapped[int] = mapped_column(primary_key=True)
    doctor_id: Mapped[int] = mapped_column(ForeignKey("doctors.id"))
    start_time: Mapped[datetime] = mapped_column(DateTime)
    end_time: Mapped[datetime] = mapped_column(DateTime)
    is_available: Mapped[bool] = mapped_column(Boolean, default=True)
    booked_by_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)


class FacOut(BaseModel):
    id: int
    name: str
    address: str
    languages_supported: list[str]
    has_wheelchair: bool
    has_visual_aids: bool
    has_hearing_aids: bool
    latitude: float
    longitude: float
    rating: float

    model_config = ConfigDict(from_attributes=True)


class DoctorOut(BaseModel):
    id: int
    fac_id: int
    name: str
    department: str

    model_config = ConfigDict(from_attributes=True)


class UserCreate(BaseModel):
    email: str
    name: str
    password: str


class UserLogin(BaseModel):
    email: str
    password: str


class UserOut(BaseModel):
    id: int
    email: str
    name: str
    has_government_id: bool
    has_prior_prescription: bool
    has_referral_letter: bool

    model_config = ConfigDict(from_attributes=True)


class SlotOut(BaseModel):
    id: int
    doctor_id: int
    start_time: datetime
    end_time: datetime
    is_available: bool

    model_config = ConfigDict(from_attributes=True)


class LoginOut(BaseModel):
    id: int
    email: str
    name: str
    has_government_id: bool
    has_prior_prescription: bool
    has_referral_letter: bool
    appointments: list[SlotOut]


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/", include_in_schema=False)
def root():
    return RedirectResponse(url="/docs")

@app.get("/facilities", include_in_schema=True, response_model=list[FacOut], tags=["Facilities"])
def facilities(
    has_wheelchair: bool | None = None,
    has_visual_aids: bool | None = None,
    has_hearing_aids: bool | None = None,
    language: str | None = None,
):
    with SessionLocal() as session:
        query = session.query(Facilities)
        if has_wheelchair is not None:
            query = query.filter(Facilities.has_wheelchair == has_wheelchair)
        if has_visual_aids is not None:
            query = query.filter(Facilities.has_visual_aids == has_visual_aids)
        if has_hearing_aids is not None:
            query = query.filter(Facilities.has_hearing_aids == has_hearing_aids)
        facilities = query.all()
        if language is not None:
            facilities = [f for f in facilities if language in f.languages_supported]
        if not facilities:
            raise HTTPException(status_code=404, detail="No facilities match the given constraints")
        return facilities


@app.get("/facilities/{facility_id}", response_model=FacOut, tags=["Facilities"])
def facility_by_id(facility_id: int):
    with SessionLocal() as session:
        facility = session.get(Facilities, facility_id)
        if facility is None:
            raise HTTPException(status_code=404, detail="Facility not found")
        return facility


@app.get("/doctors", response_model=list[DoctorOut], tags=["Doctors"])
def doctors(fac_id: int | None = None, department: str | None = None):
    with SessionLocal() as session:
        query = session.query(Doctors)
        if fac_id is not None:
            query = query.filter(Doctors.fac_id == fac_id)
        if department is not None:
            query = query.filter(Doctors.department == department)
        doctors = query.all()
        if not doctors:
            raise HTTPException(status_code=404, detail="No doctors match the given constraints")
        return doctors


@app.get("/slots", response_model=list[SlotOut], tags=["Appointment Slots"])
def slots(doctor_id: int | None = None, only_available: bool = True):
    with SessionLocal() as session:
        query = session.query(AppointmentSlots)
        if doctor_id is not None:
            query = query.filter(AppointmentSlots.doctor_id == doctor_id)
        if only_available:
            query = query.filter(AppointmentSlots.is_available == True)
        slots = query.order_by(AppointmentSlots.start_time).all()
        if not slots:
            raise HTTPException(status_code=404, detail="No slots match the given constraints")
        return slots


@app.post("/slots/{slot_id}/book", response_model=SlotOut, tags=["Appointment Slots"])
def book_slot(slot_id: int, user_id: int):
    with SessionLocal() as session:
        user = session.get(Users, user_id)
        if user is None:
            raise HTTPException(status_code=404, detail="User not found")

        slot = session.get(AppointmentSlots, slot_id)
        if slot is None:
            raise HTTPException(status_code=404, detail="Slot not found")

        result = session.execute(
            update(AppointmentSlots)
            .where(AppointmentSlots.id == slot_id, AppointmentSlots.is_available == True)
            .values(is_available=False, booked_by_user_id=user_id)
        )
        session.commit()

        if result.rowcount == 0:
            raise HTTPException(status_code=409, detail="Slot is no longer available")

        session.refresh(slot)
        return slot


@app.post("/signup", response_model=UserOut, tags=["Auth"])
def signup(user: UserCreate):
    with SessionLocal() as session:
        existing = session.query(Users).filter(Users.email == user.email).first()
        if existing is not None:
            raise HTTPException(status_code=400, detail="Email already registered")
        hashed_password = bcrypt.hashpw(user.password.encode(), bcrypt.gensalt()).decode()
        new_user = Users(email=user.email, name=user.name, hashed_password=hashed_password)
        session.add(new_user)
        session.commit()
        session.refresh(new_user)
        return new_user


@app.post("/login", response_model=LoginOut, tags=["Auth"])
def login(user: UserLogin):
    with SessionLocal() as session:
        existing = session.query(Users).filter(Users.email == user.email).first()
        if existing is None or not bcrypt.checkpw(user.password.encode(), existing.hashed_password.encode()):
            raise HTTPException(status_code=401, detail="Invalid email or password")

        appointments = (
            session.query(AppointmentSlots)
            .filter(AppointmentSlots.booked_by_user_id == existing.id)
            .order_by(AppointmentSlots.start_time)
            .all()
        )
        return LoginOut(
            id=existing.id,
            email=existing.email,
            name=existing.name,
            has_government_id=existing.has_government_id,
            has_prior_prescription=existing.has_prior_prescription,
            has_referral_letter=existing.has_referral_letter,
            appointments=appointments,
        )


@app.get("/appointments", response_model=list[SlotOut], tags=["Appointments"])
def my_appointments(user_id: int):
    with SessionLocal() as session:
        user = session.get(Users, user_id)
        if user is None:
            raise HTTPException(status_code=404, detail="User not found")

        appointments = (
            session.query(AppointmentSlots)
            .filter(AppointmentSlots.booked_by_user_id == user_id)
            .order_by(AppointmentSlots.start_time)
            .all()
        )
        if not appointments:
            raise HTTPException(status_code=404, detail="No appointments found")
        return appointments


@app.patch("/appointments/{slot_id}/reschedule", response_model=SlotOut, tags=["Appointments"])
def reschedule_appointment(slot_id: int, new_slot_id: int, user_id: int):
    with SessionLocal() as session:
        user = session.get(Users, user_id)
        if user is None:
            raise HTTPException(status_code=404, detail="User not found")

        old_slot = session.get(AppointmentSlots, slot_id)
        if old_slot is None:
            raise HTTPException(status_code=404, detail="Appointment not found")
        if old_slot.booked_by_user_id != user_id:
            raise HTTPException(status_code=403, detail="This appointment does not belong to this user")

        new_slot = session.get(AppointmentSlots, new_slot_id)
        if new_slot is None:
            raise HTTPException(status_code=404, detail="New slot not found")
        if new_slot.doctor_id != old_slot.doctor_id:
            raise HTTPException(status_code=400, detail="New slot must be with the same doctor")

        result = session.execute(
            update(AppointmentSlots)
            .where(AppointmentSlots.id == new_slot_id, AppointmentSlots.is_available == True)
            .values(is_available=False, booked_by_user_id=user_id)
        )
        if result.rowcount == 0:
            session.rollback()
            raise HTTPException(status_code=409, detail="New slot is no longer available")

        session.execute(
            update(AppointmentSlots)
            .where(AppointmentSlots.id == slot_id)
            .values(is_available=True, booked_by_user_id=None)
        )
        session.commit()

        session.refresh(new_slot)
        return new_slot


@app.patch("/checklist", response_model=UserOut, tags=["Checklist"])
def update_checklist(
    user_id: int,
    has_government_id: bool | None = None,
    has_prior_prescription: bool | None = None,
    has_referral_letter: bool | None = None,
):
    with SessionLocal() as session:
        user = session.get(Users, user_id)
        if user is None:
            raise HTTPException(status_code=404, detail="User not found")

        if has_government_id is not None:
            user.has_government_id = has_government_id
        if has_prior_prescription is not None:
            user.has_prior_prescription = has_prior_prescription
        if has_referral_letter is not None:
            user.has_referral_letter = has_referral_letter

        session.commit()
        session.refresh(user)
        return user

