from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.schemas.kid import Kid, KidCreate, KidUpdate
from app.models.kid import Kid as KidModel
# Removed SSE and VersionService imports - using database timestamp approach

router = APIRouter()

@router.get("/", response_model=List[Kid])
def get_kids(db: Session = Depends(get_db)):
    """Get all kids"""
    kids = db.query(KidModel).order_by(KidModel.name).all()
    return kids

@router.get("/{kid_id}", response_model=Kid)
def get_kid(kid_id: int, db: Session = Depends(get_db)):
    """Get a specific kid by ID"""
    kid = db.query(KidModel).filter(KidModel.id == kid_id).first()
    if not kid:
        raise HTTPException(status_code=404, detail="Kid not found")
    return kid

@router.post("/", response_model=Kid, status_code=201)
async def create_kid(kid: KidCreate, db: Session = Depends(get_db)):
    """Create a new kid"""
    try:
        db_kid = KidModel(**kid.model_dump())
        db.add(db_kid)
        db.commit()
        db.refresh(db_kid)
        
        # Database timestamp will be automatically updated by SQLAlchemy
        
        return db_kid
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Failed to create kid: {str(e)}")

@router.patch("/{kid_id}", response_model=Kid)
async def update_kid(kid_id: int, kid_update: KidUpdate, db: Session = Depends(get_db)):
    """Update a kid"""
    db_kid = db.query(KidModel).filter(KidModel.id == kid_id).first()
    if not db_kid:
        raise HTTPException(status_code=404, detail="Kid not found")
    
    try:
        # Update only provided fields
        update_data = kid_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_kid, field, value)
        
        db.commit()
        db.refresh(db_kid)
        
        return db_kid
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Failed to update kid: {str(e)}")

@router.delete("/{kid_id}")
async def delete_kid(kid_id: int, db: Session = Depends(get_db)):
    """Delete a kid"""
    db_kid = db.query(KidModel).filter(KidModel.id == kid_id).first()
    if not db_kid:
        raise HTTPException(status_code=404, detail="Kid not found")
    
    try:
        db.delete(db_kid)
        db.commit()
        
        # Database timestamp will be automatically updated by SQLAlchemy
        
        return {"message": "Kid deleted successfully"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Failed to delete kid: {str(e)}") 