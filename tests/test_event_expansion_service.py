import pytest
from datetime import datetime, timezone, timedelta
from app.services.event_expansion_service import EventExpansionService
from app.models.event import Event


class TestEventExpansionService:
    """Test suite for Event Expansion Service functionality"""
    
    def test_expand_single_event(self, db_session):
        """Test expanding a single (non-recurring) event"""
        # Create a single event
        event = Event(
            title="Single Event",
            start_utc=datetime(2025, 9, 2, 8, 0, 0, tzinfo=timezone.utc),
            end_utc=datetime(2025, 9, 2, 9, 0, 0, tzinfo=timezone.utc),
            category="family",
            source="manual"
        )
        db_session.add(event)
        db_session.commit()
        db_session.refresh(event)
        
        # Expand the event
        instances = EventExpansionService.expand_event_to_instances(event)
        
        assert len(instances) == 1
        assert instances[0]["title"] == "Single Event"
        assert instances[0]["is_recurring"] is False
        assert instances[0]["id"] == event.id
    
    def test_expand_recurring_event(self, db_session):
        """Test expanding a recurring event"""
        # Create a recurring event
        event = Event(
            title="Weekly Piano Lesson",
            start_utc=datetime(2025, 9, 2, 8, 0, 0, tzinfo=timezone.utc),  # Tuesday
            end_utc=datetime(2025, 9, 2, 9, 0, 0, tzinfo=timezone.utc),
            rrule="FREQ=WEEKLY;BYDAY=TU;UNTIL=2025-09-30T00:00:00Z",
            category="after-school",
            source="manual"
        )
        db_session.add(event)
        db_session.commit()
        db_session.refresh(event)
        
        # Expand the event
        instances = EventExpansionService.expand_event_to_instances(event)
        
        assert len(instances) > 1
        assert all(instance["is_recurring"] for instance in instances)
        assert all(instance["title"] == "Weekly Piano Lesson" for instance in instances)
        
        # Check that all instances are on Tuesdays
        for instance in instances:
            assert instance["start_utc"].weekday() == 1  # Tuesday
    
    def test_expand_event_with_exdates(self, db_session):
        """Test expanding a recurring event with exception dates"""
        # Create a recurring event with exdates
        event = Event(
            title="Daily Meeting",
            start_utc=datetime(2025, 9, 1, 8, 0, 0, tzinfo=timezone.utc),
            end_utc=datetime(2025, 9, 1, 9, 0, 0, tzinfo=timezone.utc),
            rrule="FREQ=DAILY;INTERVAL=1;UNTIL=2025-09-05T00:00:00Z",
            exdates=["2025-09-02", "2025-09-04"],
            category="family",
            source="manual"
        )
        db_session.add(event)
        db_session.commit()
        db_session.refresh(event)
        
        # Expand the event
        instances = EventExpansionService.expand_event_to_instances(event)
        
        # Should have 2 instances (Sept 1, 3) - excluding Sept 2 and 4, and UNTIL is exclusive
        assert len(instances) == 2
        
        # Check that excluded dates are not present
        instance_dates = [instance["start_utc"].date() for instance in instances]
        assert datetime(2025, 9, 2).date() not in instance_dates
        assert datetime(2025, 9, 4).date() not in instance_dates
    
    def test_expand_event_in_range(self, db_session):
        """Test expanding an event within a specific date range"""
        # Create a recurring event
        event = Event(
            title="Daily Event",
            start_utc=datetime(2025, 9, 1, 8, 0, 0, tzinfo=timezone.utc),
            end_utc=datetime(2025, 9, 1, 9, 0, 0, tzinfo=timezone.utc),
            rrule="FREQ=DAILY;INTERVAL=1;UNTIL=2025-09-10T00:00:00Z",
            category="family",
            source="manual"
        )
        db_session.add(event)
        db_session.commit()
        db_session.refresh(event)
        
        # Expand within a specific range
        range_start = datetime(2025, 9, 3, 0, 0, 0, tzinfo=timezone.utc)
        range_end = datetime(2025, 9, 7, 0, 0, 0, tzinfo=timezone.utc)
        
        instances = EventExpansionService.expand_event_to_instances(
            event, range_start, range_end
        )
        
        # Should have instances for Sept 3, 4, 5, 6 (within range)
        assert len(instances) == 4
        
        for instance in instances:
            assert range_start <= instance["start_utc"] < range_end
    
    def test_expand_multiple_events(self, db_session):
        """Test expanding multiple events"""
        # Create multiple events
        events = [
            Event(
                title="Single Event",
                start_utc=datetime(2025, 9, 2, 8, 0, 0, tzinfo=timezone.utc),
                end_utc=datetime(2025, 9, 2, 9, 0, 0, tzinfo=timezone.utc),
                category="family",
                source="manual"
            ),
            Event(
                title="Weekly Event",
                start_utc=datetime(2025, 9, 1, 10, 0, 0, tzinfo=timezone.utc),
                end_utc=datetime(2025, 9, 1, 11, 0, 0, tzinfo=timezone.utc),
                rrule="FREQ=WEEKLY;BYDAY=MO;UNTIL=2025-09-15T00:00:00Z",
                category="family",
                source="manual"
            )
        ]
        
        for event in events:
            db_session.add(event)
        db_session.commit()
        
        for event in events:
            db_session.refresh(event)
        
        # Expand all events
        instances = EventExpansionService.expand_events_to_instances(events)
        
        # Should have 1 single event + 2 weekly events (Sept 1, 8) - UNTIL is exclusive
        assert len(instances) == 3
        
        # Check that instances are sorted by start time
        for i in range(len(instances) - 1):
            assert instances[i]["instance_start"] <= instances[i + 1]["instance_start"]
    
    def test_get_events_in_range(self, db_session):
        """Test getting events in a specific date range"""
        # Create events
        events = [
            Event(
                title="Event 1",
                start_utc=datetime(2025, 9, 1, 8, 0, 0, tzinfo=timezone.utc),
                end_utc=datetime(2025, 9, 1, 9, 0, 0, tzinfo=timezone.utc),
                category="family",
                source="manual"
            ),
            Event(
                title="Event 2",
                start_utc=datetime(2025, 9, 5, 8, 0, 0, tzinfo=timezone.utc),
                end_utc=datetime(2025, 9, 5, 9, 0, 0, tzinfo=timezone.utc),
                category="school",
                source="manual"
            ),
            Event(
                title="Weekly Event",
                start_utc=datetime(2025, 9, 2, 8, 0, 0, tzinfo=timezone.utc),
                end_utc=datetime(2025, 9, 2, 9, 0, 0, tzinfo=timezone.utc),
                rrule="FREQ=WEEKLY;BYDAY=TU;UNTIL=2025-09-16T00:00:00Z",
                category="family",
                source="manual"
            )
        ]
        
        for event in events:
            db_session.add(event)
        db_session.commit()
        
        # Get events in range Sept 1-10
        range_start = datetime(2025, 9, 1, 0, 0, 0, tzinfo=timezone.utc)
        range_end = datetime(2025, 9, 10, 0, 0, 0, tzinfo=timezone.utc)
        
        instances = EventExpansionService.get_events_in_range(
            db_session, range_start, range_end
        )
        
        # Should have Event 1, Event 2, and 2 instances of Weekly Event (Sept 2, 9)
        assert len(instances) == 4
        
        # Check that all instances are within the range
        for instance in instances:
            assert range_start <= instance["start_utc"] < range_end
    
    def test_get_events_with_filters(self, db_session):
        """Test getting events with kid_id and category filters"""
        # Create events with different categories and kid_ids
        events = [
            Event(
                title="Family Event",
                start_utc=datetime(2025, 9, 1, 8, 0, 0, tzinfo=timezone.utc),
                end_utc=datetime(2025, 9, 1, 9, 0, 0, tzinfo=timezone.utc),
                kid_ids=["1"],
                category="family",
                source="manual"
            ),
            Event(
                title="School Event",
                start_utc=datetime(2025, 9, 2, 8, 0, 0, tzinfo=timezone.utc),
                end_utc=datetime(2025, 9, 2, 9, 0, 0, tzinfo=timezone.utc),
                kid_ids=["2"],
                category="school",
                source="manual"
            ),
            Event(
                title="Another Family Event",
                start_utc=datetime(2025, 9, 3, 8, 0, 0, tzinfo=timezone.utc),
                end_utc=datetime(2025, 9, 3, 9, 0, 0, tzinfo=timezone.utc),
                kid_ids=["1", "2"],
                category="family",
                source="manual"
            )
        ]
        
        for event in events:
            db_session.add(event)
        db_session.commit()
        
        # Filter by category
        family_instances = EventExpansionService.get_events_in_range(
            db_session, category="family"
        )
        assert len(family_instances) == 2
        assert all(instance["category"] == "family" for instance in family_instances)
        
        # Filter by kid_id
        kid1_instances = EventExpansionService.get_events_in_range(
            db_session, kid_id="1"
        )
        assert len(kid1_instances) == 2
        assert all("1" in instance["kid_ids"] for instance in kid1_instances)
    
    def test_get_weekly_events(self, db_session):
        """Test getting events for a specific week"""
        # Create events
        events = [
            Event(
                title="Monday Event",
                start_utc=datetime(2025, 9, 1, 8, 0, 0, tzinfo=timezone.utc),  # Monday
                end_utc=datetime(2025, 9, 1, 9, 0, 0, tzinfo=timezone.utc),
                category="family",
                source="manual"
            ),
            Event(
                title="Weekly Event",
                start_utc=datetime(2025, 9, 2, 8, 0, 0, tzinfo=timezone.utc),  # Tuesday
                end_utc=datetime(2025, 9, 2, 9, 0, 0, tzinfo=timezone.utc),
                rrule="FREQ=WEEKLY;BYDAY=TU;UNTIL=2025-09-30T00:00:00Z",
                category="family",
                source="manual"
            )
        ]
        
        for event in events:
            db_session.add(event)
        db_session.commit()
        
        # Get events for the week starting Sept 1 (Monday)
        week_start = datetime(2025, 9, 1, 0, 0, 0, tzinfo=timezone.utc)
        
        weekly_instances = EventExpansionService.get_weekly_events(
            db_session, week_start
        )
        
        # Should have Monday Event and Tuesday Weekly Event
        assert len(weekly_instances) == 2
        
        # Check that all instances are within the week
        for instance in weekly_instances:
            assert week_start <= instance["start_utc"] < week_start + timedelta(days=7)
    
    def test_get_daily_events(self, db_session):
        """Test getting events for a specific day"""
        # Create events
        events = [
            Event(
                title="Morning Event",
                start_utc=datetime(2025, 9, 2, 8, 0, 0, tzinfo=timezone.utc),
                end_utc=datetime(2025, 9, 2, 9, 0, 0, tzinfo=timezone.utc),
                category="family",
                source="manual"
            ),
            Event(
                title="Evening Event",
                start_utc=datetime(2025, 9, 2, 18, 0, 0, tzinfo=timezone.utc),
                end_utc=datetime(2025, 9, 2, 19, 0, 0, tzinfo=timezone.utc),
                category="family",
                source="manual"
            )
        ]
        
        for event in events:
            db_session.add(event)
        db_session.commit()
        
        # Get events for Sept 2
        day = datetime(2025, 9, 2, 12, 0, 0, tzinfo=timezone.utc)
        
        daily_instances = EventExpansionService.get_daily_events(
            db_session, day
        )
        
        # Should have both events
        assert len(daily_instances) == 2
        
        # Check that all instances are on the same day
        for instance in daily_instances:
            assert instance["start_utc"].date() == day.date()
    
    def test_validate_event_expansion(self, db_session):
        """Test event expansion validation"""
        # Valid single event
        event = Event(
            title="Valid Event",
            start_utc=datetime(2025, 9, 2, 8, 0, 0, tzinfo=timezone.utc),
            end_utc=datetime(2025, 9, 2, 9, 0, 0, tzinfo=timezone.utc),
            category="family",
            source="manual"
        )
        
        is_valid, error = EventExpansionService.validate_event_expansion(event)
        assert is_valid is True
        assert error == ""
        
        # Valid recurring event
        event.rrule = "FREQ=WEEKLY;BYDAY=TU"
        is_valid, error = EventExpansionService.validate_event_expansion(event)
        assert is_valid is True
        assert error == ""
        
        # Invalid RRULE
        event.rrule = "INVALID=RULE"
        is_valid, error = EventExpansionService.validate_event_expansion(event)
        assert is_valid is False
        assert "Invalid RRULE" in error
        
        # Invalid exdate
        event.rrule = "FREQ=WEEKLY;BYDAY=TU"
        event.exdates = ["invalid-date"]
        is_valid, error = EventExpansionService.validate_event_expansion(event)
        assert is_valid is False
        assert "Invalid exdate format" in error
