"""
RRULE Service for handling recurring events and event expansion
"""

from typing import List, Optional, Union
from datetime import datetime, date, timezone
from dateutil import rrule
from dateutil.parser import parse as parse_date
import re


class RRuleService:
    """Service for handling RRULE parsing and event expansion"""
    
    @staticmethod
    def parse_rrule(rrule_str: str) -> Optional[rrule.rrule]:
        """
        Parse an RRULE string and return a dateutil rrule object
        
        Args:
            rrule_str: RRULE string (e.g., "FREQ=WEEKLY;BYDAY=TU,TH;UNTIL=2025-12-20T00:00:00Z")
            
        Returns:
            dateutil.rrule object or None if parsing fails
        """
        if not rrule_str:
            return None
            
        try:
            # Parse the RRULE string - dateutil expects it to start with "RRULE:"
            if not rrule_str.startswith("RRULE:"):
                rrule_str = f"RRULE:{rrule_str}"
            return rrule.rrulestr(rrule_str)
        except (ValueError, TypeError) as e:
            print(f"Error parsing RRULE '{rrule_str}': {e}")
            return None
    
    @staticmethod
    def expand_events(
        start_utc: datetime,
        end_utc: datetime,
        rrule_str: Optional[str] = None,
        exdates: Optional[List[str]] = None,
        until_date: Optional[datetime] = None
    ) -> List[dict]:
        """
        Expand a recurring event into individual event instances
        
        Args:
            start_utc: Start time of the original event
            end_utc: End time of the original event
            rrule_str: RRULE string for recurrence
            exdates: List of exception dates (ISO format strings)
            until_date: Optional end date for expansion
            
        Returns:
            List of event instances with start_utc, end_utc, and is_recurring flag
        """
        if not rrule_str:
            # Single event, no recurrence
            return [{
                "start_utc": start_utc,
                "end_utc": end_utc,
                "is_recurring": False,
                "original_start": start_utc
            }]
        
        # Parse RRULE
        rrule_obj = RRuleService.parse_rrule(rrule_str)
        if not rrule_obj:
            # If RRULE parsing fails, return the original event
            return [{
                "start_utc": start_utc,
                "end_utc": end_utc,
                "is_recurring": False,
                "original_start": start_utc
            }]
        
        # Parse exception dates
        exdate_objects = []
        if exdates:
            for exdate_str in exdates:
                try:
                    if isinstance(exdate_str, str):
                        # Parse date string and convert to datetime
                        exdate = parse_date(exdate_str)
                        if exdate.tzinfo is None:
                            exdate = exdate.replace(tzinfo=timezone.utc)
                        exdate_objects.append(exdate)
                except (ValueError, TypeError) as e:
                    print(f"Error parsing exdate '{exdate_str}': {e}")
        
        # Set up the rrule with the original start time
        if not rrule_str.startswith("RRULE:"):
            rrule_str = f"RRULE:{rrule_str}"
        rrule_obj = rrule.rrulestr(rrule_str, dtstart=start_utc)
        
        # Generate recurring instances
        instances = []
        duration = end_utc - start_utc
        
        # Set a reasonable limit for expansion (e.g., 2 years from start)
        if until_date is None:
            until_date = start_utc.replace(year=start_utc.year + 2)
        
        try:
            for dt in rrule_obj:
                if dt > until_date:
                    break
                
                # Check if this date is in the exception list
                is_excluded = False
                for exdate in exdate_objects:
                    # Compare dates (ignore time for exdate comparison)
                    if dt.date() == exdate.date():
                        is_excluded = True
                        break
                
                if not is_excluded:
                    instance_end = dt + duration
                    instances.append({
                        "start_utc": dt,
                        "end_utc": instance_end,
                        "is_recurring": True,
                        "original_start": start_utc
                    })
        except Exception as e:
            print(f"Error generating recurring instances: {e}")
            # Return original event if expansion fails
            return [{
                "start_utc": start_utc,
                "end_utc": end_utc,
                "is_recurring": False,
                "original_start": start_utc
            }]
        
        return instances
    
    @staticmethod
    def expand_events_in_range(
        start_utc: datetime,
        end_utc: datetime,
        rrule_str: Optional[str] = None,
        exdates: Optional[List[str]] = None,
        range_start: Optional[datetime] = None,
        range_end: Optional[datetime] = None
    ) -> List[dict]:
        """
        Expand recurring events but only return instances within a specific date range
        
        Args:
            start_utc: Start time of the original event
            end_utc: End time of the original event
            rrule_str: RRULE string for recurrence
            exdates: List of exception dates
            range_start: Start of the range to filter instances
            range_end: End of the range to filter instances
            
        Returns:
            List of event instances within the specified range
        """
        all_instances = RRuleService.expand_events(
            start_utc, end_utc, rrule_str, exdates, range_end
        )
        
        if not range_start and not range_end:
            return all_instances
        
        filtered_instances = []
        for instance in all_instances:
            instance_start = instance["start_utc"]
            instance_end = instance["end_utc"]
            
            # Check if instance overlaps with the range
            if range_start and instance_end <= range_start:
                continue
            if range_end and instance_start >= range_end:
                continue
            
            filtered_instances.append(instance)
        
        return filtered_instances
    
    @staticmethod
    def validate_rrule(rrule_str: str) -> tuple[bool, str]:
        """
        Validate an RRULE string
        
        Args:
            rrule_str: RRULE string to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not rrule_str:
            return True, ""
        
        try:
            if not rrule_str.startswith("RRULE:"):
                rrule_str = f"RRULE:{rrule_str}"
            rrule.rrulestr(rrule_str)
            return True, ""
        except (ValueError, TypeError) as e:
            return False, str(e)
    
    @staticmethod
    def get_rrule_frequency(rrule_str: str) -> Optional[str]:
        """
        Extract the frequency from an RRULE string
        
        Args:
            rrule_str: RRULE string
            
        Returns:
            Frequency string (DAILY, WEEKLY, MONTHLY, YEARLY) or None
        """
        if not rrule_str:
            return None
        
        # Simple regex to extract FREQ value
        match = re.search(r'FREQ=([A-Z]+)', rrule_str.upper())
        if match:
            return match.group(1)
        
        return None
    
    @staticmethod
    def get_rrule_until_date(rrule_str: str) -> Optional[datetime]:
        """
        Extract the UNTIL date from an RRULE string
        
        Args:
            rrule_str: RRULE string
            
        Returns:
            UNTIL date as datetime object or None
        """
        if not rrule_str:
            return None
        
        # Simple regex to extract UNTIL value
        match = re.search(r'UNTIL=([^;]+)', rrule_str.upper())
        if match:
            until_str = match.group(1)
            try:
                return parse_date(until_str)
            except (ValueError, TypeError):
                return None
        
        return None
