from pydantic import BaseModel, Field, field_validator, field_serializer
from typing import Optional, List, Union
from datetime import datetime

class EventBase(BaseModel):
    title: str
    location: Optional[str] = None
    start_utc: datetime
    end_utc: datetime
    rrule: Optional[str] = None
    exdates: Optional[List[str]] = None
    kid_ids: Optional[List[int]] = None
    category: str = Field(..., pattern="^(school|after-school|family|sports|education|health|test)$")
    source: str = Field(default="manual", pattern="^(manual|ics|google|outlook|telegram)$")
    created_by: Optional[str] = None
    
    @field_validator('kid_ids', mode='before')
    @classmethod
    def normalize_kid_ids(cls, v):
        """Normalize kid_ids to integers"""
        if v is None:
            return None
        if isinstance(v, list):
            return [int(item) for item in v]
        return v
    
class EventCreate(EventBase):
    @field_validator('end_utc')
    @classmethod
    def validate_end_after_start(cls, v, info):
        """Validate that end_utc is after start_utc"""
        if 'start_utc' in info.data and v <= info.data['start_utc']:
            raise ValueError('end_utc must be after start_utc')
        return v

class EventUpdate(BaseModel):
    title: Optional[str] = None
    location: Optional[str] = None
    start_utc: Optional[datetime] = None
    end_utc: Optional[datetime] = None
    rrule: Optional[str] = None
    exdates: Optional[List[str]] = None
    kid_ids: Optional[List[int]] = None
    category: Optional[str] = Field(None, pattern="^(school|after-school|family|sports|education|health|test)$")
    source: Optional[str] = Field(None, pattern="^(manual|ics|google|outlook|telegram)$")

class Event(EventBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    model_config = {"from_attributes": True}
    
    @field_serializer('start_utc', 'end_utc', 'created_at', 'updated_at')
    def serialize_datetime(self, value):
        """Serialize datetime fields to ISO format with Z suffix"""
        if value:
            return value.strftime('%Y-%m-%dT%H:%M:%SZ')
        return value
    
    @classmethod
    def from_orm(cls, obj):
        """Custom from_orm to handle JSON string conversion"""
        data = {
            "id": obj.id,
            "title": obj.title,
            "location": obj.location,
            "start_utc": obj.start_utc,
            "end_utc": obj.end_utc,
            "rrule": obj.rrule,
            "exdates": obj.exdates_list if hasattr(obj, 'exdates_list') else obj.exdates,
            "kid_ids": obj.kid_ids_list if hasattr(obj, 'kid_ids_list') else obj.kid_ids,
            "category": obj.category,
            "source": obj.source,
            "created_by": obj.created_by,
            "created_at": obj.created_at,
            "updated_at": obj.updated_at
        }
        return cls(**data) 