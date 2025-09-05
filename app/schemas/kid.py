from pydantic import BaseModel, Field, validator
from typing import Optional
from datetime import datetime
import re

class KidBase(BaseModel):
    name: str = Field(..., min_length=1, description="Kid's name (cannot be empty)")
    color: str = Field(..., pattern=r'^#[0-9A-Fa-f]{6}$', description="Color in hex format (e.g., #FF0000)")
    avatar: Optional[str] = Field(None, description="Avatar URL")
    
    @validator('name')
    def name_must_not_be_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('Name cannot be empty')
        return v.strip()
    
    @validator('avatar')
    def avatar_must_be_valid_url(cls, v):
        if v is not None and v.strip():
            # Basic URL validation
            if not (v.startswith('http://') or v.startswith('https://')):
                raise ValueError('Avatar must be a valid URL')
        return v

class KidCreate(KidBase):
    pass

class Kid(KidBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    model_config = {"from_attributes": True} 