import enum
from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Text, Boolean, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from app.database import Base

class RequestPriority(str, enum.Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"
    EMERGENCY = "EMERGENCY"

class RequestStatus(str, enum.Enum):
    SUBMITTED = "SUBMITTED"
    TRIAGED = "TRIAGED"
    ASSIGNED = "ASSIGNED"
    IN_PROGRESS = "IN_PROGRESS"
    RESOLVED = "RESOLVED"
    CLOSED = "CLOSED"
    REJECTED = "REJECTED"

class RequestCategory(str, enum.Enum):
    ELECTRICAL = "Electrical"
    HVAC = "HVAC & Climate"
    PLUMBING = "Plumbing"
    IT_NETWORK = "IT & Network"
    SAFETY_SECURITY = "Safety & Security"
    SANITATION = "Sanitation & Cleaning"
    LAB_EQUIPMENT = "Lab Equipment"
    INFRASTRUCTURE = "Infrastructure & Civil"

class UserRole(str, enum.Enum):
    STUDENT = "STUDENT"
    FACULTY = "FACULTY"
    TECHNICIAN = "TECHNICIAN"
    SECURITY = "SECURITY"
    ADMIN = "ADMIN"

class ServiceRequest(Base):
    __tablename__ = "service_requests"

    id = Column(Integer, primary_key=True, index=True)
    ticket_code = Column(String(32), unique=True, index=True)
    title = Column(String(200), nullable=False)
    category = Column(String(64), nullable=False, index=True)
    location = Column(String(255), nullable=False)
    building_name = Column(String(128), nullable=False, index=True)
    floor_room = Column(String(64), nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    description = Column(Text, nullable=False)
    priority = Column(String(32), default=RequestPriority.MEDIUM.value, index=True)
    status = Column(String(32), default=RequestStatus.SUBMITTED.value, index=True)
    
    # Reporter details
    reporter_name = Column(String(128), nullable=False, default="Campus User")
    reporter_email = Column(String(128), nullable=False, default="user@campus.edu")
    reporter_role = Column(String(64), default=UserRole.STUDENT.value)

    # Workflow & Staff assignment
    assigned_to = Column(String(128), nullable=True)
    assigned_team = Column(String(128), nullable=True)
    resolution_notes = Column(Text, nullable=True)
    sla_hours = Column(Integer, default=24)
    deadline_at = Column(DateTime, nullable=True)
    
    # AI Innovation Fields
    ai_confidence = Column(Float, default=0.0)
    ai_triage_notes = Column(Text, nullable=True)
    is_emergency = Column(Boolean, default=False)
    evidence_url = Column(String(512), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)

    # Relationships
    audit_logs = relationship("AuditLog", back_populates="request", cascade="all, delete-orphan", order_by="AuditLog.timestamp.desc()")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    request_id = Column(Integer, ForeignKey("service_requests.id"), nullable=False, index=True)
    previous_status = Column(String(32), nullable=True)
    new_status = Column(String(32), nullable=False)
    action = Column(String(64), nullable=False)
    actor_name = Column(String(128), nullable=False)
    actor_role = Column(String(64), nullable=False)
    notes = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)

    request = relationship("ServiceRequest", back_populates="audit_logs")


class CampusBuilding(Base):
    __tablename__ = "campus_buildings"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(16), unique=True, index=True)
    name = Column(String(128), nullable=False)
    zone = Column(String(64), nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    description = Column(String(255), nullable=True)
    active_issues_count = Column(Integer, default=0)


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(64), unique=True, index=True)
    full_name = Column(String(128), nullable=False)
    email = Column(String(128), unique=True, index=True)
    role = Column(String(32), default=UserRole.STUDENT.value)
    department = Column(String(128), nullable=True)
