from sqlalchemy import Column, String, DateTime, JSON, Index
from app.models.base import BaseModel
import json

class Event(BaseModel):
    __tablename__ = "events"
    
    title = Column(String, nullable=False)
    location = Column(String, nullable=True)
    start_utc = Column(DateTime(timezone=True), nullable=False, index=True)
    end_utc = Column(DateTime(timezone=True), nullable=False, index=True)
    rrule = Column(String, nullable=True)  # RFC5545 RRULE string
    exdates = Column(JSON, nullable=True)  # Array of ISO date strings
    kid_ids = Column(JSON, nullable=True)  # Array of kid IDs
    category = Column(String, nullable=False)  # school, after-school, family
    source = Column(String, nullable=False, default="manual")  # manual, ics, google, outlook
    created_by = Column(String, nullable=True)
    
    # Add composite index for time range queries
    __table_args__ = (
        Index('ix_events_time_range', 'start_utc', 'end_utc'),
    )
    
    @property
    def kid_ids_list(self):
        """Get kid_ids as a list"""
        return self.kid_ids or []
    
    @property
    def exdates_list(self):
        """Get exdates as a list"""
        return self.exdates or [] 