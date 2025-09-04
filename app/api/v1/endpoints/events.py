from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
import json
from app.database import get_db
from app.schemas.event import Event, EventCreate, EventUpdate
from app.models.event import Event as EventModel

router = APIRouter()

@router.get("/", response_model=List[Event])
def get_events(
    start: Optional[datetime] = Query(None, description="Start date"),
    end: Optional[datetime] = Query(None, description="End date"),
    kid_id: Optional[str] = Query(None, description="Filter by kid ID"),
    db: Session = Depends(get_db)
):
    """Get events with optional filtering"""
    query = db.query(EventModel)
    
    if start:
        query = query.filter(EventModel.start_utc >= start)
    if end:
        query = query.filter(EventModel.end_utc <= end)
    if kid_id:
        query = query.filter(EventModel.kid_ids.contains([kid_id]))
    
    events = query.all()
    
    # Convert each event to proper format
    response_events = []
    for event in events:
        response_data = {
            "id": event.id,
            "title": event.title,
            "location": event.location,
            "start_utc": event.start_utc,
            "end_utc": event.end_utc,
            "rrule": event.rrule,
            "exdates": event.exdates_list,
            "kid_ids": event.kid_ids_list,
            "category": event.category,
            "source": event.source,
            "created_by": event.created_by,
            "created_at": event.created_at,
            "updated_at": event.updated_at
        }
        response_events.append(Event(**response_data))
    
    return response_events

@router.post("/", response_model=Event)
def create_event(event: EventCreate, db: Session = Depends(get_db)):
    """Create a new event"""
    event_data = event.model_dump()
    
    # Convert lists to JSON strings for TEXT columns
    if event_data.get('kid_ids'):
        event_data['kid_ids'] = json.dumps(event_data['kid_ids'])
    if event_data.get('exdates'):
        event_data['exdates'] = json.dumps(event_data['exdates'])
    
    db_event = EventModel(**event_data)
    db.add(db_event)
    db.commit()
    db.refresh(db_event)
    
    # Convert back to proper format for response
    response_data = {
        "id": db_event.id,
        "title": db_event.title,
        "location": db_event.location,
        "start_utc": db_event.start_utc,
        "end_utc": db_event.end_utc,
        "rrule": db_event.rrule,
        "exdates": db_event.exdates_list,
        "kid_ids": db_event.kid_ids_list,
        "category": db_event.category,
        "source": db_event.source,
        "created_by": db_event.created_by,
        "created_at": db_event.created_at,
        "updated_at": db_event.updated_at
    }
    return Event(**response_data) 