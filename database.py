# database.py - COMPLETE VERSION
from sqlalchemy import Column, Integer, String, Text, Enum, ForeignKey, DateTime
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from sqlalchemy import create_engine
from datetime import datetime
import enum
import os


DB_URL = os.getenv("LEGAL_RAG_DB_URL", "sqlite:///./legal_rag.db")

engine = create_engine(
    DB_URL,
    connect_args={"check_same_thread": False} if DB_URL.startswith("sqlite") else {},
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

class UserRole(str, enum.Enum):
    client = "client"
    lawyer = "lawyer"

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    name = Column(String(255), nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), nullable=False)
    cases = relationship("Case", back_populates="client", cascade="all, delete-orphan")
    lawyer_profile = relationship("LawyerProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")

class LawyerProfile(Base):
    __tablename__ = "lawyer_profiles"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    specialization = Column(String(100), nullable=True)
    city = Column(String(100), nullable=True)
    experience_years = Column(Integer, nullable=True)
    rating = Column(Integer, nullable=True)
    is_available = Column(Integer, nullable=False, default=1)
    user = relationship("User", back_populates="lawyer_profile")

class CaseStatus(str, enum.Enum):
    open = "open"
    matched = "matched"
    closed = "closed"

class Case(Base):
    __tablename__ = "cases"
    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    issue_type = Column(String(50), nullable=False)
    description = Column(Text, nullable=False)
    status = Column(Enum(CaseStatus), nullable=False, default=CaseStatus.open)
    created_at = Column(DateTime, default=datetime.utcnow)
    client = relationship("User", back_populates="cases")
    recommendations = relationship("LawyerRecommendation", back_populates="case")  # ← FIXED

class RecommendationStatus(str, enum.Enum):
    suggested = "suggested"
    client_accepted = "client_accepted"
    lawyer_accepted = "lawyer_accepted"
    matched = "matched"
    declined = "declined"

class LawyerRecommendation(Base):
    __tablename__ = "lawyer_recommendations"
    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("cases.id"), nullable=False)
    lawyer_id = Column(Integer, ForeignKey("lawyer_profiles.id"), nullable=False)
    score = Column(Integer, nullable=False)
    status = Column(Enum(RecommendationStatus), default=RecommendationStatus.suggested)
    created_at = Column(DateTime, default=datetime.utcnow)
    case = relationship("Case", back_populates="recommendations")
    lawyer = relationship("LawyerProfile")



class ActiveCase(Base):
    __tablename__ = "active_cases"

    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("cases.id"))
    lawyer_id = Column(Integer, ForeignKey("lawyer_profiles.id"))
    status = Column(String, default="active")
    created_at = Column(DateTime, default=datetime.utcnow)

    case = relationship("Case")
    lawyer = relationship("LawyerProfile")


def init_db() -> None:
    Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
