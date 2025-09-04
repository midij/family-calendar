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
            # Parse RRULE parameters manually
            params = {}
            
            # Remove RRULE: prefix if present
            if rrule_str.startswith("RRULE:"):
                rrule_str = rrule_str[6:]
            
            # Parse each parameter
            for param in rrule_str.split(';'):
                if '=' in param:
                    key, value = param.split('=', 1)
                    key = key.upper()
                    
                    if key == 'FREQ':
                        freq_map = {
                            'DAILY': rrule.DAILY,
                            'WEEKLY': rrule.WEEKLY,
                            'MONTHLY': rrule.MONTHLY,
                            'YEARLY': rrule.YEARLY
                        }
                        params['freq'] = freq_map.get(value.upper())
                        
                    elif key == 'INTERVAL':
                        params['interval'] = int(value)
                        
                    elif key == 'BYDAY':
                        day_map = {
                            'MO': rrule.MO, 'TU': rrule.TU, 'WE': rrule.WE,
                            'TH': rrule.TH, 'FR': rrule.FR, 'SA': rrule.SA, 'SU': rrule.SU
                        }
                        days = []
                        for day in value.split(','):
                            day = day.strip()
                            if day in day_map:
                                days.append(day_map[day])
                        if days:
                            params['byweekday'] = days
                            
                    elif key == 'UNTIL':
                        try:
                            until_date = parse_date(value)
                            if until_date.tzinfo is None:
                                until_date = until_date.replace(tzinfo=timezone.utc)
                            params['until'] = until_date
                        except (ValueError, TypeError):
                            pass
                            
                    elif key == 'COUNT':
                        params['count'] = int(value)
            
            # Create rrule object
            if 'freq' in params:
                return rrule.rrule(**params)
            else:
                return None
                
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
        rrule_obj = RRuleService.parse_rrule(rrule_str)
        if rrule_obj:
            # Create a new rrule with dtstart
            rrule_params = {
                'freq': rrule_obj._freq,
                'dtstart': start_utc
            }
            
            # Add optional parameters if they exist
            if rrule_obj._interval:
                rrule_params['interval'] = rrule_obj._interval
            if rrule_obj._until:
                # Ensure UNTIL date has the same timezone as dtstart
                until_date = rrule_obj._until
                if start_utc.tzinfo and until_date.tzinfo is None:
                    until_date = until_date.replace(tzinfo=timezone.utc)
                elif start_utc.tzinfo is None and until_date.tzinfo:
                    until_date = until_date.replace(tzinfo=None)
                rrule_params['until'] = until_date
            if rrule_obj._count:
                rrule_params['count'] = rrule_obj._count
            if rrule_obj._byweekday:
                rrule_params['byweekday'] = rrule_obj._byweekday
            if rrule_obj._bymonthday:
                rrule_params['bymonthday'] = rrule_obj._bymonthday
            if rrule_obj._bymonth:
                rrule_params['bymonth'] = rrule_obj._bymonth
            
            rrule_obj = rrule.rrule(**rrule_params)
        
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
                    # Ensure timezone consistency with original start time
                    if start_utc.tzinfo and dt.tzinfo is None:
                        dt = dt.replace(tzinfo=timezone.utc)
                        instance_end = instance_end.replace(tzinfo=timezone.utc)
                    elif start_utc.tzinfo is None and dt.tzinfo:
                        dt = dt.replace(tzinfo=None)
                        instance_end = instance_end.replace(tzinfo=None)
                    
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
            
            # Ensure timezone consistency for comparison
            if range_start and range_start.tzinfo is None and instance_start.tzinfo:
                range_start = range_start.replace(tzinfo=timezone.utc)
            elif range_start and range_start.tzinfo and instance_start.tzinfo is None:
                instance_start = instance_start.replace(tzinfo=timezone.utc)
                instance_end = instance_end.replace(tzinfo=timezone.utc)
            
            if range_end and range_end.tzinfo is None and instance_start.tzinfo:
                range_end = range_end.replace(tzinfo=timezone.utc)
            elif range_end and range_end.tzinfo and instance_start.tzinfo is None:
                instance_start = instance_start.replace(tzinfo=timezone.utc)
                instance_end = instance_end.replace(tzinfo=timezone.utc)
            
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
            # Use our own parse_rrule method for validation
            parsed = RRuleService.parse_rrule(rrule_str)
            if parsed is None:
                return False, "Invalid RRULE format"
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
