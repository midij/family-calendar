import pytest
from datetime import datetime, timezone, timedelta
from app.services.rrule_service import RRuleService


class TestRRuleService:
    """Test suite for RRULE service functionality"""
    
    def test_parse_rrule_valid(self):
        """Test parsing valid RRULE strings"""
        # Weekly recurrence
        rrule_str = "FREQ=WEEKLY;BYDAY=TU,TH;UNTIL=2025-12-20T00:00:00Z"
        rrule_obj = RRuleService.parse_rrule(rrule_str)
        assert rrule_obj is not None
        
        # Daily recurrence
        rrule_str = "FREQ=DAILY;INTERVAL=2"
        rrule_obj = RRuleService.parse_rrule(rrule_str)
        assert rrule_obj is not None
        
        # Monthly recurrence
        rrule_str = "FREQ=MONTHLY;BYMONTHDAY=1"
        rrule_obj = RRuleService.parse_rrule(rrule_str)
        assert rrule_obj is not None
    
    def test_parse_rrule_invalid(self):
        """Test parsing invalid RRULE strings"""
        # Invalid RRULE
        rrule_str = "INVALID=RULE"
        rrule_obj = RRuleService.parse_rrule(rrule_str)
        assert rrule_obj is None
        
        # Empty string
        rrule_obj = RRuleService.parse_rrule("")
        assert rrule_obj is None
        
        # None
        rrule_obj = RRuleService.parse_rrule(None)
        assert rrule_obj is None
    
    def test_expand_events_single(self):
        """Test expanding a single (non-recurring) event"""
        start_utc = datetime(2025, 9, 2, 8, 0, 0, tzinfo=timezone.utc)
        end_utc = datetime(2025, 9, 2, 9, 0, 0, tzinfo=timezone.utc)
        
        instances = RRuleService.expand_events(start_utc, end_utc)
        
        assert len(instances) == 1
        assert instances[0]["start_utc"] == start_utc
        assert instances[0]["end_utc"] == end_utc
        assert instances[0]["is_recurring"] is False
    
    def test_expand_events_weekly(self):
        """Test expanding weekly recurring events"""
        start_utc = datetime(2025, 9, 2, 8, 0, 0, tzinfo=timezone.utc)  # Tuesday
        end_utc = datetime(2025, 9, 2, 9, 0, 0, tzinfo=timezone.utc)
        rrule_str = "FREQ=WEEKLY;BYDAY=TU,TH;UNTIL=2025-09-30T00:00:00Z"
        
        instances = RRuleService.expand_events(start_utc, end_utc, rrule_str)
        
        assert len(instances) > 1
        assert all(instance["is_recurring"] for instance in instances)
        
        # Check that instances are on Tuesdays and Thursdays
        for instance in instances:
            weekday = instance["start_utc"].weekday()
            assert weekday in [1, 3]  # Tuesday=1, Thursday=3
    
    def test_expand_events_daily(self):
        """Test expanding daily recurring events"""
        start_utc = datetime(2025, 9, 1, 8, 0, 0, tzinfo=timezone.utc)
        end_utc = datetime(2025, 9, 1, 9, 0, 0, tzinfo=timezone.utc)
        rrule_str = "FREQ=DAILY;INTERVAL=1;UNTIL=2025-09-05T00:00:00Z"
        
        instances = RRuleService.expand_events(start_utc, end_utc, rrule_str)
        
        assert len(instances) == 4  # 4 days from Sept 1-4 (UNTIL is exclusive)
        assert all(instance["is_recurring"] for instance in instances)
        
        # Check that instances are consecutive days
        for i, instance in enumerate(instances):
            expected_date = start_utc + timedelta(days=i)
            assert instance["start_utc"].date() == expected_date.date()
    
    def test_expand_events_with_exdates(self):
        """Test expanding events with exception dates"""
        start_utc = datetime(2025, 9, 1, 8, 0, 0, tzinfo=timezone.utc)
        end_utc = datetime(2025, 9, 1, 9, 0, 0, tzinfo=timezone.utc)
        rrule_str = "FREQ=DAILY;INTERVAL=1;UNTIL=2025-09-05T00:00:00Z"
        exdates = ["2025-09-02", "2025-09-04"]
        
        instances = RRuleService.expand_events(start_utc, end_utc, rrule_str, exdates)
        
        # Should have 2 instances (Sept 1, 3) - excluding Sept 2 and 4, and UNTIL is exclusive
        assert len(instances) == 2
        
        # Check that excluded dates are not present
        instance_dates = [instance["start_utc"].date() for instance in instances]
        assert datetime(2025, 9, 2).date() not in instance_dates
        assert datetime(2025, 9, 4).date() not in instance_dates
    
    def test_expand_events_in_range(self):
        """Test expanding events within a specific date range"""
        start_utc = datetime(2025, 9, 1, 8, 0, 0, tzinfo=timezone.utc)
        end_utc = datetime(2025, 9, 1, 9, 0, 0, tzinfo=timezone.utc)
        rrule_str = "FREQ=DAILY;INTERVAL=1;UNTIL=2025-09-10T00:00:00Z"
        range_start = datetime(2025, 9, 3, 0, 0, 0, tzinfo=timezone.utc)
        range_end = datetime(2025, 9, 7, 0, 0, 0, tzinfo=timezone.utc)
        
        instances = RRuleService.expand_events_in_range(
            start_utc, end_utc, rrule_str, None, range_start, range_end
        )
        
        # Should have instances for Sept 3, 4, 5, 6 (within range)
        assert len(instances) == 4
        
        for instance in instances:
            assert range_start <= instance["start_utc"] < range_end
    
    def test_validate_rrule(self):
        """Test RRULE validation"""
        # Valid RRULE
        is_valid, error = RRuleService.validate_rrule("FREQ=WEEKLY;BYDAY=TU,TH")
        assert is_valid is True
        assert error == ""
        
        # Invalid RRULE
        is_valid, error = RRuleService.validate_rrule("INVALID=RULE")
        assert is_valid is False
        assert "INVALID" in error
        
        # Empty RRULE
        is_valid, error = RRuleService.validate_rrule("")
        assert is_valid is True
        assert error == ""
    
    def test_get_rrule_frequency(self):
        """Test extracting frequency from RRULE"""
        # Weekly
        freq = RRuleService.get_rrule_frequency("FREQ=WEEKLY;BYDAY=TU,TH")
        assert freq == "WEEKLY"
        
        # Daily
        freq = RRuleService.get_rrule_frequency("FREQ=DAILY;INTERVAL=2")
        assert freq == "DAILY"
        
        # Monthly
        freq = RRuleService.get_rrule_frequency("FREQ=MONTHLY;BYMONTHDAY=1")
        assert freq == "MONTHLY"
        
        # No frequency
        freq = RRuleService.get_rrule_frequency("BYDAY=TU,TH")
        assert freq is None
        
        # Empty
        freq = RRuleService.get_rrule_frequency("")
        assert freq is None
    
    def test_get_rrule_until_date(self):
        """Test extracting UNTIL date from RRULE"""
        # With UNTIL date
        until_date = RRuleService.get_rrule_until_date(
            "FREQ=WEEKLY;BYDAY=TU,TH;UNTIL=2025-12-20T00:00:00Z"
        )
        assert until_date is not None
        assert until_date.year == 2025
        assert until_date.month == 12
        assert until_date.day == 20
        
        # Without UNTIL date
        until_date = RRuleService.get_rrule_until_date("FREQ=WEEKLY;BYDAY=TU,TH")
        assert until_date is None
        
        # Empty
        until_date = RRuleService.get_rrule_until_date("")
        assert until_date is None
    
    def test_complex_rrule_patterns(self):
        """Test complex RRULE patterns"""
        start_utc = datetime(2025, 9, 1, 8, 0, 0, tzinfo=timezone.utc)
        end_utc = datetime(2025, 9, 1, 9, 0, 0, tzinfo=timezone.utc)
        
        # Every other week on Tuesday and Thursday
        rrule_str = "FREQ=WEEKLY;INTERVAL=2;BYDAY=TU,TH;UNTIL=2025-10-01T00:00:00Z"
        instances = RRuleService.expand_events(start_utc, end_utc, rrule_str)
        
        assert len(instances) > 0
        assert all(instance["is_recurring"] for instance in instances)
        
        # Check that instances are on Tuesdays and Thursdays
        for instance in instances:
            weekday = instance["start_utc"].weekday()
            assert weekday in [1, 3]  # Tuesday=1, Thursday=3
    
    def test_timezone_handling(self):
        """Test timezone handling in RRULE expansion"""
        # Event in UTC
        start_utc = datetime(2025, 9, 2, 8, 0, 0, tzinfo=timezone.utc)
        end_utc = datetime(2025, 9, 2, 9, 0, 0, tzinfo=timezone.utc)
        rrule_str = "FREQ=WEEKLY;BYDAY=TU;UNTIL=2025-09-16T00:00:00Z"
        
        instances = RRuleService.expand_events(start_utc, end_utc, rrule_str)
        
        assert len(instances) == 2  # Sept 2, 9 (UNTIL is exclusive)
        
        # All instances should maintain UTC timezone
        for instance in instances:
            assert instance["start_utc"].tzinfo == timezone.utc
            assert instance["end_utc"].tzinfo == timezone.utc
