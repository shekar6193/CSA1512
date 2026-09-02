from datetime import datetime
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.database import get_db
from app.models import ServiceRequest, AuditLog, CampusBuilding, User, RequestStatus, UserRole
from app.schemas import (
    ServiceRequestOut,
    ServiceRequestUpdateStatus,
    ServiceRequestAssign,
    AuditLogOut
)
from app.services.notification_service import notification_hub

router = APIRouter(prefix="/staff", tags=["Staff Incident Management"])

@router.patch("/requests/{request_id}/status", response_model=ServiceRequestOut)
async def update_request_status(
    request_id: int,
    status_in: ServiceRequestUpdateStatus,
    db: Session = Depends(get_db)
):
    """
    Update service request lifecycle status and append to immutable audit log.
    Accepts: SUBMITTED, TRIAGED, ASSIGNED, IN_PROGRESS, RESOLVED, CLOSED, REJECTED.
    """
    req = db.query(ServiceRequest).filter(ServiceRequest.id == request_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Service request not found")

    old_status = req.status
    new_status = status_in.status.upper()

    # Validate status enum
    if new_status not in RequestStatus.__members__:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid status '{new_status}'. Allowed: {list(RequestStatus.__members__.keys())}"
        )

    req.status = new_status
    if status_in.resolution_notes:
        req.resolution_notes = status_in.resolution_notes

    # Set resolved timestamp if marked RESOLVED or CLOSED
    if new_status in [RequestStatus.RESOLVED.value, RequestStatus.CLOSED.value] and not req.resolved_at:
        req.resolved_at = datetime.utcnow()
    elif new_status not in [RequestStatus.RESOLVED.value, RequestStatus.CLOSED.value]:
        req.resolved_at = None

    # Record Audit Log
    audit_log = AuditLog(
        request_id=req.id,
        previous_status=old_status,
        new_status=new_status,
        action="STATUS_CHANGE",
        actor_name=status_in.actor_name,
        actor_role=status_in.actor_role,
        notes=status_in.resolution_notes or f"Status changed from {old_status} to {new_status}",
        timestamp=datetime.utcnow()
    )
    db.add(audit_log)

    # Recalculate building active issues count
    building = db.query(CampusBuilding).filter(CampusBuilding.name == req.building_name).first()
    if building:
        active_count = db.query(ServiceRequest).filter(
            ServiceRequest.building_name == building.name,
            ServiceRequest.status.notin_([RequestStatus.RESOLVED.value, RequestStatus.CLOSED.value, RequestStatus.REJECTED.value])
        ).count()
        building.active_issues_count = active_count

    db.commit()
    db.refresh(req)

    # Broadcast status change via WebSocket
    await notification_hub.broadcast("STATUS_UPDATED", {
        "id": req.id,
        "ticket_code": req.ticket_code,
        "title": req.title,
        "old_status": old_status,
        "new_status": new_status,
        "actor_name": status_in.actor_name,
        "actor_role": status_in.actor_role,
        "resolution_notes": status_in.resolution_notes
    })

    return req

@router.patch("/requests/{request_id}/assign", response_model=ServiceRequestOut)
async def assign_request(
    request_id: int,
    assign_in: ServiceRequestAssign,
    db: Session = Depends(get_db)
):
    """
    Assign a service request to a specific field technician or emergency dispatch team.
    """
    req = db.query(ServiceRequest).filter(ServiceRequest.id == request_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Service request not found")

    old_assigned = req.assigned_to
    req.assigned_to = assign_in.assigned_to
    if assign_in.assigned_team:
        req.assigned_team = assign_in.assigned_team

    # If status is SUBMITTED or TRIAGED, auto-progress to ASSIGNED
    if req.status in [RequestStatus.SUBMITTED.value, RequestStatus.TRIAGED.value]:
        req.status = RequestStatus.ASSIGNED.value

    # Record Audit Log
    audit_log = AuditLog(
        request_id=req.id,
        previous_status=req.status,
        new_status=req.status,
        action="ASSIGNMENT_CHANGE",
        actor_name=assign_in.actor_name,
        actor_role=assign_in.actor_role,
        notes=assign_in.notes or f"Assigned to {assign_in.assigned_to} ({assign_in.assigned_team or 'General Facilities'})",
        timestamp=datetime.utcnow()
    )
    db.add(audit_log)

    db.commit()
    db.refresh(req)

    # Broadcast assignment update via WebSocket
    await notification_hub.broadcast("TICKET_ASSIGNED", {
        "id": req.id,
        "ticket_code": req.ticket_code,
        "assigned_to": req.assigned_to,
        "assigned_team": req.assigned_team,
        "status": req.status
    })

    return req

@router.get("/requests/{request_id}/audit-logs", response_model=List[AuditLogOut])
def get_request_audit_logs(request_id: int, db: Session = Depends(get_db)):
    """
    Retrieve the complete, immutable change history for a given ticket.
    """
    logs = db.query(AuditLog).filter(AuditLog.request_id == request_id).order_by(desc(AuditLog.timestamp)).all()
    return logs

@router.get("/technicians")
def list_technicians_and_workload(db: Session = Depends(get_db)):
    """
    List all staff technicians and their current active workload.
    """
    staff_users = db.query(User).filter(
        User.role.in_([UserRole.TECHNICIAN.value, UserRole.SECURITY.value, UserRole.ADMIN.value])
    ).all()

    workload = []
    for user in staff_users:
        open_count = db.query(ServiceRequest).filter(
            ServiceRequest.assigned_to == user.full_name,
            ServiceRequest.status.notin_([RequestStatus.RESOLVED.value, RequestStatus.CLOSED.value, RequestStatus.REJECTED.value])
        ).count()

        workload.append({
            "id": user.id,
            "username": user.username,
            "full_name": user.full_name,
            "email": user.email,
            "role": user.role,
            "department": user.department,
            "active_assigned_tasks": open_count
        })

    return workload
