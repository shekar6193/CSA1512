import re
from typing import List, Tuple
from app.config import settings
from app.schemas import TriageAnalysisResponse

class TriageEngine:
    """
    AI-Powered Campus Incident Triage & Emergency Severity Classifier.
    Analyzes incident descriptions, detects critical safety hazards,
    infers appropriate department routing, and establishes SLA deadlines.
    """

    CRITICAL_EMERGENCY_RULES = [
        (r"\b(fire|flame|smoke|blaze|burning|explosion|gas leak|carbon monoxide)\b", "EMERGENCY", "Safety & Security", "Campus Emergency & Fire Safety"),
        (r"\b(electric shock|exposed wire|sparking|transformer blown|live wire)\b", "CRITICAL", "Electrical", "Emergency Electrical Response"),
        (r"\b(flooding|burst pipe|water gushing|submerged|sewage backflow)\b", "HIGH", "Plumbing", "Hydrology & Plumbing Team"),
        (r"\b(elevator stuck|person trapped|lift breakdown|locked inside)\b", "CRITICAL", "Infrastructure & Civil", "Civil Emergency & Rapid Rescue"),
        (r"\b(chemical spill|acid|toxic fumes|biohazard|radiation)\b", "EMERGENCY", "Lab Equipment", "Environmental Health & Hazardous Safety"),
        (r"\b(assault|weapon|threat|intruder|physical fight|unconscious)\b", "EMERGENCY", "Safety & Security", "Campus Police & Security"),
        (r"\b(roof leak|ceiling collapsed|broken glass|door jammed|lock broken)\b", "MEDIUM", "Infrastructure & Civil", "Facilities Carpentry & Structural"),
        (r"\b(server down|wifi outage|switch down|ethernet down|blackout|network unreachable)\b", "HIGH", "IT & Network", "Network Operations Center (NOC)"),
        (r"\b(ac broken|no cooling|freezing|heating failure|chiller)\b", "MEDIUM", "HVAC & Climate", "HVAC Operations Unit"),
        (r"\b(trash overflow|restroom dirty|pest|spill on floor|sanitation)\b", "LOW", "Sanitation & Cleaning", "Campus Janitorial Services"),
    ]

    CATEGORY_KEYWORDS = {
        "Electrical": ["spark", "outlet", "switchboard", "fuse", "blackout", "wiring", "bulb", "power cut", "voltage", "socket", "generator"],
        "HVAC & Climate": ["ac", "air conditioner", "heating", "cooling", "thermostat", "ventilation", "chiller", "radiator", "duct", "humidity"],
        "Plumbing": ["leak", "pipe", "tap", "drain", "sink", "toilet", "water", "faucet", "clog", "flush", "overflow", "plumber"],
        "IT & Network": ["wifi", "internet", "router", "ethernet", "lan", "projector", "printer", "portal", "server", "switch", "ip address"],
        "Safety & Security": ["security", "camera", "cctv", "fire", "alarm", "smoke", "guard", "theft", "stolen", "lock", "emergency", "assault"],
        "Sanitation & Cleaning": ["trash", "dustbin", "cleaning", "garbage", "restroom", "dirty", "smell", "odor", "stain", "mop"],
        "Lab Equipment": ["microscope", "fume hood", "autoclave", "centrifuge", "chemical", "spectrometer", "laser", "oscilloscope", "hazardous"],
        "Infrastructure & Civil": ["door", "window", "roof", "stairs", "ramp", "crack", "paint", "furniture", "desk", "chair", "pothole", "elevator"]
    }

    @classmethod
    def analyze(cls, title: str, description: str, current_category: str = None) -> TriageAnalysisResponse:
        combined_text = f"{title} {description}".lower()
        
        detected_keywords: List[str] = []
        is_emergency = False
        recommended_priority = "MEDIUM"
        recommended_category = current_category or "Infrastructure & Civil"
        suggested_dispatch_team = "General Campus Facilities"
        confidence = 0.70

        # 1. Match against Emergency Rules
        matched_rule = False
        for pattern, priority, cat, team in cls.CRITICAL_EMERGENCY_RULES:
            match = re.search(pattern, combined_text, re.IGNORECASE)
            if match:
                detected_keywords.append(match.group(0))
                recommended_priority = priority
                recommended_category = cat
                suggested_dispatch_team = team
                confidence = 0.95 if priority in ["EMERGENCY", "CRITICAL"] else 0.85
                if priority in ["EMERGENCY", "CRITICAL"]:
                    is_emergency = True
                matched_rule = True
                break

        # 2. Check settings emergency list if not matched
        if not matched_rule:
            for kw in settings.EMERGENCY_KEYWORDS:
                if kw in combined_text:
                    detected_keywords.append(kw)
                    is_emergency = True
                    recommended_priority = "HIGH"
                    confidence = 0.88

        # 3. Categorization matching score
        if not matched_rule or not current_category:
            best_cat = recommended_category
            best_score = 0
            for cat, keywords in cls.CATEGORY_KEYWORDS.items():
                cat_matches = sum(1 for kw in keywords if re.search(r"\b" + re.escape(kw) + r"\b", combined_text))
                if cat_matches > best_score:
                    best_score = cat_matches
                    best_cat = cat
            if best_score > 0 and (not current_category or current_category == "General"):
                recommended_category = best_cat
                if not matched_rule:
                    confidence = min(0.92, 0.65 + (best_score * 0.08))

        # 4. Determine SLA Hours
        suggested_sla = settings.SLA_HOURS.get(recommended_priority, 24)

        # 5. Build Explainable Rationale
        if is_emergency:
            rationale = (
                f"🚨 CRITICAL ALERT DETECTED: Keywords [{', '.join(detected_keywords)}] indicate an immediate "
                f"safety/operational risk. Priority automatically escalated to {recommended_priority} with a {suggested_sla}h SLA."
            )
        elif detected_keywords:
            rationale = (
                f"High-impact patterns detected: [{', '.join(detected_keywords)}]. Routed to {suggested_dispatch_team} "
                f"with {recommended_priority} priority."
            )
        else:
            rationale = (
                f"Standard routine maintenance request categorized under {recommended_category}. "
                f"Assigned default {recommended_priority} priority with a {suggested_sla}h SLA."
            )

        return TriageAnalysisResponse(
            recommended_priority=recommended_priority,
            is_emergency=is_emergency,
            confidence_score=round(confidence, 2),
            recommended_category=recommended_category,
            detected_risk_keywords=list(set(detected_keywords)),
            suggested_sla_hours=suggested_sla,
            triage_rationale=rationale,
            suggested_dispatch_team=suggested_dispatch_team
        )
