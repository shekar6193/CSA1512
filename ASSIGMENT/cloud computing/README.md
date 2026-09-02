# CampusPulse Cloud: Smart Campus Service Request & Incident Response Platform

[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688.svg?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Python](https://img.shields.io/badge/Python-3.11%20|%203.12%20|%203.14-blue.svg?logo=python&logoColor=white)](https://python.org)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED.svg?logo=docker&logoColor=white)](https://www.docker.com/)
[![Kubernetes](https://img.shields.io/badge/Kubernetes-K8s-326CE5.svg?logo=kubernetes&logoColor=white)](https://kubernetes.io/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

A modern, cloud-ready **Smart Campus Service Request and Incident Response Platform**. The platform allows campus users (students, faculty, guests) to report incidents with category, location, description, priority, and photo evidence; empowers facilities and security staff to manage dispatch workflows, assign technicians, and record status transitions; preserves request data with persistent database storage and immutable audit trails; and exposes all operations through high-performance REST APIs and real-time WebSockets.

---

## 🌟 Distinct Faculty Innovations & Enhancements

This project includes multi-faceted faculty innovations exceeding standard requirements:

1. **AI-Powered Emergency Prioritization & NLP Triage Engine**:
   - Analyzes reported incident text in real-time.
   - Detects safety hazards (fires, gas leaks, electrical sparking, toxic spills, lift entrapments).
   - Automatically escalates priority to `CRITICAL` or `EMERGENCY` with accelerated 1-hour/2-hour SLA targets.
   - Automatically routes tickets to specialized dispatch teams (e.g. *Environmental Health & Hazardous Safety*, *Emergency Electrical Response*).

2. **Interactive Real-Time GIS Campus Map & Heatmaps**:
   - Leaflet.js-powered geospatial map of campus buildings with live incident pins color-coded by severity.
   - Click-to-pin location selection for report submission.
   - Building-level active issue density tracking.

3. **Real-Time WebSocket Notification Bus**:
   - Zero-refresh live event streaming (`/ws/events`) broadcasting new requests, status changes, and emergency alerts to connected dashboards.

4. **Predictive Workload & SLA Analytics**:
   - Computes Mean Time to Resolution (MTTR), SLA compliance rate, category breakdowns, and building reliability rankings with Chart.js.

5. **Multilingual Access & WCAG 2.1 Accessibility**:
   - Instant localization across **5 languages**: English, Español, हिन्दी (Hindi), తెలుగు (Telugu), Français.
   - High-contrast toggle and screen-reader compliant semantic HTML.

6. **Cloud Portability & Telemetry**:
   - Multi-stage `Dockerfile`, `docker-compose.yml`, Kubernetes manifests (`deployment.yaml`, `service.yaml`, `hpa.yaml`, `configmap.yaml`).
   - Prometheus metrics endpoint (`/api/v1/metrics`) and cloud health probes (`/api/v1/health`, `/api/v1/health/ready`).

---

## 👥 Team Member Module Ownership Matrix

| Module / Responsibility | Team Member | Key Deliverables & Code Artifacts |
| :--- | :--- | :--- |
| **Module 1: Backend Architecture & REST API** | **Team Member 1** | FastAPI app initialization, Pydantic data schemas (`schemas.py`), SQLAlchemy ORM models (`models.py`), database persistence (`database.py`), OpenAPI specification (`/docs`). |
| **Module 2: Request Submission & GIS Portal** | **Team Member 2** | User incident creation form, Leaflet GIS campus map (`map.js`), photo evidence upload (`/upload-evidence`), multilingual localization (`i18n.js`). |
| **Module 3: Staff Incident Dispatch & Workflow Engine** | **Team Member 3** | Status state machine (`SUBMITTED` &rarr; `CLOSED`), technician assignment, role switching (`app.js`), immutable audit logging (`AuditLog`). |
| **Module 4: AI Triage, Analytics & Cloud Ops** | **Team Member 4** | NLP emergency classifier (`triage_service.py`), MTTR analytics (`analytics.py`, `charts.js`), WebSocket broadcaster (`ws.js`), Docker & Kubernetes manifests. |

---

## 🏗️ System Architecture

```
                                    +-----------------------------------------+
                                    |         Web Browser / Mobile Client     |
                                    |  (Tailwind + Leaflet GIS + Chart.js)   |
                                    +--------------------+--------------------+
                                                         | HTTP REST / WebSocket
                                                         v
+---------------------------------------------------------------------------------------------------------+
|                                    FastAPI ASGI Application Server                                      |
|                                                                                                         |
|  +---------------------+   +---------------------+   +----------------------+   +--------------------+  |
|  | Request Controller  |   |   Staff Dispatch    |   | AI NLP Triage Engine |   | WebSocket Event Hub|  |
|  | (/api/v1/requests)  |   |  (/api/v1/staff)    |   | (/api/v1/triage)     |   | (/ws/events)       |  |
|  +----------+----------+   +----------+----------+   +----------+-----------+   +---------+----------+  |
|             |                         |                         |                         |             |
|             +-------------------------+-------------------------+-------------------------+             |
|                                       |                                                                 |
|                                       v                                                                 |
|                      +---------------------------------+                                                |
|                      |         SQLAlchemy ORM          |                                                |
|                      +----------------+----------------+                                                |
+---------------------------------------|-----------------------------------------------------------------+
                                        v
                       +---------------------------------+
                       | Database Storage (SQLite /      |
                       | PostgreSQL) + Evidence Files    |
                       +---------------------------------+
```

---

## 🚀 Getting Started

### Prerequisites
- Python 3.10+ installed
- *(Optional)* Docker & Docker Compose

### 1. Local Quick Start (Zero Config)

#### Windows:
Double-click `run.bat` or run:
```powershell
python -m pip install -r requirements.txt email-validator
python main.py
```

#### Linux / macOS:
```bash
chmod +x run.sh
./run.sh
```

Open your browser at:
- **Web Application**: [http://localhost:8000](http://localhost:8000)
- **Interactive Swagger REST API Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc API Documentation**: [http://localhost:8000/redoc](http://localhost:8000/redoc)
- **Cloud Liveness Health Probe**: [http://localhost:8000/api/v1/health](http://localhost:8000/api/v1/health)
- **Prometheus Metrics**: [http://localhost:8000/api/v1/metrics](http://localhost:8000/api/v1/metrics)

---

## 🧪 Running Automated Tests

Run the complete test suite verifying all 10 endpoint scenarios:
```bash
python -m pytest test_api.py -v
```

---

## 🐳 Container & Cloud Deployment

### 1. Docker Compose
Run the entire platform inside an isolated container with persistent storage:
```bash
docker-compose up --build -d
```

### 2. Standalone Docker
```bash
docker build -t campuspulse:latest .
docker run -p 8000:8000 --name campuspulse campuspulse:latest
```

### 3. Kubernetes (K8s) Cluster Deployment
Deploy to any Kubernetes cluster (Minikube, GKE, EKS, AKS):
```bash
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
kubectl apply -f k8s/hpa.yaml
kubectl apply -f k8s/ingress.yaml
```

---

## 📡 REST API Reference Summary

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/api/v1/requests` | Create a new service request with AI triage & SLA calculation |
| `GET` | `/api/v1/requests` | List & filter service requests (category, status, priority, building, search) |
| `GET` | `/api/v1/requests/{id}` | Get specific request details and full audit log |
| `DELETE` | `/api/v1/requests/{id}` | Delete a service request |
| `POST` | `/api/v1/requests/upload-evidence` | Upload photo/document evidence attachment |
| `GET` | `/api/v1/requests/buildings` | List all campus buildings with coordinates and active issue counts |
| `PATCH` | `/api/v1/staff/requests/{id}/status` | Update lifecycle status and append to immutable audit log |
| `PATCH` | `/api/v1/staff/requests/{id}/assign` | Assign field technician or emergency dispatch team |
| `GET` | `/api/v1/staff/requests/{id}/audit-logs` | Retrieve complete audit trail for a ticket |
| `GET` | `/api/v1/staff/technicians` | List all staff technicians and their current workload |
| `POST` | `/api/v1/triage/analyze` | Real-time AI NLP emergency classification endpoint |
| `GET` | `/api/v1/analytics/summary` | Retrieve MTTR, SLA compliance rate, and status breakdown |
| `GET` | `/api/v1/analytics/building-hotspots` | Ranking of buildings by issue frequency |
| `GET` | `/api/v1/health` | Cloud liveness health check probe |
| `GET` | `/api/v1/health/ready` | Kubernetes readiness probe |
| `GET` | `/api/v1/metrics` | Prometheus telemetry exposition |
| `WS` | `/ws/events` | Real-time WebSocket event streaming |

---

## 📄 License
This project is released under the MIT License.
