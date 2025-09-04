from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Union
from datetime import datetime

class EventBase(BaseModel):
    title: str
    location: Optional[str] = None
    start_utc: datetime
    end_utc: datetime
    rrule: Optional[str] = None
    exdates: Optional[List[str]] = None
    kid_ids: Optional[List[Union[str, int]]] = None
    category: str = Field(..., pattern="^(school|after-school|family)$")
    source: str = Field(default="manual", pattern="^(manual|ics|google|outlook)$")
    created_by: Optional[str] = None
    
    @field_validator('kid_ids', mode='before')
    @classmethod
    def normalize_kid_ids(cls, v):
        """Normalize kid_ids to strings"""
        if v is None:
            return None
        if isinstance(v, list):
            return [str(item) for item in v]
        return v

class EventCreate(EventBase):
    pass

class EventUpdate(BaseModel):
    title: Optional[str] = None
    location: Optional[str] = None
    start_utc: Optional[datetime] = None
    end_utc: Optional[datetime] = None
    rrule: Optional[str] = None
    exdates: Optional[List[str]] = None
    kid_ids: Optional[List[Union[str, int]]] = None
    category: Optional[str] = Field(None, pattern="^(school|after-school|family)$")
    source: Optional[str] = Field(None, pattern="^(manual|ics|google|outlook)$")

class Event(EventBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    model_config = {"from_attributes": True}
    
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