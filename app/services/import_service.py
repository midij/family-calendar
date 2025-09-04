"""
Import Service for handling CSV and ICS file imports
"""

import csv
import io
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timezone, date, time
from sqlalchemy.orm import Session
from dateutil import parser as date_parser
from dateutil import rrule
from icalendar import Calendar, Event as ICalEvent
from app.models.event import Event as EventModel
from app.schemas.event import EventCreate
from app.services.rrule_service import RRuleService


class ImportService:
    """Service for importing events from CSV and ICS files"""
    
    @staticmethod
    def import_csv_events(
        csv_content: str,
        default_kid_id: Optional[str] = None,
        default_category: Optional[str] = None,
        default_source: str = "csv",
        db: Session = None
    ) -> Dict[str, Any]:
        """
        Import events from CSV content
        
        Args:
            csv_content: CSV file content as string
            default_kid_id: Default kid ID for events without kid_ids
            default_category: Default category for events
            default_source: Source identifier
            db: Database session
            
        Returns:
            Dictionary with import results
        """
        results = {
            "total_rows": 0,
            "imported_events": [],
            "errors": [],
            "success_count": 0,
            "error_count": 0
        }
        
        try:
            # Parse CSV content
            csv_reader = csv.DictReader(io.StringIO(csv_content))
            rows = list(csv_reader)
            results["total_rows"] = len(rows)
            
            for row_num, row in enumerate(rows, 1):
                try:
                    # Parse and validate row data
                    event_data = ImportService._parse_csv_row(
                        row, default_kid_id, default_category, default_source
                    )
                    
                    # Create event in database
                    event = EventModel(**event_data)
                    db.add(event)
                    db.commit()
                    db.refresh(event)
                    
                    results["imported_events"].append({
                        "id": event.id,
                        "title": event.title,
                        "start_utc": event.start_utc.isoformat()
                    })
                    results["success_count"] += 1
                    
                except Exception as e:
                    error_msg = f"Row {row_num}: {str(e)}"
                    results["errors"].append(error_msg)
                    results["error_count"] += 1
                    db.rollback()
                    
        except Exception as e:
            results["errors"].append(f"CSV parsing error: {str(e)}")
            results["error_count"] += 1
            
        return results
    
    @staticmethod
    def _parse_csv_row(
        row: Dict[str, str],
        default_kid_id: Optional[str],
        default_category: Optional[str],
        default_source: str
    ) -> Dict[str, Any]:
        """
        Parse a single CSV row into event data
        
        Args:
            row: CSV row data
            default_kid_id: Default kid ID
            default_category: Default category
            default_source: Source identifier
            
        Returns:
            Dictionary with event data
        """
        # Required fields
        if not row.get("title"):
            raise ValueError("Title is required")
        
        if not row.get("start_date"):
            raise ValueError("Start date is required")
        
        # Parse dates and times
        start_date = ImportService._parse_date(row["start_date"])
        start_time = ImportService._parse_time(row.get("start_time", "00:00"))
        start_utc = datetime.combine(start_date, start_time).replace(tzinfo=timezone.utc)
        
        # Parse end date/time (optional)
        if row.get("end_date"):
            end_date = ImportService._parse_date(row["end_date"])
            end_time = ImportService._parse_time(row.get("end_time", "01:00"))
            end_utc = datetime.combine(end_date, end_time).replace(tzinfo=timezone.utc)
        else:
            # Default to 1 hour duration
            end_utc = start_utc.replace(hour=start_utc.hour + 1)
        
        # Validate time range
        if start_utc >= end_utc:
            raise ValueError("Start time must be before end time")
        
        # Parse kid_ids
        kid_ids = []
        if row.get("kid_ids"):
            kid_ids = [kid.strip() for kid in row["kid_ids"].split(",") if kid.strip()]
        elif default_kid_id:
            kid_ids = [default_kid_id]
        
        # Parse RRULE
        rrule_str = row.get("rrule", "").strip()
        if rrule_str:
            # Validate RRULE
            is_valid, error = RRuleService.validate_rrule(rrule_str)
            if not is_valid:
                raise ValueError(f"Invalid RRULE: {error}")
        
        # Build event data
        event_data = {
            "title": row["title"].strip(),
            "start_utc": start_utc,
            "end_utc": end_utc,
            "location": row.get("location", "").strip() or None,
            "rrule": rrule_str or None,
            "kid_ids": kid_ids,
            "category": row.get("category", default_category) or "family",
            "source": default_source,
            "created_by": "import"
        }
        
        return event_data
    
    @staticmethod
    def _parse_date(date_str: str) -> date:
        """Parse date string in YYYY-MM-DD format"""
        try:
            return datetime.strptime(date_str.strip(), "%Y-%m-%d").date()
        except ValueError:
            raise ValueError(f"Invalid date format: {date_str}. Expected YYYY-MM-DD")
    
    @staticmethod
    def _parse_time(time_str: str) -> time:
        """Parse time string in HH:MM format"""
        try:
            return datetime.strptime(time_str.strip(), "%H:%M").time()
        except ValueError:
            raise ValueError(f"Invalid time format: {time_str}. Expected HH:MM")
    
    @staticmethod
    def import_ics_events(
        ics_content: str,
        default_kid_id: Optional[str] = None,
        default_category: Optional[str] = None,
        default_source: str = "ics",
        db: Session = None
    ) -> Dict[str, Any]:
        """
        Import events from ICS content
        
        Args:
            ics_content: ICS file content as string
            default_kid_id: Default kid ID for events
            default_category: Default category for events
            default_source: Source identifier
            db: Database session
            
        Returns:
            Dictionary with import results
        """
        results = {
            "total_events": 0,
            "imported_events": [],
            "errors": [],
            "success_count": 0,
            "error_count": 0
        }
        
        try:
            # Parse ICS content
            calendar = Calendar.from_ical(ics_content)
            
            for component in calendar.walk():
                if component.name == "VEVENT":
                    try:
                        # Parse VEVENT component
                        event_data = ImportService._parse_ics_vevent(
                            component, default_kid_id, default_category, default_source
                        )
                        
                        # Create event in database
                        event = EventModel(**event_data)
                        db.add(event)
                        db.commit()
                        db.refresh(event)
                        
                        results["imported_events"].append({
                            "id": event.id,
                            "title": event.title,
                            "start_utc": event.start_utc.isoformat()
                        })
                        results["success_count"] += 1
                        results["total_events"] += 1
                        
                    except Exception as e:
                        error_msg = f"VEVENT parsing error: {str(e)}"
                        results["errors"].append(error_msg)
                        results["error_count"] += 1
                        results["total_events"] += 1
                        db.rollback()
                        
        except Exception as e:
            results["errors"].append(f"ICS parsing error: {str(e)}")
            results["error_count"] += 1
            
        return results
    
    @staticmethod
    def _parse_ics_vevent(
        vevent: ICalEvent,
        default_kid_id: Optional[str],
        default_category: Optional[str],
        default_source: str
    ) -> Dict[str, Any]:
        """
        Parse a VEVENT component into event data
        
        Args:
            vevent: VEVENT component from icalendar
            default_kid_id: Default kid ID
            default_category: Default category
            default_source: Source identifier
            
        Returns:
            Dictionary with event data
        """
        # Extract basic event information
        title = str(vevent.get("SUMMARY", "Untitled Event"))
        location = str(vevent.get("LOCATION", "")) if vevent.get("LOCATION") else None
        
        # Parse start and end times
        dtstart = vevent.get("DTSTART")
        dtend = vevent.get("DTEND")
        
        if not dtstart:
            raise ValueError("VEVENT must have DTSTART")
        
        # Convert to datetime objects
        start_utc = ImportService._convert_ical_datetime(dtstart)
        
        if dtend:
            end_utc = ImportService._convert_ical_datetime(dtend)
        else:
            # If no DTEND, try DURATION
            duration = vevent.get("DURATION")
            if duration:
                # Add duration to start time
                end_utc = start_utc + duration.dt
            else:
                # Default to 1 hour duration
                end_utc = start_utc.replace(hour=start_utc.hour + 1)
        
        # Validate time range
        if start_utc >= end_utc:
            raise ValueError("Start time must be before end time")
        
        # Parse RRULE
        rrule_str = None
        rrule_component = vevent.get("RRULE")
        if rrule_component:
            # Convert RRULE component to proper RRULE string
            if hasattr(rrule_component, 'to_ical'):
                # Use the to_ical method to get proper RRULE string
                rrule_str = rrule_component.to_ical().decode('utf-8')
            else:
                # Fallback to string conversion
                rrule_str = str(rrule_component)
            
            # Ensure RRULE starts with RRULE: prefix for validation
            if not rrule_str.startswith("RRULE:"):
                rrule_str = f"RRULE:{rrule_str}"
            # Validate RRULE
            is_valid, error = RRuleService.validate_rrule(rrule_str)
            if not is_valid:
                raise ValueError(f"Invalid RRULE: {error}")
            # Remove RRULE: prefix for storage
            rrule_str = rrule_str[6:] if rrule_str.startswith("RRULE:") else rrule_str
        
        # Parse EXDATE (exception dates)
        exdates = []
        for exdate in vevent.get("EXDATE", []):
            if hasattr(exdate, 'dts'):
                for dt in exdate.dts:
                    exdates.append(ImportService._convert_ical_datetime(dt).strftime("%Y-%m-%d"))
            else:
                exdates.append(ImportService._convert_ical_datetime(exdate).strftime("%Y-%m-%d"))
        
        # Parse kid_ids (from custom property or default)
        kid_ids = []
        if vevent.get("X-KID-IDS"):
            kid_ids = [kid.strip() for kid in str(vevent.get("X-KID-IDS")).split(",") if kid.strip()]
        elif default_kid_id:
            kid_ids = [default_kid_id]
        
        # Build event data
        event_data = {
            "title": title,
            "start_utc": start_utc,
            "end_utc": end_utc,
            "location": location,
            "rrule": rrule_str,
            "exdates": exdates if exdates else None,
            "kid_ids": kid_ids,
            "category": default_category or "family",
            "source": default_source,
            "created_by": "import"
        }
        
        return event_data
    
    @staticmethod
    def _convert_ical_datetime(ical_dt) -> datetime:
        """
        Convert iCalendar datetime to Python datetime
        
        Args:
            ical_dt: iCalendar datetime object
            
        Returns:
            Python datetime object in UTC
        """
        if hasattr(ical_dt, 'dt'):
            dt = ical_dt.dt
        else:
            dt = ical_dt
        
        # If it's a date object, convert to datetime
        if isinstance(dt, date) and not isinstance(dt, datetime):
            dt = datetime.combine(dt, time(0, 0))
        
        # Ensure timezone awareness
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        else:
            # Convert to UTC
            dt = dt.astimezone(timezone.utc)
        
        return dt
