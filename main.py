import os
from typing import Literal
from dotenv import load_dotenv
from pydantic import BaseModel,HttpUrl,field_validator
from fastapi import FastAPI,HTTPException,Header,Depends,Path,Response
from sqlalchemy import Boolean, ForeignKey, JSON, String, Text, create_engine,LargeBinary
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

class Doctors(Base):
    __tablename__ = "doctors"

    id: Mapped[int] = mapped_column(primary_key=True)
    fac_id: Mapped[int] = mapped_column(ForeignKey("facilities.id"))
    name: Mapped[str] = mapped_column(String(255))
    department: Mapped[str] = mapped_column(String(255))


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
