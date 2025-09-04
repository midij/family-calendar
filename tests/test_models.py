import pytest
from datetime import datetime, timezone
from app.models.kid import Kid
from app.models.event import Event


class TestModels:
    """Test suite for database models"""
    
    def test_kid_creation(self, db_session):
        """Test creating a kid"""
        kid = Kid(
            name="小明",
            color="#4f46e5",
            avatar="https://example.com/avatar1.jpg"
        )
        db_session.add(kid)
        db_session.commit()
        db_session.refresh(kid)
        
        assert kid.id is not None
        assert kid.name == "小明"
        assert kid.color == "#4f46e5"
        assert kid.avatar == "https://example.com/avatar1.jpg"
        assert kid.created_at is not None
    
    def test_event_creation(self, db_session):
        """Test creating an event"""
        event = Event(
            title="钢琴课",
            location="艺术中心302",
            start_utc=datetime(2025, 9, 2, 8, 0, 0, tzinfo=timezone.utc),
            end_utc=datetime(2025, 9, 2, 9, 0, 0, tzinfo=timezone.utc),
            kid_ids=["1", "2"],
            exdates=["2025-10-01"],
            category="after-school",
            source="manual",
            created_by="admin"
        )
        db_session.add(event)
        db_session.commit()
        db_session.refresh(event)
        
        assert event.id is not None
        assert event.title == "钢琴课"
        assert event.location == "艺术中心302"
        assert event.kid_ids == ["1", "2"]
        assert event.exdates == ["2025-10-01"]
        assert event.category == "after-school"
        assert event.source == "manual"
        assert event.created_by == "admin"
        assert event.created_at is not None
    
    def test_event_json_fields(self, db_session):
        """Test that JSON fields work correctly"""
        event = Event(
            title="Test Event",
            start_utc=datetime(2025, 9, 2, 8, 0, 0, tzinfo=timezone.utc),
            end_utc=datetime(2025, 9, 2, 9, 0, 0, tzinfo=timezone.utc),
            kid_ids=["1", "2", "3"],
            exdates=["2025-10-01", "2025-11-01"],
            category="family",
            source="manual"
        )
        db_session.add(event)
        db_session.commit()
        db_session.refresh(event)
        
        # Test property methods
        assert event.kid_ids_list == ["1", "2", "3"]
        assert event.exdates_list == ["2025-10-01", "2025-11-01"]
        
        # Test that we can retrieve the event
        retrieved_event = db_session.query(Event).filter(Event.id == event.id).first()
        assert retrieved_event is not None
        assert retrieved_event.kid_ids_list == ["1", "2", "3"]
        assert retrieved_event.exdates_list == ["2025-10-01", "2025-11-01"]
    
    def test_event_with_none_json_fields(self, db_session):
        """Test event with None JSON fields"""
        event = Event(
            title="Test Event",
            start_utc=datetime(2025, 9, 2, 8, 0, 0, tzinfo=timezone.utc),
            end_utc=datetime(2025, 9, 2, 9, 0, 0, tzinfo=timezone.utc),
            kid_ids=None,
            exdates=None,
            category="family",
            source="manual"
        )
        db_session.add(event)
        db_session.commit()
        db_session.refresh(event)
        
        assert event.kid_ids_list == []
        assert event.exdates_list == []
    
    def test_kid_ordering(self, db_session):
        """Test that kids can be ordered by name"""
        kid1 = Kid(name="Charlie", color="#ff0000")
        kid2 = Kid(name="Alice", color="#00ff00")
        kid3 = Kid(name="Bob", color="#0000ff")
        
        db_session.add_all([kid1, kid2, kid3])
        db_session.commit()
        
        # Test ordering
        kids = db_session.query(Kid).order_by(Kid.name).all()
        names = [kid.name for kid in kids]
        assert names == ["Alice", "Bob", "Charlie"]
    
    def test_event_ordering(self, db_session):
        """Test that events can be ordered by start time"""
        event1 = Event(
            title="Late Event",
            start_utc=datetime(2025, 9, 2, 10, 0, 0, tzinfo=timezone.utc),
            end_utc=datetime(2025, 9, 2, 11, 0, 0, tzinfo=timezone.utc),
            category="family",
            source="manual"
        )
        event2 = Event(
            title="Early Event",
            start_utc=datetime(2025, 9, 2, 8, 0, 0, tzinfo=timezone.utc),
            end_utc=datetime(2025, 9, 2, 9, 0, 0, tzinfo=timezone.utc),
            category="family",
            source="manual"
        )
        
        db_session.add_all([event1, event2])
        db_session.commit()
        
        # Test ordering
        events = db_session.query(Event).order_by(Event.start_utc).all()
        titles = [event.title for event in events]
        assert titles == ["Early Event", "Late Event"]
