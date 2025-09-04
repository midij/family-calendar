from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class KidBase(BaseModel):
    name: str
    color: str
    avatar: Optional[str] = None

class KidCreate(KidBase):
    pass

class Kid(KidBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    model_config = {"from_attributes": True} 