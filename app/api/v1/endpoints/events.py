from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from app.database import get_db
from app.schemas.event import Event, EventCreate, EventUpdate
from app.models.event import Event as EventModel

router = APIRouter()

@router.get("/", response_model=List[Event])
def get_events(
    start: Optional[datetime] = Query(None, description="Start date (ISO format)"),
    end: Optional[datetime] = Query(None, description="End date (ISO format)"),
    kid_id: Optional[str] = Query(None, description="Filter by kid ID"),
    category: Optional[str] = Query(None, description="Filter by category (school, after-school, family)"),
    db: Session = Depends(get_db)
):
    """Get events with optional filtering by date range, kid, or category"""
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

@router.get("/{event_id}", response_model=Event)
def get_event(event_id: int, db: Session = Depends(get_db)):
    """Get a specific event by ID"""
    event = db.query(EventModel).filter(EventModel.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    return event

@router.post("/", response_model=Event)
def create_event(event: EventCreate, db: Session = Depends(get_db)):
    """Create a new event"""
    try:
        # Create the event directly - SQLAlchemy will handle JSON serialization
        db_event = EventModel(**event.model_dump())
        db.add(db_event)
        db.commit()
        db.refresh(db_event)
        return db_event
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Failed to create event: {str(e)}")

@router.patch("/{event_id}", response_model=Event)
def update_event(event_id: int, event_update: EventUpdate, db: Session = Depends(get_db)):
    """Update an existing event"""
    db_event = db.query(EventModel).filter(EventModel.id == event_id).first()
    if not db_event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    try:
        # Update only provided fields
        update_data = event_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_event, field, value)
        
        db.commit()
        db.refresh(db_event)
        return db_event
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Failed to update event: {str(e)}")

@router.delete("/{event_id}")
def delete_event(event_id: int, db: Session = Depends(get_db)):
    """Delete an event"""
    db_event = db.query(EventModel).filter(EventModel.id == event_id).first()
    if not db_event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    try:
        db.delete(db_event)
        db.commit()
        return {"message": "Event deleted successfully"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Failed to delete event: {str(e)}") 