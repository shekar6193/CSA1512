import os
import uuid
import aiofiles
from datetime import datetime, timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, status
from sqlalchemy.orm import Session
from sqlalchemy import or_, desc

from app.database import get_db
from app.config import settings
from app.models import ServiceRequest, AuditLog, CampusBuilding, RequestStatus, RequestPriority
from app.schemas import (
    ServiceRequestCreate,
    ServiceRequestOut,
    CampusBuildingOut
)
from app.services.triage_service import TriageEngine
from app.services.notification_service import notification_hub

router = APIRouter(prefix="/requests", tags=["Service Requests"])

def generate_ticket_code(db: Session) -> str:
    count = db.query(ServiceRequest).count() + 1
    year = datetime.utcnow().year
    return f"CP-{year}-{count:04d}"

@router.post("", response_model=ServiceRequestOut, status_code=status.HTTP_201_CREATED)
async def create_service_request(
    request_in: ServiceRequestCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new campus service request or incident report.
    Automatically evaluates incident description with AI Triage Engine,
    computes SLA deadline, persists to database, and broadcasts to staff.
    """
    # Run AI Triage Engine
    triage_result = TriageEngine.analyze(
        title=request_in.title,
        description=request_in.description,
        current_category=request_in.category
    )

    # Determine final priority & SLA
    priority = request_in.priority
    if triage_result.is_emergency and priority not in ["CRITICAL", "EMERGENCY"]:
        priority = triage_result.recommended_priority

    sla_hours = settings.SLA_HOURS.get(priority, 24)
    deadline_at = datetime.utcnow() + timedelta(hours=sla_hours)

    ticket_code = generate_ticket_code(db)

    # If building GPS not supplied, lookup building
    lat = request_in.latitude
    lng = request_in.longitude
    if lat is None or lng is None:
        building = db.query(CampusBuilding).filter(CampusBuilding.name == request_in.building_name).first()
        if building:
            lat = building.latitude
            lng = building.longitude

    new_request = ServiceRequest(
        ticket_code=ticket_code,
        title=request_in.title,
        category=request_in.category or triage_result.recommended_category,
        location=request_in.location,
        building_name=request_in.building_name,
        floor_room=request_in.floor_room,
        latitude=lat,
        longitude=lng,
        description=request_in.description,
        priority=priority,
        status=RequestStatus.SUBMITTED.value,
        reporter_name=request_in.reporter_name,
        reporter_email=request_in.reporter_email,
        reporter_role=request_in.reporter_role or "STUDENT",
        assigned_team=triage_result.suggested_dispatch_team,
        sla_hours=sla_hours,
        deadline_at=deadline_at,
        ai_confidence=triage_result.confidence_score,
        ai_triage_notes=triage_result.triage_rationale,
        is_emergency=triage_result.is_emergency,
        evidence_url=request_in.evidence_url,
        created_at=datetime.utcnow()
    )

    db.add(new_request)
    db.flush()

    # Initial Audit Trail
    audit_entry = AuditLog(
        request_id=new_request.id,
        previous_status=None,
        new_status=RequestStatus.SUBMITTED.value,
        action="TICKET_CREATED",
        actor_name=request_in.reporter_name,
        actor_role=request_in.reporter_role or "STUDENT",
        notes=f"Service request submitted. AI Triage: {triage_result.triage_rationale}",
        timestamp=datetime.utcnow()
    )
    db.add(audit_entry)

    # Update building active issues count
    building = db.query(CampusBuilding).filter(CampusBuilding.name == request_in.building_name).first()
    if building:
        building.active_issues_count = (building.active_issues_count or 0) + 1

    db.commit()
    db.refresh(new_request)

    # Broadcast real-time event via WebSocket
    await notification_hub.broadcast("REQUEST_CREATED", {
        "id": new_request.id,
        "ticket_code": new_request.ticket_code,
        "title": new_request.title,
        "category": new_request.category,
        "building_name": new_request.building_name,
        "priority": new_request.priority,
        "status": new_request.status,
        "is_emergency": new_request.is_emergency
    })

    return new_request

@router.get("", response_model=List[ServiceRequestOut])
def list_service_requests(
    category: Optional[str] = None,
    status_filter: Optional[str] = Query(None, alias="status"),
    priority: Optional[str] = None,
    building_name: Optional[str] = None,
    search: Optional[str] = None,
    emergency_only: Optional[bool] = False,
    limit: int = Query(100, le=500),
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """
    List, filter, and search campus service requests with pagination and criteria filters.
    """
    query = db.query(ServiceRequest)

    if category:
        query = query.filter(ServiceRequest.category == category)
    if status_filter:
        query = query.filter(ServiceRequest.status == status_filter)
    if priority:
        query = query.filter(ServiceRequest.priority == priority)
    if building_name:
        query = query.filter(ServiceRequest.building_name == building_name)
    if emergency_only:
        query = query.filter(ServiceRequest.is_emergency == True)
    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            or_(
                ServiceRequest.title.ilike(search_pattern),
                ServiceRequest.description.ilike(search_pattern),
                ServiceRequest.ticket_code.ilike(search_pattern),
                ServiceRequest.location.ilike(search_pattern),
                ServiceRequest.reporter_name.ilike(search_pattern)
            )
        )

    # Order by Emergency/Critical first, then newest
    requests = query.order_by(
        desc(ServiceRequest.is_emergency),
        desc(ServiceRequest.created_at)
    ).offset(offset).limit(limit).all()

    return requests

@router.get("/buildings", response_model=List[CampusBuildingOut])
def get_campus_buildings(db: Session = Depends(get_db)):
    """
    Retrieve all campus buildings with real-time active incident counts and coordinates.
    """
    return db.query(CampusBuilding).all()

@router.get("/{request_id}", response_model=ServiceRequestOut)
def get_service_request(request_id: int, db: Session = Depends(get_db)):
    """
    Get detailed information and full audit trail for a specific service request.
    """
    req = db.query(ServiceRequest).filter(ServiceRequest.id == request_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Service request not found")
    return req

@router.delete("/{request_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_service_request(request_id: int, db: Session = Depends(get_db)):
    """
    Delete a service request (Admin only).
    """
    req = db.query(ServiceRequest).filter(ServiceRequest.id == request_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Service request not found")
    
    db.delete(req)
    db.commit()

    await notification_hub.broadcast("REQUEST_DELETED", {"id": request_id})
    return None

@router.post("/upload-evidence")
async def upload_evidence(file: UploadFile = File(...)):
    """
    Upload image or document evidence for a service request.
    Stores file securely and returns public access URL.
    """
    allowed_exts = {".jpg", ".jpeg", ".png", ".webp", ".pdf", ".gif"}
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in allowed_exts:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file format '{ext}'. Allowed: {', '.join(allowed_exts)}"
        )

    file_id = f"{uuid.uuid4().hex[:12]}{ext}"
    file_path = os.path.join(settings.UPLOAD_DIR, file_id)

    async with aiofiles.open(file_path, 'wb') as out_file:
        content = await file.read()
        await out_file.write(content)

    return {
        "filename": file.filename,
        "file_url": f"/uploads/{file_id}",
        "size_bytes": len(content)
    }
