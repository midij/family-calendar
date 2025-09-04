"""
Event Expansion Service for handling recurring events and generating event instances
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.models.event import Event as EventModel
from app.schemas.event import Event as EventSchema
from app.services.rrule_service import RRuleService


class EventExpansionService:
    """Service for expanding recurring events into individual instances"""
    
    @staticmethod
    def expand_event_to_instances(
        event: EventModel,
        range_start: Optional[datetime] = None,
        range_end: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """
        Expand a single event (recurring or not) into individual instances
        
        Args:
            event: Event model instance
            range_start: Optional start date for filtering instances
            range_end: Optional end date for filtering instances
            
        Returns:
            List of event instances with expanded data
        """
        # Convert exdates from JSON to list of strings
        exdates = event.exdates_list if hasattr(event, 'exdates_list') else (event.exdates or [])
        
        # Ensure timezone-aware datetimes for database-retrieved events
        start_utc = event.start_utc
        end_utc = event.end_utc
        if start_utc.tzinfo is None:
            start_utc = start_utc.replace(tzinfo=timezone.utc)
        if end_utc.tzinfo is None:
            end_utc = end_utc.replace(tzinfo=timezone.utc)
        
        # Expand the event using RRULE service
        instances = RRuleService.expand_events_in_range(
            start_utc=start_utc,
            end_utc=end_utc,
            rrule_str=event.rrule,
            exdates=exdates,
            range_start=range_start,
            range_end=range_end
        )
        
        # Convert instances to event-like dictionaries
        expanded_events = []
        for instance in instances:
            event_data = {
                "id": event.id,
                "title": event.title,
                "location": event.location,
                "start_utc": instance["start_utc"],
                "end_utc": instance["end_utc"],
                "rrule": event.rrule,
                "exdates": event.exdates,
                "kid_ids": event.kid_ids,
                "category": event.category,
                "source": event.source,
                "created_by": event.created_by,
                "created_at": event.created_at,
                "updated_at": event.updated_at,
                "is_recurring": instance["is_recurring"],
                "original_start": instance["original_start"],
                "instance_start": instance["start_utc"]  # For sorting and identification
            }
            expanded_events.append(event_data)
        
        return expanded_events
    
    @staticmethod
    def expand_events_to_instances(
        events: List[EventModel],
        range_start: Optional[datetime] = None,
        range_end: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """
        Expand multiple events into individual instances
        
        Args:
            events: List of Event model instances
            range_start: Optional start date for filtering instances
            range_end: Optional end date for filtering instances
            
        Returns:
            List of all expanded event instances, sorted by start time
        """
        all_instances = []
        
        for event in events:
            instances = EventExpansionService.expand_event_to_instances(
                event, range_start, range_end
            )
            all_instances.extend(instances)
        
        # Sort by start time
        all_instances.sort(key=lambda x: x["instance_start"])
        
        return all_instances
    
    @staticmethod
    def get_events_in_range(
        db: Session,
        range_start: Optional[datetime] = None,
        range_end: Optional[datetime] = None,
        kid_id: Optional[str] = None,
        category: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get all events (expanded) within a date range with optional filtering
        
        Args:
            db: Database session
            range_start: Start of date range
            range_end: End of date range
            kid_id: Optional kid ID filter
            category: Optional category filter
            
        Returns:
            List of expanded event instances
        """
        # Build query
        query = db.query(EventModel)
        
        # Apply filters
        if kid_id:
            query = query.filter(EventModel.kid_ids.like(f'%"{kid_id}"%'))
        
        if category:
            query = query.filter(EventModel.category == category)
        
        # Get events that might overlap with the range
        # We need to get events that could potentially have instances in our range
        if range_start and range_end:
            # Get events that start before our range ends and could have instances in our range
            # This is a simplified approach - in production, you might want more sophisticated logic
            query = query.filter(EventModel.start_utc <= range_end)
        
        events = query.all()
        
        # Expand all events and filter instances
        all_instances = EventExpansionService.expand_events_to_instances(
            events, range_start, range_end
        )
        
        return all_instances
    
    @staticmethod
    def get_weekly_events(
        db: Session,
        week_start: datetime,
        kid_id: Optional[str] = None,
        category: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get all events for a specific week (Monday to Sunday)
        
        Args:
            db: Database session
            week_start: Start of the week (Monday)
            kid_id: Optional kid ID filter
            category: Optional category filter
            
        Returns:
            List of expanded event instances for the week
        """
        # Calculate week end (Sunday)
        week_end = week_start.replace(hour=23, minute=59, second=59, microsecond=999999)
        week_end = week_end.replace(day=week_start.day + 6)
        
        return EventExpansionService.get_events_in_range(
            db, week_start, week_end, kid_id, category
        )
    
    @staticmethod
    def get_daily_events(
        db: Session,
        day: datetime,
        kid_id: Optional[str] = None,
        category: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get all events for a specific day
        
        Args:
            db: Database session
            day: The day to get events for
            kid_id: Optional kid ID filter
            category: Optional category filter
            
        Returns:
            List of expanded event instances for the day
        """
        day_start = day.replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day.replace(hour=23, minute=59, second=59, microsecond=999999)
        
        return EventExpansionService.get_events_in_range(
            db, day_start, day_end, kid_id, category
        )
    
    @staticmethod
    def validate_event_expansion(event: EventModel) -> tuple[bool, str]:
        """
        Validate that an event can be properly expanded
        
        Args:
            event: Event model instance
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not event.rrule:
            return True, ""  # Single event, no validation needed
        
        # Validate RRULE
        is_valid, error = RRuleService.validate_rrule(event.rrule)
        if not is_valid:
            return False, f"Invalid RRULE: {error}"
        
        # Validate exdates
        if event.exdates:
            exdates = event.exdates_list if hasattr(event, 'exdates_list') else event.exdates
            for exdate_str in exdates:
                try:
                    datetime.fromisoformat(exdate_str.replace('Z', '+00:00'))
                except (ValueError, AttributeError):
                    return False, f"Invalid exdate format: {exdate_str}"
        
        return True, ""
