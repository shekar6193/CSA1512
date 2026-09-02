from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict
from app.models import RequestPriority, RequestStatus, RequestCategory, UserRole

# Audit Log Schemas
class AuditLogBase(BaseModel):
    previous_status: Optional[str] = None
    new_status: str
    action: str
    actor_name: str
    actor_role: str
    notes: Optional[str] = None

class AuditLogOut(AuditLogBase):
    id: int
    request_id: int
    timestamp: datetime
    model_config = ConfigDict(from_attributes=True)

# Service Request Schemas
class ServiceRequestCreate(BaseModel):
    title: str = Field(..., min_length=3, max_length=200)
    category: str
    location: str = Field(..., min_length=2, max_length=255)
    building_name: str
    floor_room: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    description: str = Field(..., min_length=5)
    priority: Optional[str] = "MEDIUM"
    reporter_name: str = "Campus User"
    reporter_email: str = "user@campus.edu"
    reporter_role: Optional[str] = "STUDENT"
    evidence_url: Optional[str] = None

class ServiceRequestUpdateStatus(BaseModel):
    status: str
    resolution_notes: Optional[str] = None
    actor_name: str = "Staff Member"
    actor_role: str = "TECHNICIAN"

class ServiceRequestAssign(BaseModel):
    assigned_to: str
    assigned_team: Optional[str] = None
    actor_name: str = "Admin"
    actor_role: str = "ADMIN"
    notes: Optional[str] = None

class ServiceRequestOut(BaseModel):
    id: int
    ticket_code: str
    title: str
    category: str
    location: str
    building_name: str
    floor_room: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    description: str
    priority: str
    status: str
    reporter_name: str
    reporter_email: str
    reporter_role: str
    assigned_to: Optional[str] = None
    assigned_team: Optional[str] = None
    resolution_notes: Optional[str] = None
    sla_hours: int
    deadline_at: Optional[datetime] = None
    ai_confidence: float
    ai_triage_notes: Optional[str] = None
    is_emergency: bool
    evidence_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    resolved_at: Optional[datetime] = None
    audit_logs: List[AuditLogOut] = []

    model_config = ConfigDict(from_attributes=True)

# AI Triage Schemas
class TriageAnalysisRequest(BaseModel):
    title: str
    description: str
    category: Optional[str] = None
    location: Optional[str] = None

class TriageAnalysisResponse(BaseModel):
    recommended_priority: str
    is_emergency: bool
    confidence_score: float
    recommended_category: str
    detected_risk_keywords: List[str]
    suggested_sla_hours: int
    triage_rationale: str
    suggested_dispatch_team: str

# Campus Building Schemas
class CampusBuildingOut(BaseModel):
    id: int
    code: str
    name: str
    zone: str
    latitude: float
    longitude: float
    description: Optional[str] = None
    active_issues_count: int = 0

    model_config = ConfigDict(from_attributes=True)

# Analytics & Dashboard Schemas
class AnalyticsSummary(BaseModel):
    total_requests: int
    active_requests: int
    resolved_requests: int
    emergency_requests: int
    sla_compliance_rate: float
    mean_time_to_resolution_hours: float
    status_breakdown: dict
    priority_breakdown: dict
    category_breakdown: dict
    recent_activity: List[AuditLogOut]

# Health & System Schemas
class HealthCheckResponse(BaseModel):
    status: str
    version: str
    database_connected: bool
    timestamp: datetime
    active_websockets: int
