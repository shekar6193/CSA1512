from fastapi import APIRouter
from app.schemas import TriageAnalysisRequest, TriageAnalysisResponse
from app.services.triage_service import TriageEngine

router = APIRouter(prefix="/triage", tags=["AI Triage & Emergency Classifier"])

@router.post("/analyze", response_model=TriageAnalysisResponse)
def analyze_incident_text(payload: TriageAnalysisRequest):
    """
    Live AI Triage preview endpoint.
    Analyzes title and description in real-time, detecting safety hazards,
    suggesting SLA, and recommending appropriate category and dispatch unit.
    """
    result = TriageEngine.analyze(
        title=payload.title,
        description=payload.description,
        current_category=payload.category
    )
    return result
