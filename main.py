import os
from typing import Literal
from dotenv import load_dotenv
from pydantic import BaseModel,ConfigDict,HttpUrl,field_validator
from fastapi import FastAPI,HTTPException,Header,Depends,Path,Response
from sqlalchemy import Boolean, Float, ForeignKey, JSON, String, Text, create_engine,LargeBinary
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()

MOD_PASSWORD = os.environ["MOD_PASSWORD"]

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./complaints.db")

if DATABASE_URL.startswith("postgres://"):
   DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

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

class Doctors(Base):
    __tablename__ = "doctors"

    id: Mapped[int] = mapped_column(primary_key=True)
    fac_id: Mapped[int] = mapped_column(ForeignKey("facilities.id"))
    name: Mapped[str] = mapped_column(String(255))
    department: Mapped[str] = mapped_column(String(255))


class FacOut(BaseModel):
    id: int
    name: str
    address: str
    languages_supported: list[str]
    has_wheelchair: bool
    has_visual_aids: bool
    has_hearing_aids: bool

    model_config = ConfigDict(from_attributes=True)


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "https://rdchampion.me",
        "http://127.0.0.1:5500"

    ],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/", include_in_schema=False)
def root():
    return RedirectResponse(url="/docs")

@app.get("/facilities", include_in_schema=True, response_model=list[FacOut])
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
        if language is not None:
            query = query.filter(Facilities.languages_supported.contains(language))
        facilities = query.all()
        if not facilities:
            raise HTTPException(status_code=404, detail="No facilities match the given constraints")
        return facilities

