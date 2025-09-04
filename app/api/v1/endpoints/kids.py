from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.schemas.kid import Kid, KidCreate
from app.models.kid import Kid as KidModel

router = APIRouter()

@router.get("/", response_model=List[Kid])
def get_kids(db: Session = Depends(get_db)):
    """Get all kids"""
    kids = db.query(KidModel).all()
    return kids

@router.post("/", response_model=Kid)
def create_kid(kid: KidCreate, db: Session = Depends(get_db)):
    """Create a new kid"""
    db_kid = KidModel(**kid.model_dump())
    db.add(db_kid)
    db.commit()
    db.refresh(db_kid)
    return db_kid 