"""
Tests for Telegram bot integration and NLP parsing
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock
from app.services.nlp_service import NLPService
from app.services.telegram_service import TelegramService


class TestNLPService:
    """Test NLP parsing functionality"""
    
    @pytest.fixture
    def nlp_service(self):
        """Create NLP service with mocked OpenAI"""
        with patch('app.services.nlp_service.OpenAI'):
            service = NLPService()
            return service
    
    @pytest.fixture
    def kids_list(self):
        """Sample kids list"""
        return [
            {"id": 1, "name": "Emma"},
            {"id": 2, "name": "Noah"},
            {"id": 3, "name": "Sophie"}
        ]
    
    def test_rrule_to_human_readable_weekly(self):
        """Test RRULE to human readable conversion - weekly"""
        result = NLPService.rrule_to_human_readable("FREQ=WEEKLY;BYDAY=TU")
        assert result == "Weekly on Tuesday"
    
    def test_rrule_to_human_readable_multiple_days(self):
        """Test RRULE to human readable conversion - multiple days"""
        result = NLPService.rrule_to_human_readable("FREQ=WEEKLY;BYDAY=MO,WE,FR")
        assert result == "Weekly on Monday, Wednesday and Friday"
    
    def test_rrule_to_human_readable_daily(self):
        """Test RRULE to human readable conversion - daily"""
        result = NLPService.rrule_to_human_readable("FREQ=DAILY")
        assert result == "Daily"
    
    def test_rrule_to_human_readable_monthly_nth(self):
        """Test RRULE to human readable conversion - nth weekday"""
        result = NLPService.rrule_to_human_readable("FREQ=MONTHLY;BYDAY=1FR")
        assert result == "Monthly on the first Friday"
    
    def test_rrule_to_human_readable_with_until(self):
        """Test RRULE to human readable conversion - with end date"""
        result = NLPService.rrule_to_human_readable("FREQ=WEEKLY;BYDAY=SA;UNTIL=20260630T000000Z")
        assert "Weekly on Saturday until" in result
        assert "June 30, 2026" in result
    
    def test_rrule_to_human_readable_with_count(self):
        """Test RRULE to human readable conversion - with count"""
        result = NLPService.rrule_to_human_readable("FREQ=DAILY;COUNT=30")
        assert result == "Daily for 30 times"
    
    def test_rrule_to_human_readable_invalid(self):
        """Test RRULE to human readable conversion - invalid input"""
        result = NLPService.rrule_to_human_readable(None)
        assert result == "Does not repeat"
    
    def test_get_next_weekday(self):
        """Test getting next weekday"""
        service = NLPService()
        # Monday is 0, Sunday is 6
        next_monday = service._get_next_weekday(0)
        assert next_monday.weekday() == 0
        assert next_monday > datetime.now()
    
    @patch('app.services.nlp_service.OpenAI')
    def test_parse_simple_event(self, mock_openai, kids_list):
        """Test parsing a simple one-time event"""
        # Mock OpenAI response
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = '''
        {
            "title": "Soccer practice",
            "kid_names": ["Emma"],
            "date": "2026-02-11",
            "start_time": "16:00",
            "end_time": "17:00",
            "location": "rec center",
            "category": "sports",
            "is_recurring": false,
            "rrule": null,
            "confidence": "high",
            "missing_fields": []
        }
        '''
        mock_openai.return_value.chat.completions.create.return_value = mock_response
        
        service = NLPService()
        result = service.parse_event_from_text(
            "Soccer practice for Emma tomorrow at 4pm at rec center",
            kids_list
        )
        
        assert result["title"] == "Soccer practice"
        assert result["kid_names"] == ["Emma"]
        assert result["category"] == "sports"
        assert result["is_recurring"] is False
        assert result["rrule"] is None
    
    @patch('app.services.nlp_service.OpenAI')
    def test_parse_recurring_event(self, mock_openai, kids_list):
        """Test parsing a recurring event"""
        # Mock OpenAI response
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = '''
        {
            "title": "Piano lessons",
            "kid_names": [],
            "date": "2026-02-11",
            "start_time": "16:00",
            "end_time": "17:00",
            "location": null,
            "category": "education",
            "is_recurring": true,
            "rrule": "FREQ=WEEKLY;BYDAY=TU",
            "confidence": "high",
            "missing_fields": ["kid_names"]
        }
        '''
        mock_openai.return_value.chat.completions.create.return_value = mock_response
        
        service = NLPService()
        result = service.parse_event_from_text(
            "Piano lessons every Tuesday at 4pm",
            kids_list
        )
        
        assert result["title"] == "Piano lessons"
        assert result["is_recurring"] is True
        assert result["rrule"] == "FREQ=WEEKLY;BYDAY=TU"
        assert result["category"] == "education"
    
    @patch('app.services.nlp_service.OpenAI')
    def test_parse_invalid_kid_name(self, mock_openai, kids_list):
        """Test parsing with invalid kid name"""
        # Mock OpenAI response with invalid kid name
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = '''
        {
            "title": "Dance class",
            "kid_names": ["InvalidKid"],
            "date": "2026-02-11",
            "start_time": "16:00",
            "end_time": "17:00",
            "location": null,
            "category": "sports",
            "is_recurring": false,
            "rrule": null,
            "confidence": "medium",
            "missing_fields": []
        }
        '''
        mock_openai.return_value.chat.completions.create.return_value = mock_response
        
        service = NLPService()
        result = service.parse_event_from_text(
            "Dance class for InvalidKid tomorrow",
            kids_list
        )
        
        # Invalid kid names should be filtered out
        assert result["kid_names"] == []
    
    @patch('app.services.nlp_service.OpenAI')
    def test_parse_invalid_rrule(self, mock_openai, kids_list):
        """Test parsing with invalid RRULE"""
        # Mock OpenAI response with invalid RRULE
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = '''
        {
            "title": "Test event",
            "kid_names": [],
            "date": "2026-02-11",
            "start_time": "16:00",
            "end_time": "17:00",
            "location": null,
            "category": "family",
            "is_recurring": true,
            "rrule": "INVALID_RRULE",
            "confidence": "high",
            "missing_fields": []
        }
        '''
        mock_openai.return_value.chat.completions.create.return_value = mock_response
        
        service = NLPService()
        result = service.parse_event_from_text(
            "Test event",
            kids_list
        )
        
        # Invalid RRULE should be nullified
        assert result["rrule"] is None
        assert result["is_recurring"] is False
        assert result["confidence"] == "low"


class TestTelegramService:
    """Test Telegram service functionality"""
    
    @pytest.fixture
    def telegram_service(self):
        """Create Telegram service with mocked config"""
        with patch('app.services.telegram_service.settings') as mock_settings:
            mock_settings.TELEGRAM_BOT_TOKEN = "test_token"
            mock_settings.TELEGRAM_ALLOWED_USER_IDS = "123456,789012"
            service = TelegramService()
            return service
    
    def test_parse_allowed_users(self, telegram_service):
        """Test parsing allowed user IDs"""
        assert telegram_service.allowed_user_ids == [123456, 789012]
    
    def test_verify_user_authorized(self, telegram_service):
        """Test user verification - authorized"""
        assert telegram_service.verify_user(123456) is True
    
    def test_verify_user_unauthorized(self, telegram_service):
        """Test user verification - unauthorized"""
        assert telegram_service.verify_user(999999) is False
    
    @pytest.mark.asyncio
    async def test_send_message(self, telegram_service):
        """Test sending a message"""
        with patch.object(telegram_service, 'get_application') as mock_get_app:
            mock_app = AsyncMock()
            mock_bot = AsyncMock()
            mock_message = Mock()
            mock_message.message_id = 123
            mock_message.chat_id = 456
            mock_bot.send_message.return_value = mock_message
            mock_app.bot = mock_bot
            mock_get_app.return_value = mock_app
            
            result = await telegram_service.send_message(456, "Test message")
            
            assert result["success"] is True
            assert result["message_id"] == 123
            assert result["chat_id"] == 456
    
    @pytest.mark.asyncio
    async def test_send_confirmation(self, telegram_service):
        """Test sending confirmation message"""
        event_data = {
            "title": "Soccer practice",
            "kid_names": ["Emma"],
            "date": "2026-02-11",
            "start_time": "16:00",
            "end_time": "17:00",
            "location": "rec center",
            "category": "sports",
            "is_recurring": False,
            "confidence": "high",
            "missing_fields": []
        }
        
        with patch.object(telegram_service, 'send_message') as mock_send:
            mock_send.return_value = {"success": True, "message_id": 123}
            
            result = await telegram_service.send_confirmation(456, event_data)
            
            assert result["success"] is True
            # Check that send_message was called with proper arguments
            mock_send.assert_called_once()
            call_args = mock_send.call_args
            assert call_args[0][0] == 456  # chat_id
            assert "Soccer practice" in call_args[0][1]  # message text contains title
            # Check reply_markup in either positional or keyword args
            has_markup = (len(call_args[0]) > 2 and call_args[0][2] is not None) or \
                         (call_args[1].get('reply_markup') is not None if call_args[1] else False)
            assert has_markup  # has buttons
    
    @pytest.mark.asyncio
    async def test_send_help_message(self, telegram_service):
        """Test sending help message"""
        with patch.object(telegram_service, 'send_message') as mock_send:
            mock_send.return_value = {"success": True}
            
            result = await telegram_service.send_help_message(456, ["Emma", "Noah"])
            
            assert result["success"] is True
            mock_send.assert_called_once()
            call_args = mock_send.call_args
            assert "Emma, Noah" in call_args[0][1]  # kid names in message
    
    @pytest.mark.asyncio
    async def test_send_error_message(self, telegram_service):
        """Test sending error message"""
        with patch.object(telegram_service, 'send_message') as mock_send:
            mock_send.return_value = {"success": True}
            
            result = await telegram_service.send_error_message(456, "Something went wrong")
            
            assert result["success"] is True
            mock_send.assert_called_once()
            call_args = mock_send.call_args
            assert "Error" in call_args[0][1]
            assert "Something went wrong" in call_args[0][1]


# Integration test scenarios (manual testing checklist)
"""
Manual Testing Checklist:

ONE-TIME EVENTS:
1. "Dentist for Emma tomorrow 2pm" 
   - Should create event for tomorrow at 14:00
   
2. "Swimming lesson for Emma and Noah Saturday 10am"
   - Should create event for next Saturday at 10:00 with both kids
   
3. "Family dinner this Friday 6pm at Luigi's"
   - Should include location, category=family
   
4. "Dance for InvalidKid tomorrow"
   - Should warn about unknown kid name

RECURRING EVENTS:
5. "Piano lessons every Tuesday 4pm"
   - Should create with RRULE: FREQ=WEEKLY;BYDAY=TU
   
6. "Soccer practice every Monday and Wednesday 5pm"
   - Should create with RRULE: FREQ=WEEKLY;BYDAY=MO,WE
   
7. "Study time every day at 6pm"
   - Should create with RRULE: FREQ=DAILY
   
8. "Dentist checkup first Friday of each month 2pm"
   - Should create with RRULE: FREQ=MONTHLY;BYDAY=1FR
   
9. "Swimming lessons every Saturday until end of summer"
   - Should create with RRULE: FREQ=WEEKLY;BYDAY=SA;UNTIL=...
   
10. Test invalid RRULE detection and error handling

EDGE CASES:
11. "Something tomorrow" - ambiguous, should ask for more details
12. Empty message
13. Message with only command (/start, /help)
14. Very long message (>1000 chars)
15. Special characters and emojis
"""
