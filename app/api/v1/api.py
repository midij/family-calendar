from fastapi import APIRouter
from app.api.v1.endpoints import kids, events, imports

api_router = APIRouter()
api_router.include_router(kids.router, prefix="/kids", tags=["kids"])
api_router.include_router(events.router, prefix="/events", tags=["events"])
api_router.include_router(imports.router, prefix="/import", tags=["import"]) 