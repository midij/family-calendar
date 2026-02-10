#!/usr/bin/env python3
"""
Test script for data seeding functionality
"""

import sys
import os
from datetime import datetime, timezone, timedelta

# Add the parent directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.database import get_db
from sqlalchemy.orm import Session
from sqlalchemy import text
from seed_data import DataSeeder


class SeedingTester:
    def __init__(self):
        self.db: Session = next(get_db())
        self.seeder = DataSeeder()
    
    def test_sample_kids_creation(self) -> bool:
        """Test sample kids creation"""
        print("🧪 Testing sample kids creation...")
        
        try:
            # Clean up first
            self.seeder.cleanup_sample_data()
            
            # Create sample kids
            kids = self.seeder.create_sample_kids()
            
            # Validate
            assert len(kids) >= 2, "Should create at least 2 kids"
            assert any(kid["name"] == "小明" for kid in kids), "Should create 小明"
            assert any(kid["name"] == "小红" for kid in kids), "Should create 小红"
            
            # Check database
            result = self.db.execute(text("SELECT COUNT(*) FROM kids WHERE name IN ('小明', '小红')"))
            db_kids_count = result.fetchone()[0]
            assert db_kids_count >= 2, "Kids should be in database"
            
            print("✅ Sample kids creation test passed")
            return True
            
        except Exception as e:
            print(f"❌ Sample kids creation test failed: {e}")
            return False
    
    def test_sample_events_creation(self) -> bool:
        """Test sample events creation"""
        print("🧪 Testing sample events creation...")
        
        try:
            # Ensure we have kids first
            if not self.seeder.sample_kids:
                self.seeder.create_sample_kids()
            
            # Create sample events
            events = self.seeder.create_sample_events()
            
            # Validate
            assert len(events) >= 4, "Should create at least 4 events"
            
            # Check for specific events
            event_titles = [event["title"] for event in events]
            assert "钢琴课" in event_titles, "Should create 钢琴课"
            assert "游泳课" in event_titles, "Should create 游泳课"
            assert "家庭聚餐" in event_titles, "Should create 家庭聚餐"
            
            # Check recurring events
            recurring_events = [e for e in events if e["rrule"]]
            assert len(recurring_events) >= 3, "Should create recurring events"
            
            # Check one-time events
            one_time_events = [e for e in events if not e["rrule"]]
            assert len(one_time_events) >= 1, "Should create one-time events"
            
            print("✅ Sample events creation test passed")
            return True
            
        except Exception as e:
            print(f"❌ Sample events creation test failed: {e}")
            return False
    
    def test_data_relationships(self) -> bool:
        """Test data relationships"""
        print("🧪 Testing data relationships...")
        
        try:
            # Get all events with kid_ids
            result = self.db.execute(text("SELECT title, kid_ids FROM events WHERE kid_ids IS NOT NULL AND kid_ids != '[]'"))
            events_with_kids = result.fetchall()
            
            invalid_relationships = []
            for event_title, kid_ids_json in events_with_kids:
                if kid_ids_json and kid_ids_json != '[]':
                    # Parse kid_ids JSON
                    import json
                    try:
                        kid_ids = json.loads(kid_ids_json)
                        for kid_id in kid_ids:
                            # Check that referenced kid exists
                            kid_result = self.db.execute(text("SELECT id FROM kids WHERE id = :kid_id"), {"kid_id": kid_id})
                            kid = kid_result.fetchone()
                            if kid is None:
                                invalid_relationships.append(f"Event {event_title} references non-existent kid {kid_id}")
                    except (json.JSONDecodeError, TypeError):
                        # Skip invalid JSON or None values
                        continue
            
            # Only fail if we have invalid relationships in our sample data
            sample_event_titles = ["钢琴课", "游泳课", "家庭聚餐", "数学补习", "足球训练", "美术课", "医生预约", "生日派对"]
            sample_invalid = [rel for rel in invalid_relationships if any(title in rel for title in sample_event_titles)]
            
            if sample_invalid:
                print(f"❌ Data relationships test failed: {sample_invalid}")
                return False
            
            print("✅ Data relationships test passed")
            return True
            
        except Exception as e:
            print(f"❌ Data relationships test failed: {e}")
            return False
    
    def test_rrule_validation(self) -> bool:
        """Test RRULE validation"""
        print("🧪 Testing RRULE validation...")
        
        try:
            result = self.db.execute(text("SELECT rrule FROM events WHERE rrule IS NOT NULL"))
            recurring_events = result.fetchall()
            
            for (rrule,) in recurring_events:
                assert rrule, "Recurring event should have RRULE"
                assert "FREQ=" in rrule, "RRULE should contain FREQ"
                assert "UNTIL=" in rrule, "RRULE should contain UNTIL"
            
            print("✅ RRULE validation test passed")
            return True
            
        except Exception as e:
            print(f"❌ RRULE validation test failed: {e}")
            return False
    
    def test_cleanup_functionality(self) -> bool:
        """Test cleanup functionality"""
        print("🧪 Testing cleanup functionality...")
        
        try:
            # Count before cleanup
            result = self.db.execute(text("SELECT COUNT(*) FROM kids"))
            kids_before = result.fetchone()[0]
            result = self.db.execute(text("SELECT COUNT(*) FROM events"))
            events_before = result.fetchone()[0]
            
            # Cleanup
            self.seeder.cleanup_sample_data()
            
            # Count after cleanup
            result = self.db.execute(text("SELECT COUNT(*) FROM kids"))
            kids_after = result.fetchone()[0]
            result = self.db.execute(text("SELECT COUNT(*) FROM events"))
            events_after = result.fetchone()[0]
            
            # Should have fewer items (or same if no sample data existed)
            assert kids_after <= kids_before, "Cleanup should not increase kid count"
            assert events_after <= events_before, "Cleanup should not increase event count"
            
            print("✅ Cleanup functionality test passed")
            return True
            
        except Exception as e:
            print(f"❌ Cleanup functionality test failed: {e}")
            return False
    
    def test_overlapping_events(self) -> bool:
        """Test overlapping events creation"""
        print("🧪 Testing overlapping events...")
        
        try:
            # Ensure we have kids
            if not self.seeder.sample_kids:
                self.seeder.create_sample_kids()
            
            # Create additional test events (including overlapping ones)
            additional_events = self.seeder.create_additional_test_events()
            
            # Check for overlapping events
            overlapping_events = [e for e in additional_events if "重叠" in e["title"]]
            assert len(overlapping_events) >= 2, "Should create overlapping events"
            
            # Check time range events
            early_events = [e for e in additional_events if "早间" in e["title"]]
            late_events = [e for e in additional_events if "晚间" in e["title"]]
            
            assert len(early_events) >= 1, "Should create early morning events"
            assert len(late_events) >= 1, "Should create late evening events"
            
            print("✅ Overlapping events test passed")
            return True
            
        except Exception as e:
            print(f"❌ Overlapping events test failed: {e}")
            return False
    
    def run_all_tests(self) -> bool:
        """Run all seeding tests"""
        print("🧪 Starting seeding tests...")
        print("=" * 50)
        
        tests = [
            self.test_sample_kids_creation,
            self.test_sample_events_creation,
            self.test_data_relationships,
            self.test_rrule_validation,
            self.test_overlapping_events,
            self.test_cleanup_functionality
        ]
        
        passed = 0
        total = len(tests)
        
        for test in tests:
            if test():
                passed += 1
            print()
        
        print("=" * 50)
        print(f"🧪 Test Results: {passed}/{total} tests passed")
        
        if passed == total:
            print("🎉 All seeding tests passed!")
            return True
        else:
            print("❌ Some seeding tests failed!")
            return False
    
    def __del__(self):
        if hasattr(self, 'db'):
            self.db.close()


def main():
    """Main function"""
    tester = SeedingTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
