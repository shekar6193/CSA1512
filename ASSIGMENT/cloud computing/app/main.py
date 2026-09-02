import os
import time
from datetime import datetime
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST

from app.config import settings
from app.database import engine, Base, SessionLocal
from app.services.seed_data import seed_database
from app.services.notification_service import notification_hub

# Route imports
from app.routes.requests import router as requests_router
from app.routes.staff import router as staff_router
from app.routes.analytics import router as analytics_router
from app.routes.triage import router as triage_router
from app.routes.auth import router as auth_router
from app.routes.websockets import router as ws_router

# Prometheus Metrics for Cloud Monitoring
REQUEST_COUNT = Counter("campuspulse_http_requests_total", "Total HTTP requests", ["method", "endpoint", "status_code"])
REQUEST_LATENCY = Histogram("campuspulse_http_request_duration_seconds", "HTTP request latency", ["endpoint"])

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Create tables and seed initial demo data
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_database(db)
    finally:
        db.close()
    yield
    # Shutdown logic if needed

app = FastAPI(
    title="CampusPulse Cloud - Smart Campus Service Request & Incident Response Platform",
    description="""
    ## Cloud-Ready Smart Campus Service Request & Incident Response Platform REST API
    
    Exposes full CRUD operations for service requests, real-time staff incident dispatching, 
    AI-powered emergency triage, GIS campus mapping, and analytics.

    ### Innovation Features:
    - **AI Emergency Triage Engine**: Real-time NLP keyword and hazard severity classification.
    - **Interactive GIS Campus Map**: Live visual building incident pins and status overlays.
    - **Real-time WebSockets**: Bidirectional event stream for immediate status synchronization.
    - **Cloud & Container Portability**: Native health probes, Prometheus metrics, and Docker/K8s readiness.
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Prometheus Middleware for latency and request tracking
@app.middleware("http")
async def prometheus_middleware(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    duration = time.time() - start_time
    
    endpoint = request.url.path
    # Group static/upload endpoints to keep Prometheus metrics clean
    if endpoint.startswith("/static") or endpoint.startswith("/uploads"):
        endpoint = "/static/*"

    REQUEST_COUNT.labels(method=request.method, endpoint=endpoint, status_code=response.status_code).inc()
    REQUEST_LATENCY.labels(endpoint=endpoint).observe(duration)
    return response

# Mount API Routers
app.include_router(requests_router, prefix=settings.API_V1_STR)
app.include_router(staff_router, prefix=settings.API_V1_STR)
app.include_router(analytics_router, prefix=settings.API_V1_STR)
app.include_router(triage_router, prefix=settings.API_V1_STR)
app.include_router(auth_router, prefix=settings.API_V1_STR)
app.include_router(ws_router)

# Mount Uploads directory for evidence attachments
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")

# Health & Cloud Monitoring Endpoints
@app.get("/api/v1/health", tags=["Cloud Health & Probes"])
def liveness_probe():
    """
    Cloud Liveness probe verifying server health, database connectivity, and active connections.
    """
    db_ok = True
    try:
        db = SessionLocal()
        db.execute("SELECT 1")
        db.close()
    except Exception:
        # Fallback for SQLite/SQLAlchemy 2.0 text execution
        try:
            from sqlalchemy import text
            db = SessionLocal()
            db.execute(text("SELECT 1"))
            db.close()
        except Exception:
            db_ok = False

    return {
        "status": "healthy" if db_ok else "degraded",
        "service": settings.PROJECT_NAME,
        "version": settings.PROJECT_VERSION,
        "database_connected": db_ok,
        "active_websockets": notification_hub.get_active_count(),
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/api/v1/health/ready", tags=["Cloud Health & Probes"])
def readiness_probe():
    """
    Kubernetes Readiness probe verifying application is ready to receive network traffic.
    """
    return {"status": "ready", "ready": True}

@app.get("/api/v1/metrics", tags=["Cloud Health & Probes"])
def metrics_endpoint():
    """
    Prometheus metrics exposition endpoint for Grafana and cloud telemetry.
    """
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)

# Serve Frontend Static Assets
static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

@app.get("/", include_in_schema=False)
async def serve_index():
    """Serve the Single Page Application UI."""
    index_file = os.path.join(os.path.dirname(__file__), "static", "index.html")
    if os.path.exists(index_file):
        return FileResponse(index_file)
    return {"message": "CampusPulse API is running. Access docs at /docs"}
