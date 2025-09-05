from fastapi import APIRouter, Depends, HTTPException, Query, Header, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
import hashlib
import json
from app.database import get_db
from app.schemas.event import Event, EventCreate, EventUpdate
from app.models.event import Event as EventModel
from app.services.event_expansion_service import EventExpansionService
from app.services.rrule_service import RRuleService
# Removed SSE and VersionService imports - using database timestamp approach

router = APIRouter()

@router.get("/", response_model=List[Event])
def get_events(
    start: Optional[datetime] = Query(None, description="Start date (ISO format)"),
    end: Optional[datetime] = Query(None, description="End date (ISO format)"),
    kid_id: Optional[str] = Query(None, description="Filter by kid ID"),
    category: Optional[str] = Query(None, description="Filter by category (school, after-school, family)"),
    expand: bool = Query(False, description="Expand recurring events into individual instances"),
    db: Session = Depends(get_db)
):
    """Get events with optional filtering by date range, kid, or category"""
    if expand:
        # Use event expansion service for recurring events
        expanded_events = EventExpansionService.get_events_in_range(
            db, start, end, kid_id, category
        )
        return expanded_events
    else:
        # Original behavior - return raw events
        query = db.query(EventModel)
        
        # Date range filtering
        if start:
            query = query.filter(EventModel.start_utc >= start)
        if end:
            query = query.filter(EventModel.end_utc <= end)
        
        # Kid filtering - check if kid_id is in the kid_ids JSON array
        if kid_id:
            query = query.filter(EventModel.kid_ids.contains([kid_id]))
        
        # Category filtering
        if category:
            query = query.filter(EventModel.category == category)
        
        # Order by start time
        query = query.order_by(EventModel.start_utc)
        
        events = query.all()
        return events

# Removed SSE stream endpoint - using database timestamp polling instead

@router.get("/version")
def get_version_info(db: Session = Depends(get_db)):
    """Get current version information for polling fallback"""
    from sqlalchemy import func
    
    # Get the latest updated_at timestamp from events table
    latest_updated = db.query(func.max(EventModel.updated_at)).scalar()
    
    return {
        "last_updated": latest_updated.isoformat() if latest_updated else None,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

@router.get("/{event_id}", response_model=Event)
def get_event(event_id: int, db: Session = Depends(get_db)):
    """Get a specific event by ID"""
    event = db.query(EventModel).filter(EventModel.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    return event

@router.post("/", response_model=Event, status_code=201)
async def create_event(event: EventCreate, db: Session = Depends(get_db)):
    """Create a new event"""
    try:
        # Create the event directly - SQLAlchemy will handle JSON serialization
        db_event = EventModel(**event.model_dump())
        db.add(db_event)
        db.commit()
        db.refresh(db_event)
        
        # Database timestamp will be automatically updated by SQLAlchemy
        return db_event
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Failed to create event: {str(e)}")

@router.patch("/{event_id}", response_model=Event)
async def update_event(
    event_id: int, 
    event_update: EventUpdate, 
    db: Session = Depends(get_db),
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key")
):
    """Update an existing event with idempotency support"""
    from app.services.idempotency_service import IdempotencyService
    
    # Check if event exists
    db_event = IdempotencyService.validate_event_exists(db, event_id)
    if not db_event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    # Get update data
    update_data = event_update.model_dump(exclude_unset=True)
    
    # Validate update data
    is_valid, error_message = IdempotencyService.validate_event_update_data(update_data)
    if not is_valid:
        raise HTTPException(status_code=400, detail=error_message)
    
    # Handle idempotency if key is provided
    if idempotency_key:
        # Check if this operation was already performed
        cached_result = IdempotencyService.check_idempotency(
            idempotency_key, "update", event_id
        )
        if cached_result:
            return cached_result
    
    try:
        # Update only provided fields
        for field, value in update_data.items():
            setattr(db_event, field, value)
        
        # Update the updated_at timestamp
        db_event.updated_at = datetime.now(timezone.utc)
        
        db.commit()
        db.refresh(db_event)
        
        # Store result for idempotency if key was provided
        if idempotency_key:
            IdempotencyService.store_idempotency_result(
                idempotency_key, "update", event_id, db_event
            )
        
        # Database timestamp will be automatically updated by SQLAlchemy
        return db_event
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Failed to update event: {str(e)}")

@router.delete("/{event_id}")
async def delete_event(
    event_id: int, 
    db: Session = Depends(get_db),
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key")
):
    """Delete an event with idempotency support"""
    from app.services.idempotency_service import IdempotencyService
    
    # Check if event exists
    db_event = IdempotencyService.validate_event_exists(db, event_id)
    if not db_event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    # Handle idempotency if key is provided
    if idempotency_key:
        # Check if this operation was already performed
        cached_result = IdempotencyService.check_idempotency(
            idempotency_key, "delete", event_id
        )
        if cached_result:
            return cached_result
    
    try:
        # Store event data before deletion for idempotency
        event_data = {
            "id": db_event.id,
            "title": db_event.title,
            "deleted_at": datetime.now(timezone.utc).isoformat()
        }
        
        db.delete(db_event)
        db.commit()
        
        result = {"message": "Event deleted successfully", "event_id": event_id}
        
        # Store result for idempotency if key was provided
        if idempotency_key:
            IdempotencyService.store_idempotency_result(
                idempotency_key, "delete", event_id, result
            )
        
        # Database timestamp will be automatically updated by SQLAlchemy
        return result
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Failed to delete event: {str(e)}")

@router.get("/expanded/", response_model=List[Dict[str, Any]])
def get_expanded_events(
    start: Optional[datetime] = Query(None, description="Start date (ISO format)"),
    end: Optional[datetime] = Query(None, description="End date (ISO format)"),
    kid_id: Optional[str] = Query(None, description="Filter by kid ID"),
    category: Optional[str] = Query(None, description="Filter by category"),
    db: Session = Depends(get_db)
):
    """Get expanded events (recurring events expanded into individual instances)"""
    expanded_events = EventExpansionService.get_events_in_range(
        db, start, end, kid_id, category
    )
    return expanded_events

@router.get("/weekly/", response_model=List[Dict[str, Any]])
def get_weekly_events(
    week_start: datetime = Query(..., description="Start of the week (Monday)"),
    kid_id: Optional[str] = Query(None, description="Filter by kid ID"),
    category: Optional[str] = Query(None, description="Filter by category"),
    db: Session = Depends(get_db)
):
    """Get all events for a specific week (Monday to Sunday)"""
    expanded_events = EventExpansionService.get_weekly_events(
        db, week_start, kid_id, category
    )
    return expanded_events

@router.get("/daily/", response_model=List[Dict[str, Any]])
def get_daily_events(
    day: datetime = Query(..., description="The day to get events for"),
    kid_id: Optional[str] = Query(None, description="Filter by kid ID"),
    category: Optional[str] = Query(None, description="Filter by category"),
    db: Session = Depends(get_db)
):
    """Get all events for a specific day"""
    expanded_events = EventExpansionService.get_daily_events(
        db, day, kid_id, category
    )
    return expanded_events

@router.post("/validate-rrule")
def validate_rrule(rrule_str: str):
    """Validate an RRULE string"""
    is_valid, error_message = RRuleService.validate_rrule(rrule_str)
    
    if is_valid:
        frequency = RRuleService.get_rrule_frequency(rrule_str)
        until_date = RRuleService.get_rrule_until_date(rrule_str)
        
        return {
            "valid": True,
            "frequency": frequency,
            "until_date": until_date.isoformat() if until_date else None,
            "message": "RRULE is valid"
        }
    else:
        return {
            "valid": False,
            "error": error_message,
            "message": "RRULE is invalid"
        }

@router.get("/{event_id}/expand", response_model=List[Dict[str, Any]])
def expand_event(
    event_id: int,
    start: Optional[datetime] = Query(None, description="Start date for expansion range"),
    end: Optional[datetime] = Query(None, description="End date for expansion range"),
    db: Session = Depends(get_db)
):
    """Expand a specific event into individual instances"""
    event = db.query(EventModel).filter(EventModel.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    # Validate the event can be expanded
    is_valid, error = EventExpansionService.validate_event_expansion(event)
    if not is_valid:
        raise HTTPException(status_code=400, detail=f"Event expansion failed: {error}")
    
    expanded_instances = EventExpansionService.expand_event_to_instances(
        event, start, end
    )
    
    return expanded_instances 