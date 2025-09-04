"""
Idempotency Service for handling duplicate request prevention
"""

from typing import Optional, Dict, Any
from datetime import datetime, timezone
import hashlib
import json
from sqlalchemy.orm import Session
from app.models.event import Event as EventModel


class IdempotencyService:
    """Service for handling idempotency keys and preventing duplicate operations"""
    
    # In-memory store for idempotency keys (in production, use Redis or database)
    _idempotency_store: Dict[str, Dict[str, Any]] = {}
    
    @staticmethod
    def generate_idempotency_key(
        operation: str,
        event_id: Optional[int],
        request_data: Dict[str, Any]
    ) -> str:
        """
        Generate a unique idempotency key based on operation, event ID, and request data
        
        Args:
            operation: The operation being performed (update, delete)
            event_id: The ID of the event being operated on
            request_data: The request payload data
            
        Returns:
            A unique idempotency key string
        """
        # Create a deterministic string from the operation parameters
        key_data = {
            "operation": operation,
            "event_id": event_id,
            "data": request_data
        }
        
        # Sort the data to ensure consistent key generation
        key_string = json.dumps(key_data, sort_keys=True, default=str)
        
        # Generate SHA-256 hash
        return hashlib.sha256(key_string.encode()).hexdigest()
    
    @staticmethod
    def check_idempotency(
        idempotency_key: str,
        operation: str,
        event_id: Optional[int] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Check if an operation with the given idempotency key has already been performed
        
        Args:
            idempotency_key: The idempotency key to check
            operation: The operation being performed
            event_id: The ID of the event being operated on
            
        Returns:
            The cached result if the operation was already performed, None otherwise
        """
        if idempotency_key in IdempotencyService._idempotency_store:
            cached_result = IdempotencyService._idempotency_store[idempotency_key]
            
            # Check if the cached result is for the same operation and event
            if (cached_result.get("operation") == operation and 
                cached_result.get("event_id") == event_id):
                return cached_result.get("result")
        
        return None
    
    @staticmethod
    def store_idempotency_result(
        idempotency_key: str,
        operation: str,
        event_id: Optional[int],
        result: Dict[str, Any]
    ) -> None:
        """
        Store the result of an operation for idempotency checking
        
        Args:
            idempotency_key: The idempotency key
            operation: The operation that was performed
            event_id: The ID of the event that was operated on
            result: The result of the operation
        """
        IdempotencyService._idempotency_store[idempotency_key] = {
            "operation": operation,
            "event_id": event_id,
            "result": result,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    @staticmethod
    def validate_event_exists(db: Session, event_id: int) -> Optional[EventModel]:
        """
        Validate that an event exists and return it
        
        Args:
            db: Database session
            event_id: The ID of the event to validate
            
        Returns:
            The event model if it exists, None otherwise
        """
        return db.query(EventModel).filter(EventModel.id == event_id).first()
    
    @staticmethod
    def validate_event_update_data(update_data: Dict[str, Any]) -> tuple[bool, str]:
        """
        Validate event update data
        
        Args:
            update_data: The data to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check for invalid field combinations
        if "start_utc" in update_data and "end_utc" in update_data:
            start_utc = update_data["start_utc"]
            end_utc = update_data["end_utc"]
            
            if isinstance(start_utc, str):
                start_utc = datetime.fromisoformat(start_utc.replace('Z', '+00:00'))
            if isinstance(end_utc, str):
                end_utc = datetime.fromisoformat(end_utc.replace('Z', '+00:00'))
            
            if start_utc >= end_utc:
                return False, "Start time must be before end time"
        
        # Validate RRULE if provided
        if "rrule" in update_data and update_data["rrule"]:
            from app.services.rrule_service import RRuleService
            is_valid, error = RRuleService.validate_rrule(update_data["rrule"])
            if not is_valid:
                return False, f"Invalid RRULE: {error}"
        
        # Validate category if provided
        if "category" in update_data and update_data["category"]:
            valid_categories = ["school", "after-school", "family"]
            if update_data["category"] not in valid_categories:
                return False, f"Invalid category. Must be one of: {', '.join(valid_categories)}"
        
        # Validate source if provided
        if "source" in update_data and update_data["source"]:
            valid_sources = ["manual", "ics", "google", "outlook"]
            if update_data["source"] not in valid_sources:
                return False, f"Invalid source. Must be one of: {', '.join(valid_sources)}"
        
        return True, ""
