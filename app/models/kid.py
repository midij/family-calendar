from sqlalchemy import Column, String
from app.models.base import BaseModel

class Kid(BaseModel):
    __tablename__ = "kids"
    
    name = Column(String, nullable=False)
    color = Column(String, nullable=False)  # Hex color code
    avatar = Column(String, nullable=True)  # URL to avatar image 