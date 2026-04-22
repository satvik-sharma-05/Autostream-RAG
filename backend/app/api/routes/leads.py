"""Lead management endpoints."""
import csv
import io
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from typing import List
from app.schemas.lead import LeadResponse
from app.core.tools import get_all_leads

router = APIRouter()


@router.get("/leads", response_model=List[LeadResponse])
async def list_leads():
    """Return all captured leads."""
    return get_all_leads()


@router.get("/leads/export")
async def export_leads_csv():
    """Export all leads as a CSV file."""
    leads = get_all_leads()
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=["name", "email", "platform", "captured_at", "status"])
    writer.writeheader()
    writer.writerows(leads)
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=leads.csv"},
    )
