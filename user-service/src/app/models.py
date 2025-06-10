from sqlalchemy import Column, ForeignKey, Integer, String, Date, DateTime, Enum, Boolean
from sqlalchemy.sql import func
from .database import Base
from . import schemas

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    birthday = Column(Date, nullable=True)
    email = Column(String, unique=True, index=True, nullable=True)
    mobile_number = Column(String, nullable=True)
    level = Column(String, nullable=False)
    role = Column(String, nullable=False)
    username = Column(String, unique=True, index=True, nullable=True)
    hashed_password = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class Organization_categories(Base):
    __tablename__ = "organization_categories"

    id = Column(Integer, primary_key=True, index=True)
    category_name = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class Organization_units(Base):
    __tablename__ = "organization_units"

    id = Column(Integer, primary_key=True, index=True)
    unit_name = Column(String)
    category_id = Column(Integer)
    parent_unit_id = Column(Integer)
    leader_id = Column(Integer)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class User_organization_units(Base):
    __tablename__ = "user_organization_units"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer)
    unit_id = Column(Integer)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class Meeting_attendance(Base):
    __tablename__ = "meeting_attendance"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    meeting_type = Column(Enum(schemas.MeetingType), nullable=False)
    meeting_date = Column(Date, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())