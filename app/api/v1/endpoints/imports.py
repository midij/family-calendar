"""
Import endpoints for CSV and ICS file processing
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
import csv
import io
from app.database import get_db
from app.models.event import Event as EventModel
from app.schemas.event import EventCreate
from app.services.import_service import ImportService
from app.services.version_service import VersionService
from app.services.sse_service import SSEService

router = APIRouter()

@router.post("/csv", response_model=Dict[str, Any])
async def import_csv_events(
    file: UploadFile = File(..., description="CSV file containing events"),
    kid_id: Optional[str] = Form(None, description="Default kid ID for imported events"),
    category: Optional[str] = Form(None, description="Default category for imported events"),
    source: str = Form("csv", description="Source identifier for imported events"),
    db: Session = Depends(get_db)
):
    """
    Import events from a CSV file
    
    Expected CSV format:
    - title: Event title (required)
    - start_date: Start date (YYYY-MM-DD format)
    - start_time: Start time (HH:MM format, optional)
    - end_date: End date (YYYY-MM-DD format, optional)
    - end_time: End time (HH:MM format, optional)
    - location: Event location (optional)
    - description: Event description (optional)
    - rrule: RRULE string (optional)
    - kid_ids: Comma-separated kid IDs (optional)
    """
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="File must be a CSV file")
    
    try:
        # Read file content
        content = await file.read()
        csv_content = content.decode('utf-8')
        
        # Parse CSV and import events
        result = ImportService.import_csv_events(
            csv_content=csv_content,
            default_kid_id=kid_id,
            default_category=category,
            default_source=source,
            db=db
        )
        
        # Update version and broadcast to SSE clients if any events were imported
        if result["success_count"] > 0:
            version_info = VersionService.update_version(db)
            await SSEService.broadcast_update(version_info)
        
        return {
            "message": "CSV import completed",
            "total_rows": result["total_rows"],
            "imported_events": result["imported_events"],
            "errors": result["errors"],
            "success_count": result["success_count"],
            "error_count": result["error_count"]
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to import CSV: {str(e)}")

@router.post("/ics", response_model=Dict[str, Any])
async def import_ics_events(
    file: UploadFile = File(..., description="ICS file containing events"),
    kid_id: Optional[str] = Form(None, description="Default kid ID for imported events"),
    category: Optional[str] = Form(None, description="Default category for imported events"),
    source: str = Form("ics", description="Source identifier for imported events"),
    db: Session = Depends(get_db)
):
    """
    Import events from an ICS (iCalendar) file
    
    Supports standard iCalendar format with VEVENT components
    """
    if not file.filename.endswith(('.ics', '.ical')):
        raise HTTPException(status_code=400, detail="File must be an ICS file")
    
    try:
        # Read file content
        content = await file.read()
        ics_content = content.decode('utf-8')
        
        # Parse ICS and import events
        result = ImportService.import_ics_events(
            ics_content=ics_content,
            default_kid_id=kid_id,
            default_category=category,
            default_source=source,
            db=db
        )
        
        # Update version and broadcast to SSE clients if any events were imported
        if result["success_count"] > 0:
            version_info = VersionService.update_version(db)
            await SSEService.broadcast_update(version_info)
        
        return {
            "message": "ICS import completed",
            "total_events": result["total_events"],
            "imported_events": result["imported_events"],
            "errors": result["errors"],
            "success_count": result["success_count"],
            "error_count": result["error_count"]
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to import ICS: {str(e)}")

@router.get("/templates/csv")
def get_csv_template():
    """
    Get a CSV template for event import
    """
    template_data = [
        {
            "title": "Sample Event",
            "start_date": "2025-09-01",
            "start_time": "08:00",
            "end_date": "2025-09-01",
            "end_time": "09:00",
            "location": "Sample Location",
            "rrule": "FREQ=WEEKLY;BYDAY=MO;UNTIL=2025-12-31T00:00:00Z",
            "kid_ids": "1,2"
        }
    ]
    
    # Create CSV content
    output = io.StringIO()
    fieldnames = template_data[0].keys()
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(template_data)
    
    csv_content = output.getvalue()
    output.close()
    
    return {
        "template": csv_content,
        "description": "CSV template for event import",
        "required_fields": ["title", "start_date"],
        "optional_fields": ["start_time", "end_date", "end_time", "location", "rrule", "kid_ids"]
    }
