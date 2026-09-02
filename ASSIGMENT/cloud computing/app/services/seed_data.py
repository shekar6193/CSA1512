from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.models import ServiceRequest, AuditLog, CampusBuilding, User, RequestPriority, RequestStatus, UserRole

def seed_database(db: Session):
    """Seed initial smart campus buildings, staff users, and sample service requests."""
    
    # 1. Seed Campus Buildings
    if db.query(CampusBuilding).count() == 0:
        buildings = [
            CampusBuilding(code="ENG-01", name="Engineering Complex", zone="North Quad", latitude=37.7758, longitude=-122.4194, description="Computer Science, Electrical & Mechanical Labs"),
            CampusBuilding(code="SCI-02", name="Science & Biotech Park", zone="West Quad", latitude=37.7770, longitude=-122.4225, description="Chemistry, Biology & Material Science Research Facilities"),
            CampusBuilding(code="LIB-01", name="Central University Library", zone="Central Quad", latitude=37.7740, longitude=-122.4180, description="Main 5-story study commons, digital archive, and cafe"),
            CampusBuilding(code="SAC-01", name="Student Activity Center", zone="South Quad", latitude=37.7720, longitude=-122.4175, description="Dining hall, student union, recreation and event auditoriums"),
            CampusBuilding(code="ADM-01", name="Main Administrative Hall", zone="Central Quad", latitude=37.7745, longitude=-122.4155, description="Registrar, Provost, Financial Aid and Campus Operations"),
            CampusBuilding(code="RES-01", name="North Residential Quad", zone="North Quad", latitude=37.7785, longitude=-122.4180, description="Undergraduate student dormitory blocks A, B & C"),
            CampusBuilding(code="SPT-01", name="Campus Sports Complex", zone="East Quad", latitude=37.7728, longitude=-122.4130, description="Indoor gymnasium, Olympic swimming pool, and athletic track"),
            CampusBuilding(code="MED-01", name="Campus Health & Medical", zone="South Quad", latitude=37.7712, longitude=-122.4215, description="24/7 First aid, student clinic, and emergency response center")
        ]
        db.add_all(buildings)
        db.commit()

    # 2. Seed Default Staff & Demo Users
    if db.query(User).count() == 0:
        users = [
            User(username="alex.student", full_name="Alex Rivera", email="alex.r@campus.edu", role=UserRole.STUDENT.value, department="Computer Science"),
            User(username="dr.chen", full_name="Dr. Elena Chen", email="echen@campus.edu", role=UserRole.FACULTY.value, department="Bioengineering"),
            User(username="tech.dave", full_name="Dave Miller", email="dmiller@facilities.campus.edu", role=UserRole.TECHNICIAN.value, department="Electrical & HVAC"),
            User(username="tech.sarah", full_name="Sarah Jenkins", email="sjenkins@facilities.campus.edu", role=UserRole.TECHNICIAN.value, department="Plumbing & Hydrology"),
            User(username="sec.rodriguez", full_name="Officer Carlos Rodriguez", email="crodriguez@security.campus.edu", role=UserRole.SECURITY.value, department="Campus Police & Safety"),
            User(username="admin.clara", full_name="Clara Oswald", email="admin@campus.edu", role=UserRole.ADMIN.value, department="Facilities Operations & Dispatch")
        ]
        db.add_all(users)
        db.commit()

    # 3. Seed Realistic Sample Service Requests if none exist
    if db.query(ServiceRequest).count() == 0:
        now = datetime.utcnow()
        sample_requests = [
            {
                "ticket_code": "CP-2026-001",
                "title": "HVAC Chiller emitting dense smoke in Server Room B",
                "category": "HVAC & Climate",
                "location": "Engineering Complex, Room 204B",
                "building_name": "Engineering Complex",
                "floor_room": "2nd Floor, Server Room B",
                "latitude": 37.7758,
                "longitude": -122.4194,
                "description": "High temperature alarm triggered. The main cooling compressor unit is smoking and making a grinding screech.",
                "priority": RequestPriority.CRITICAL.value,
                "status": RequestStatus.IN_PROGRESS.value,
                "reporter_name": "Alex Rivera",
                "reporter_email": "alex.r@campus.edu",
                "reporter_role": UserRole.STUDENT.value,
                "assigned_to": "Dave Miller",
                "assigned_team": "HVAC Operations Unit",
                "sla_hours": 2,
                "deadline_at": now + timedelta(hours=1),
                "ai_confidence": 0.96,
                "ai_triage_notes": "🚨 CRITICAL ALERT: Detected high-risk keyword 'smoke' and thermal failure in critical infrastructure.",
                "is_emergency": True,
                "created_at": now - timedelta(hours=1, minutes=30),
                "audit": [
                    ("SUBMITTED", "System AI Triage", "SYSTEM", "Automated intake and triage. Escalated to CRITICAL due to smoke keyword."),
                    ("TRIAGED", "Clara Oswald", "ADMIN", "Triage confirmed. Dispatched HVAC emergency crew."),
                    ("IN_PROGRESS", "Dave Miller", "TECHNICIAN", "Arrived on scene, isolated power to compressor unit.")
                ]
            },
            {
                "ticket_code": "CP-2026-002",
                "title": "Major water pipe leak causing floor flooding on 3rd Floor",
                "category": "Plumbing",
                "location": "Central University Library, 3rd Floor Restrooms",
                "building_name": "Central University Library",
                "floor_room": "3rd Floor West Restroom",
                "latitude": 37.7740,
                "longitude": -122.4180,
                "description": "Pressurized main line connector burst. Water is gushing into the hallway carpet and study cubicles.",
                "priority": RequestPriority.HIGH.value,
                "status": RequestStatus.ASSIGNED.value,
                "reporter_name": "Dr. Elena Chen",
                "reporter_email": "echen@campus.edu",
                "reporter_role": UserRole.FACULTY.value,
                "assigned_to": "Sarah Jenkins",
                "assigned_team": "Plumbing & Hydrology Team",
                "sla_hours": 8,
                "deadline_at": now + timedelta(hours=6),
                "ai_confidence": 0.91,
                "ai_triage_notes": "High priority plumbing alert. Detected risk keywords: 'water leak', 'flooding', 'burst pipe'.",
                "is_emergency": False,
                "created_at": now - timedelta(hours=2),
                "audit": [
                    ("SUBMITTED", "System AI Triage", "SYSTEM", "Intake recorded."),
                    ("ASSIGNED", "Clara Oswald", "ADMIN", "Assigned to Sarah Jenkins (Plumbing). Main shutoff valve locator notified.")
                ]
            },
            {
                "ticket_code": "CP-2026-003",
                "title": "Campus WiFi Access Point offline in Student Dining Commons",
                "category": "IT & Network",
                "location": "Student Activity Center, Dining Hall West",
                "building_name": "Student Activity Center",
                "floor_room": "Ground Floor Dining Hub",
                "latitude": 37.7720,
                "longitude": -122.4175,
                "description": "AP-SAC-04 is blinking amber and not broadcasting SSID 'CampusSecure'. Students unable to connect.",
                "priority": RequestPriority.MEDIUM.value,
                "status": RequestStatus.SUBMITTED.value,
                "reporter_name": "Alex Rivera",
                "reporter_email": "alex.r@campus.edu",
                "reporter_role": UserRole.STUDENT.value,
                "assigned_to": None,
                "assigned_team": "Network Operations Center (NOC)",
                "sla_hours": 24,
                "deadline_at": now + timedelta(hours=22),
                "ai_confidence": 0.88,
                "ai_triage_notes": "Standard IT network connectivity ticket. Routed to NOC.",
                "is_emergency": False,
                "created_at": now - timedelta(hours=2, minutes=15),
                "audit": [
                    ("SUBMITTED", "System Intake", "SYSTEM", "Request submitted by student.")
                ]
            },
            {
                "ticket_code": "CP-2026-004",
                "title": "Broken glass door handle and jammed latch in North Quad Dorm B",
                "category": "Infrastructure & Civil",
                "location": "North Residential Quad, Block B Entrance",
                "building_name": "North Residential Quad",
                "floor_room": "Entry Lobby B-101",
                "latitude": 37.7785,
                "longitude": -122.4180,
                "description": "Main entry magnetic latch is misaligned, causing keycards to fail and door to stick open.",
                "priority": RequestPriority.HIGH.value,
                "status": RequestStatus.RESOLVED.value,
                "reporter_name": "Dave Miller",
                "reporter_email": "dmiller@facilities.campus.edu",
                "reporter_role": UserRole.TECHNICIAN.value,
                "assigned_to": "Dave Miller",
                "assigned_team": "Facilities Carpentry & Structural",
                "resolution_notes": "Realigned magnetic striker plate, replaced tension spring, and tested RFID pass 20 times. Fully operational.",
                "sla_hours": 8,
                "deadline_at": now - timedelta(hours=4),
                "resolved_at": now - timedelta(hours=3),
                "ai_confidence": 0.85,
                "ai_triage_notes": "Infrastructure access & security issue.",
                "is_emergency": False,
                "created_at": now - timedelta(hours=12),
                "audit": [
                    ("SUBMITTED", "System Intake", "SYSTEM", "Request logged."),
                    ("ASSIGNED", "Clara Oswald", "ADMIN", "Assigned to Dave Miller."),
                    ("IN_PROGRESS", "Dave Miller", "TECHNICIAN", "Replacing latch hardware."),
                    ("RESOLVED", "Dave Miller", "TECHNICIAN", "Striker plate aligned, door tested and operational.")
                ]
            },
            {
                "ticket_code": "CP-2026-005",
                "title": "Fume Hood airflow alarm buzzing in Organic Chemistry Lab 301",
                "category": "Lab Equipment",
                "location": "Science & Biotech Park, Lab 301",
                "building_name": "Science & Biotech Park",
                "floor_room": "3rd Floor, Organic Chem 301",
                "latitude": 37.7770,
                "longitude": -122.4225,
                "description": "Exhaust face velocity dropped below 80 FPM. Audible warning siren active. Lab currently evacuated.",
                "priority": RequestPriority.CRITICAL.value,
                "status": RequestStatus.TRIAGED.value,
                "reporter_name": "Dr. Elena Chen",
                "reporter_email": "echen@campus.edu",
                "reporter_role": UserRole.FACULTY.value,
                "assigned_to": None,
                "assigned_team": "Environmental Health & Hazardous Safety",
                "sla_hours": 2,
                "deadline_at": now + timedelta(hours=1, minutes=45),
                "ai_confidence": 0.94,
                "ai_triage_notes": "🚨 Safety Hazard: Fume hood airflow failure in chemistry facility. Immediate EH&S response required.",
                "is_emergency": True,
                "created_at": now - timedelta(minutes=25),
                "audit": [
                    ("SUBMITTED", "System Intake", "SYSTEM", "Automated intake with hazardous classification."),
                    ("TRIAGED", "Officer Carlos Rodriguez", "SECURITY", "Confirmed lab evacuation. Security perimeter established.")
                ]
            }
        ]

        for item in sample_requests:
            audit_steps = item.pop("audit")
            req = ServiceRequest(**item)
            db.add(req)
            db.flush()

            prev_st = None
            for st, actor, role, notes in audit_steps:
                log = AuditLog(
                    request_id=req.id,
                    previous_status=prev_st,
                    new_status=st,
                    action="STATUS_CHANGE" if prev_st else "TICKET_CREATED",
                    actor_name=actor,
                    actor_role=role,
                    notes=notes,
                    timestamp=req.created_at + timedelta(minutes=10)
                )
                db.add(log)
                prev_st = st
        
        db.commit()

        # Update building active issues count
        for b in db.query(CampusBuilding).all():
            count = db.query(ServiceRequest).filter(
                ServiceRequest.building_name == b.name,
                ServiceRequest.status.notin_([RequestStatus.RESOLVED.value, RequestStatus.CLOSED.value, RequestStatus.REJECTED.value])
            ).count()
            b.active_issues_count = count
        db.commit()
