from sqlalchemy import Column, String, DateTime, Text
from app.models.base import BaseModel
import json

class Event(BaseModel):
    __tablename__ = "events"
    
    title = Column(String, nullable=False)
    location = Column(String, nullable=True)
    start_utc = Column(DateTime(timezone=True), nullable=False)
    end_utc = Column(DateTime(timezone=True), nullable=False)
    rrule = Column(String, nullable=True)  # RFC5545 RRULE string
    exdates = Column(Text, nullable=True)  # Array of ISO date strings (stored as JSON text)
    kid_ids = Column(Text, nullable=True)  # Array of kid IDs (stored as JSON text)
    category = Column(String, nullable=False)  # school, after-school, family
    source = Column(String, nullable=False, default="manual")  # manual, ics, google, outlook
    created_by = Column(String, nullable=True)
    
    @property
    def kid_ids_list(self):
        """Convert stored JSON string back to list"""
        if self.kid_ids:
            try:
                return json.loads(self.kid_ids)
            except (json.JSONDecodeError, TypeError):
                return []
        return []
    
    @property
    def exdates_list(self):
        """Convert stored JSON string back to list"""
        if self.exdates:
            try:
                return json.loads(self.exdates)
            except (json.JSONDecodeError, TypeError):
                return []
        return [] 