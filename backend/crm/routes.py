from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query, Body
from fastapi.responses import FileResponse
from typing import Optional, List
from datetime import datetime
import os

from .models import LeadCreate, LeadUpdate, ReminderCreate, ReminderUpdate
from .controllers import CRMController
from .utils import validate_file_type, save_upload_file, delete_file

router = APIRouter(prefix="/crm", tags=["CRM"])

# Test endpoint
@router.post("/test")
async def test_endpoint(data: dict):
    """Test endpoint to check if POST works"""
    return {"success": True, "received": data}

@router.post("/debug")
async def debug_endpoint(request: dict = Body(...)):
    """Debug endpoint to check request parsing"""
    return {"success": True, "body": request}

# Dependency to get CRM controller
def get_crm_controller(db=Depends(lambda: None)):
    # This will be replaced with actual DB dependency in server.py
    return CRMController(db)


# ============ LEAD ENDPOINTS ============

@router.post("/leads")
async def create_lead(
    lead_data: dict = Body(...),
    controller: CRMController = Depends(get_crm_controller),
    current_user: dict = None  # Will be injected by auth middleware
):
    """Create a new lead"""
    print(f"DEBUG: Received lead_data: {lead_data}")
    try:
        # Convert dict to LeadCreate model
        lead = LeadCreate(**lead_data)
        user_id = current_user.get("username") if current_user else "admin"
        created_lead = await controller.create_lead(lead, user_id)
        return {"success": True, "lead": created_lead}
    except Exception as e:
        print(f"DEBUG: Error creating lead: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Invalid lead data: {str(e)}")


@router.get("/leads")
async def get_leads(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    lead_type: Optional[str] = None,
    status: Optional[str] = None,
    source: Optional[str] = None,
    search: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    controller: CRMController = Depends(get_crm_controller)
):
    """Get leads with filters and pagination"""
    result = await controller.get_leads(
        skip=skip,
        limit=limit,
        lead_type=lead_type,
        status=status,
        source=source,
        search=search,
        date_from=date_from,
        date_to=date_to
    )
    return result


@router.get("/leads/{lead_id}")
async def get_lead(
    lead_id: str,
    controller: CRMController = Depends(get_crm_controller)
):
    """Get a single lead by ID"""
    lead = await controller.get_lead_by_id(lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    return lead


@router.put("/leads/{lead_id}")
async def update_lead(
    lead_id: str,
    lead_update: LeadUpdate,
    controller: CRMController = Depends(get_crm_controller),
    current_user: dict = None
):
    """Update a lead"""
    user_id = current_user.get("username") if current_user else "admin"
    updated_lead = await controller.update_lead(lead_id, lead_update, user_id)
    if not updated_lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    return {"success": True, "lead": updated_lead}


@router.delete("/leads/{lead_id}")
async def delete_lead(
    lead_id: str,
    controller: CRMController = Depends(get_crm_controller)
):
    """Delete a lead"""
    success = await controller.delete_lead(lead_id)
    if not success:
        raise HTTPException(status_code=404, detail="Lead not found")
    return {"success": True, "message": "Lead deleted successfully"}


# ============ DOCUMENT ENDPOINTS ============

@router.post("/leads/{lead_id}/upload")
async def upload_document(
    lead_id: str,
    file: UploadFile = File(...),
    controller: CRMController = Depends(get_crm_controller)
):
    """Upload a document for a lead"""
    # Validate file type
    if not validate_file_type(file.filename):
        raise HTTPException(
            status_code=400,
            detail="Invalid file type. Allowed: PDF, JPG, PNG, DOCX"
        )
    
    # Validate file size (3 MB = 3 * 1024 * 1024 bytes)
    content = await file.read()
    if len(content) > 3 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File size exceeds 3 MB limit")
    
    # Reset file pointer
    await file.seek(0)
    
    # Check if lead exists
    lead = await controller.get_lead_by_id(lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    # Save file
    document = await save_upload_file(file, lead.get("lead_id") or lead_id)
    
    # Add to lead documents
    await controller.add_document(lead_id, document)
    
    return {"success": True, "document": document}


@router.get("/leads/{lead_id}/docs/download")
async def download_document(
    lead_id: str,
    file_path: str = Query(...),
    controller: CRMController = Depends(get_crm_controller)
):
    """Download a document"""
    # Check if lead exists
    lead = await controller.get_lead_by_id(lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    # Check if file exists in lead's documents
    doc_exists = any(doc["file_path"] == file_path for doc in lead.get("documents", []))
    if not doc_exists:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Get full file path
    full_path = f"/app/backend{file_path}"
    
    if not os.path.exists(full_path):
        raise HTTPException(status_code=404, detail="File not found on disk")
    
    filename = os.path.basename(file_path)
    return FileResponse(full_path, filename=filename)


@router.delete("/leads/{lead_id}/docs")
async def delete_document(
    lead_id: str,
    file_path: str = Query(...),
    controller: CRMController = Depends(get_crm_controller)
):
    """Delete a document"""
    # Check if lead exists
    lead = await controller.get_lead_by_id(lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    # Delete from database
    await controller.delete_document(lead_id, file_path)
    
    # Delete file from disk
    delete_file(file_path)
    
    return {"success": True, "message": "Document deleted successfully"}


# ============ REMINDER ENDPOINTS ============

@router.post("/reminders")
async def create_reminder(
    reminder: ReminderCreate,
    controller: CRMController = Depends(get_crm_controller),
    current_user: dict = None
):
    """Create a new reminder"""
    user_id = current_user.get("username") if current_user else "admin"
    created_reminder = await controller.create_reminder(reminder, user_id)
    return {"success": True, "reminder": created_reminder}


@router.get("/reminders")
async def get_reminders(
    lead_id: Optional[str] = None,
    status: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    controller: CRMController = Depends(get_crm_controller)
):
    """Get reminders with filters"""
    date_from_dt = datetime.fromisoformat(date_from) if date_from else None
    date_to_dt = datetime.fromisoformat(date_to) if date_to else None
    
    reminders = await controller.get_reminders(
        lead_id=lead_id,
        status=status,
        date_from=date_from_dt,
        date_to=date_to_dt
    )
    return reminders


@router.put("/reminders/{reminder_id}")
async def update_reminder(
    reminder_id: str,
    reminder_update: ReminderUpdate,
    controller: CRMController = Depends(get_crm_controller)
):
    """Update a reminder"""
    updated_reminder = await controller.update_reminder(reminder_id, reminder_update)
    if not updated_reminder:
        raise HTTPException(status_code=404, detail="Reminder not found")
    return {"success": True, "reminder": updated_reminder}


@router.delete("/reminders/{reminder_id}")
async def delete_reminder(
    reminder_id: str,
    controller: CRMController = Depends(get_crm_controller)
):
    """Delete a reminder"""
    success = await controller.delete_reminder(reminder_id)
    if not success:
        raise HTTPException(status_code=404, detail="Reminder not found")
    return {"success": True, "message": "Reminder deleted successfully"}


# ============ DASHBOARD & ANALYTICS ENDPOINTS ============

@router.get("/dashboard-summary")
async def get_dashboard_summary(
    controller: CRMController = Depends(get_crm_controller)
):
    """Get dashboard summary with counts and stats"""
    summary = await controller.get_dashboard_summary()
    return summary


@router.get("/reports/monthly")
async def get_monthly_leads(
    year: int = Query(datetime.utcnow().year),
    controller: CRMController = Depends(get_crm_controller)
):
    """Get monthly lead counts for a year"""
    data = await controller.get_monthly_leads(year)
    return data


@router.get("/reports/lead-type-breakdown")
async def get_lead_type_breakdown(
    controller: CRMController = Depends(get_crm_controller)
):
    """Get lead count by type"""
    data = await controller.get_lead_type_breakdown()
    return data


@router.get("/reports/lead-source-breakdown")
async def get_lead_source_breakdown(
    controller: CRMController = Depends(get_crm_controller)
):
    """Get lead count by source"""
    data = await controller.get_lead_source_breakdown()
    return data


@router.get("/reports/referral-leaderboard")
async def get_referral_leaderboard(
    limit: int = Query(10, ge=1, le=50),
    controller: CRMController = Depends(get_crm_controller)
):
    """Get top referrers"""
    data = await controller.get_referral_leaderboard(limit)
    return data


@router.get("/upcoming-travels")
async def get_upcoming_travels(
    controller: CRMController = Depends(get_crm_controller)
):
    """Get leads with travel dates in next 10 days"""
    leads = await controller.get_upcoming_travels()
    return leads
