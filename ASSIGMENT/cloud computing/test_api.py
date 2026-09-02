import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database import Base, engine, SessionLocal
from app.services.seed_data import seed_database

client = TestClient(app)

@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    seed_database(db)
    db.close()

def test_health_check_liveness():
    """Verify cloud liveness probe."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ["healthy", "degraded"]
    assert "version" in data
    assert data["database_connected"] is True

def test_health_check_readiness():
    """Verify Kubernetes readiness probe."""
    response = client.get("/api/v1/health/ready")
    assert response.status_code == 200
    assert response.json()["ready"] is True

def test_prometheus_metrics():
    """Verify Prometheus telemetry endpoint."""
    response = client.get("/api/v1/metrics")
    assert response.status_code == 200
    assert "campuspulse_http_requests_total" in response.text

def test_list_service_requests():
    """Verify listing service requests with filters."""
    response = client.get("/api/v1/requests")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0
    # Check ticket structure
    first = data[0]
    assert "ticket_code" in first
    assert "title" in first
    assert "category" in first
    assert "priority" in first
    assert "status" in first

def test_create_service_request():
    """Verify creating a new service request."""
    payload = {
        "title": "Air filter replacement in Biology Lab",
        "category": "HVAC & Climate",
        "building_name": "Science & Biotech Park",
        "floor_room": "Lab 102",
        "location": "Science & Biotech Park, Lab 102",
        "priority": "MEDIUM",
        "description": "The HEPA filter is due for routine scheduled maintenance and replacement.",
        "reporter_name": "Dr. Elena Chen",
        "reporter_email": "echen@campus.edu",
        "reporter_role": "FACULTY"
    }
    response = client.post("/api/v1/requests", json=payload)
    assert response.status_code == 201
    created = response.json()
    assert created["ticket_code"].startswith("CP-")
    assert created["status"] == "SUBMITTED"
    assert created["sla_hours"] == 24
    assert len(created["audit_logs"]) >= 1

def test_ai_emergency_triage_escalation():
    """Verify AI Triage automatically flags critical hazards and escalates priority."""
    payload = {
        "title": "Severe gas leak and strong odor near chemistry store",
        "description": "Gas valve is hissing with thick fumes spreading into corridor. Possible explosion risk.",
        "category": "Safety & Security"
    }
    response = client.post("/api/v1/triage/analyze", json=payload)
    assert response.status_code == 200
    triage = response.json()
    assert triage["is_emergency"] is True
    assert triage["recommended_priority"] in ["EMERGENCY", "CRITICAL"]
    assert triage["suggested_sla_hours"] <= 2
    assert len(triage["detected_risk_keywords"]) > 0

def test_update_request_status_and_audit():
    """Verify updating request status creates immutable audit log entries."""
    # 1. Fetch first request
    res = client.get("/api/v1/requests")
    req_id = res.json()[0]["id"]

    # 2. Update status
    update_payload = {
        "status": "IN_PROGRESS",
        "resolution_notes": "Technician on site inspecting components.",
        "actor_name": "Dave Miller",
        "actor_role": "TECHNICIAN"
    }
    patch_res = client.patch(f"/api/v1/staff/requests/{req_id}/status", json=update_payload)
    assert patch_res.status_code == 200
    updated = patch_res.json()
    assert updated["status"] == "IN_PROGRESS"
    assert updated["resolution_notes"] == update_payload["resolution_notes"]

    # 3. Check audit logs
    audit_res = client.get(f"/api/v1/staff/requests/{req_id}/audit-logs")
    assert audit_res.status_code == 200
    logs = audit_res.json()
    assert len(logs) >= 1
    assert logs[0]["new_status"] == "IN_PROGRESS"
    assert logs[0]["actor_name"] == "Dave Miller"

def test_assign_technician():
    """Verify assigning a technician to a ticket."""
    res = client.get("/api/v1/requests")
    req_id = res.json()[0]["id"]

    assign_payload = {
        "assigned_to": "Dave Miller",
        "assigned_team": "Electrical Rapid Response",
        "actor_name": "Clara Oswald",
        "actor_role": "ADMIN"
    }
    assign_res = client.patch(f"/api/v1/staff/requests/{req_id}/assign", json=assign_payload)
    assert assign_res.status_code == 200
    data = assign_res.json()
    assert data["assigned_to"] == "Dave Miller"
    assert data["assigned_team"] == "Electrical Rapid Response"

def test_analytics_summary():
    """Verify analytics KPI calculations."""
    response = client.get("/api/v1/analytics/summary")
    assert response.status_code == 200
    summary = response.json()
    assert "total_requests" in summary
    assert "active_requests" in summary
    assert "sla_compliance_rate" in summary
    assert "mean_time_to_resolution_hours" in summary
    assert "category_breakdown" in summary

def test_campus_buildings():
    """Verify campus buildings and coordinates endpoint."""
    response = client.get("/api/v1/requests/buildings")
    assert response.status_code == 200
    buildings = response.json()
    assert len(buildings) >= 8
    assert "latitude" in buildings[0]
    assert "longitude" in buildings[0]

if __name__ == "__main__":
    pytest.main(["-v", __file__])
