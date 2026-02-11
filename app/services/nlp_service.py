"""
NLP Service for parsing natural language event messages using OpenAI
"""

from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from openai import OpenAI
import json
import logging
from app.config import settings
from app.services.rrule_service import RRuleService

logger = logging.getLogger(__name__)


class NLPService:
    """Service for parsing natural language into structured event data"""
    
    def __init__(self):
        """Initialize OpenAI client"""
        if not settings.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY not configured")
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = settings.OPENAI_MODEL
    
    def parse_event_from_text(
        self, 
        message: str, 
        kids_list: List[Dict[str, Any]], 
        timezone_str: str = "UTC"
    ) -> Dict[str, Any]:
        """
        Parse natural language message into structured event data
        
        Args:
            message: Natural language message (e.g., "Soccer practice for Emma tomorrow at 4pm")
            kids_list: List of kid dictionaries with 'name' and 'id' keys
            timezone_str: Timezone for date/time interpretation (default: UTC)
            
        Returns:
            Dictionary with parsed event data:
            {
                "title": str,
                "kid_names": List[str],
                "date": str (ISO format),
                "start_time": str (HH:MM format),
                "end_time": str (HH:MM format),
                "location": Optional[str],
                "category": str,
                "is_recurring": bool,
                "rrule": Optional[str],
                "confidence": str ("high", "medium", "low"),
                "missing_fields": List[str]
            }
        """
        try:
            # Build the prompt with current context
            prompt = self._build_prompt(message, kids_list, timezone_str)
            
            # Call OpenAI API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": prompt["system"]},
                    {"role": "user", "content": message}
                ],
                temperature=0.3,  # Lower temperature for more consistent parsing
                response_format={"type": "json_object"}
            )
            
            # Extract and parse the response
            result_text = response.choices[0].message.content
            result = json.loads(result_text)
            
            # Log raw LLM response for debugging
            logger.info(f"Raw LLM response: {json.dumps(result, indent=2)}")
            
            # Validate and clean the parsed data
            cleaned_result = self._validate_and_clean_result(result, kids_list)
            
            logger.info(f"Successfully parsed event: {cleaned_result.get('title')}")
            logger.info(f"Kid names extracted: {cleaned_result.get('kid_names', [])}")
            return cleaned_result
            
        except Exception as e:
            logger.error(f"Error parsing event from text: {e}")
            return {
                "error": str(e),
                "confidence": "low",
                "missing_fields": ["all"]
            }
    
    def _build_prompt(
        self, 
        message: str, 
        kids_list: List[Dict[str, Any]], 
        timezone_str: str
    ) -> Dict[str, str]:
        """Build the system prompt with current context"""
        
        # Get kid names for the prompt
        kid_names = [kid.get("name", "") for kid in kids_list]
        kid_names_str = ", ".join(kid_names) if kid_names else "No kids configured"
        
        # Get current date for context
        current_date = datetime.now().strftime("%Y-%m-%d")
        current_day = datetime.now().strftime("%A")
        
        system_prompt = f"""You are a family calendar assistant. Parse natural language messages into structured event data.

**Current Context:**
- Current date: {current_date} ({current_day})
- Timezone: {timezone_str}
- Available kids: {kid_names_str}

**Categories:** school, after-school, family, sports, education, health

**Recurring Events (RRULE RFC5545):**
Detect recurring patterns and generate RRULE strings:
- "every Tuesday" → FREQ=WEEKLY;BYDAY=TU
- "every Monday and Wednesday" → FREQ=WEEKLY;BYDAY=MO,WE
- "every weekday" → FREQ=WEEKLY;BYDAY=MO,TU,WE,TH,FR
- "every weekend" → FREQ=WEEKLY;BYDAY=SA,SU
- "daily" → FREQ=DAILY
- "weekly" → FREQ=WEEKLY
- "monthly on the 15th" → FREQ=MONTHLY;BYMONTHDAY=15
- "first Friday of each month" → FREQ=MONTHLY;BYDAY=1FR
- "last Monday of each month" → FREQ=MONTHLY;BYDAY=-1MO
- "every 2 weeks" → FREQ=WEEKLY;INTERVAL=2
- "every Tuesday until June" → FREQ=WEEKLY;BYDAY=TU;UNTIL=20260630T000000Z
- "every day for 30 days" → FREQ=DAILY;COUNT=30

**BYDAY codes:** MO, TU, WE, TH, FR, SA, SU
**Prefixes:** 1-5 for first to fifth, -1 for last (e.g., 1MO = first Monday, -1FR = last Friday)

**Instructions:**
1. Extract event title, kid names, date, times, location, and category
2. If no end_time specified, infer duration (typically 1 hour)
3. Detect recurring patterns and generate valid RRULE
4. If information is missing or ambiguous, list in missing_fields
5. Assign confidence: "high" (all clear), "medium" (minor inference), "low" (major ambiguity)

**Response Format (JSON only):**
{{
  "title": "Event title",
  "kid_names": ["Kid1", "Kid2"] or [] if not specified,
  "date": "YYYY-MM-DD" (first occurrence for recurring),
  "start_time": "HH:MM" (24-hour format),
  "end_time": "HH:MM" (24-hour format),
  "location": "Location" or null,
  "category": "one of: school, after-school, family, sports, education, health",
  "is_recurring": true or false,
  "rrule": "RRULE string" or null,
  "confidence": "high" or "medium" or "low",
  "missing_fields": ["field1", "field2"] or []
}}

**Examples:**

Input: "Soccer practice for Emma tomorrow at 4pm at rec center"
Output:
{{
  "title": "Soccer practice",
  "kid_names": ["Emma"],
  "date": "{(datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')}",
  "start_time": "16:00",
  "end_time": "17:00",
  "location": "rec center",
  "category": "sports",
  "is_recurring": false,
  "rrule": null,
  "confidence": "high",
  "missing_fields": []
}}

Input: "Piano lessons every Tuesday at 4pm"
Output:
{{
  "title": "Piano lessons",
  "kid_names": [],
  "date": "{self._get_next_weekday(1, timezone_str).strftime('%Y-%m-%d')}",
  "start_time": "16:00",
  "end_time": "17:00",
  "location": null,
  "category": "education",
  "is_recurring": true,
  "rrule": "FREQ=WEEKLY;BYDAY=TU",
  "confidence": "high",
  "missing_fields": ["kid_names"]
}}

Input: "Dentist checkup first Friday of each month 2pm"
Output:
{{
  "title": "Dentist checkup",
  "kid_names": [],
  "date": "{self._get_next_nth_weekday(1, 4, timezone_str).strftime('%Y-%m-%d')}",
  "start_time": "14:00",
  "end_time": "15:00",
  "location": null,
  "category": "health",
  "is_recurring": true,
  "rrule": "FREQ=MONTHLY;BYDAY=1FR",
  "confidence": "medium",
  "missing_fields": ["kid_names"]
}}

Parse the following message and return ONLY valid JSON:"""
        
        return {
            "system": system_prompt
        }
    
    def _validate_and_clean_result(
        self, 
        result: Dict[str, Any], 
        kids_list: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Validate and clean the parsed result
        
        Args:
            result: Raw result from OpenAI
            kids_list: List of available kids
            
        Returns:
            Cleaned and validated result
        """
        # Ensure required fields exist
        cleaned = {
            "title": result.get("title", "Untitled Event"),
            "kid_names": result.get("kid_names", []),
            "date": result.get("date", ""),
            "start_time": result.get("start_time", ""),
            "end_time": result.get("end_time", ""),
            "location": result.get("location"),
            "category": result.get("category", "family"),
            "is_recurring": result.get("is_recurring", False),
            "rrule": result.get("rrule"),
            "confidence": result.get("confidence", "medium"),
            "missing_fields": result.get("missing_fields", [])
        }
        
        # Validate kid names against available kids (case-insensitive)
        if cleaned["kid_names"]:
            # Create a mapping of lowercase names to actual names
            name_mapping = {kid.get("name", "").lower(): kid.get("name", "") for kid in kids_list}
            
            # Match kid names case-insensitively and use the correct case from database
            matched_names = []
            for name in cleaned["kid_names"]:
                actual_name = name_mapping.get(name.lower())
                if actual_name:
                    matched_names.append(actual_name)
                    logger.info(f"Matched LLM kid name '{name}' to database kid '{actual_name}'")
                else:
                    logger.warning(f"Could not match LLM kid name '{name}' to any kid in database")
            
            cleaned["kid_names"] = matched_names
        
        # Validate RRULE if present
        if cleaned["rrule"]:
            is_valid, error_msg = RRuleService.validate_rrule(cleaned["rrule"])
            if not is_valid:
                logger.warning(f"Invalid RRULE generated: {cleaned['rrule']}, Error: {error_msg}")
                cleaned["rrule"] = None
                cleaned["is_recurring"] = False
                cleaned["confidence"] = "low"
                if "rrule" not in cleaned["missing_fields"]:
                    cleaned["missing_fields"].append("rrule")
        
        # Validate category
        valid_categories = ["school", "after-school", "family", "sports", "education", "health"]
        if cleaned["category"] not in valid_categories:
            cleaned["category"] = "family"
        
        return cleaned
    
    def _get_next_weekday(self, weekday: int, timezone_str: str = "UTC") -> datetime:
        """
        Get the next occurrence of a weekday (0=Monday, 6=Sunday)
        
        Args:
            weekday: Day of week (0-6)
            timezone_str: Timezone to use for calculating "today" (default: UTC)
            
        Returns:
            datetime of next occurrence in the specified timezone
        """
        from zoneinfo import ZoneInfo
        
        # Get today in the target timezone
        tz = ZoneInfo(timezone_str)
        today = datetime.now(tz)
        
        days_ahead = weekday - today.weekday()
        if days_ahead <= 0:
            days_ahead += 7
        return today + timedelta(days=days_ahead)
    
    def _get_next_nth_weekday(self, nth: int, weekday: int, timezone_str: str = "UTC") -> datetime:
        """
        Get the next nth weekday of the month (e.g., first Friday)
        
        Args:
            nth: Which occurrence (1-5, or -1 for last)
            weekday: Day of week (0=Monday, 6=Sunday)
            timezone_str: Timezone to use for calculating "today" (default: UTC)
            
        Returns:
            datetime of next occurrence in the specified timezone
        """
        from dateutil.rrule import rrule, MONTHLY
        from zoneinfo import ZoneInfo
        
        # Get today in the target timezone
        tz = ZoneInfo(timezone_str)
        today = datetime.now(tz)
        
        # Start from next month to avoid conflicts
        start_date = today.replace(day=1) + timedelta(days=32)
        start_date = start_date.replace(day=1)
        
        # Generate occurrences
        rule = rrule(
            MONTHLY,
            byweekday=weekday,
            bysetpos=nth,
            dtstart=start_date,
            count=1
        )
        
        result = list(rule)
        return result[0] if result else today + timedelta(days=1)
    
    @staticmethod
    def rrule_to_human_readable(rrule_str: str) -> str:
        """
        Convert RRULE string to human-readable text
        
        Args:
            rrule_str: RRULE string (e.g., "FREQ=WEEKLY;BYDAY=TU")
            
        Returns:
            Human-readable string (e.g., "Weekly on Tuesday")
        """
        if not rrule_str:
            return "Does not repeat"
        
        try:
            # Parse RRULE components
            parts = {}
            for part in rrule_str.split(';'):
                if '=' in part:
                    key, value = part.split('=', 1)
                    parts[key] = value
            
            freq = parts.get('FREQ', '').lower()
            byday = parts.get('BYDAY', '')
            interval = parts.get('INTERVAL', '1')
            until = parts.get('UNTIL', '')
            count = parts.get('COUNT', '')
            bymonthday = parts.get('BYMONTHDAY', '')
            
            # Build human-readable string
            result = []
            
            # Frequency
            if freq == 'daily':
                if interval == '1':
                    result.append("Daily")
                else:
                    result.append(f"Every {interval} days")
            elif freq == 'weekly':
                if interval == '1':
                    result.append("Weekly")
                else:
                    result.append(f"Every {interval} weeks")
            elif freq == 'monthly':
                if interval == '1':
                    result.append("Monthly")
                else:
                    result.append(f"Every {interval} months")
            elif freq == 'yearly':
                result.append("Yearly")
            
            # Days
            if byday:
                day_names = {
                    'MO': 'Monday', 'TU': 'Tuesday', 'WE': 'Wednesday',
                    'TH': 'Thursday', 'FR': 'Friday', 'SA': 'Saturday', 'SU': 'Sunday'
                }
                
                # Handle nth weekday (e.g., 1MO = first Monday)
                if byday[0].isdigit() or byday[0] == '-':
                    nth_map = {'1': 'first', '2': 'second', '3': 'third', '4': 'fourth', '5': 'fifth', '-1': 'last'}
                    if byday[0] == '-':
                        nth = byday[:2]
                        day = byday[2:]
                    else:
                        nth = byday[0]
                        day = byday[1:]
                    result.append(f"on the {nth_map.get(nth, nth)} {day_names.get(day, day)}")
                else:
                    days = [day_names.get(d, d) for d in byday.split(',')]
                    if len(days) == 1:
                        result.append(f"on {days[0]}")
                    else:
                        result.append(f"on {', '.join(days[:-1])} and {days[-1]}")
            
            if bymonthday:
                result.append(f"on day {bymonthday}")
            
            # End condition
            if until:
                # Parse date from UNTIL (format: YYYYMMDDTHHMMSSZ)
                try:
                    until_date = datetime.strptime(until[:8], '%Y%m%d').strftime('%B %d, %Y')
                    result.append(f"until {until_date}")
                except:
                    pass
            elif count:
                result.append(f"for {count} times")
            
            return " ".join(result)
            
        except Exception as e:
            logger.error(f"Error converting RRULE to human readable: {e}")
            return rrule_str
