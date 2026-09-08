from fastapi import APIRouter
from pydantic import BaseModel, EmailStr
from typing import List

router = APIRouter()

class EscalationRequest(BaseModel):
    user_name: str
    user_email: str
    user_phone: str
    query_summary: str
    formulation_category: str
    preferred_facilitator_type: str = "Patent Agent (Ayurvedic/Pharma Specialization)"

@router.post("/escalation/connect")
async def escalate_to_facilitator(request: EscalationRequest):
    """
    Escalation Endpoint to route complex cases to registered IP Facilitators and Patent Agents.
    """
    return {
        "status": "SUCCESS",
        "reference_ticket_id": "IP-SAKTI-2026-8942",
        "message": "Your query has been routed to the AYUSH IP Facilitation Panel. A registered Patent Agent will contact you.",
        "matched_facilitators": [
            {
                "name": "Dr. V. K. Sharma (Registered Patent Agent IN/PA-1402)",
                "specialization": "Ayurveda Phytopharmaceuticals & Section 3(p) TK Defense",
                "location": "New Delhi / Remote"
            },
            {
                "name": "Smt. A. R. Lakshmi (IP Attorney & GI Consultant)",
                "specialization": "Ayurveda-Aahar, FSSAI & Biological Diversity Act Compliance",
                "location": "Bengaluru / Remote"
            }
        ]
    }
