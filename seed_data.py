#!/usr/bin/env python3
"""
Data Seeding Script for Family Calendar
Creates sample data for testing and demonstration purposes
"""

import sys
import os
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any

# Add the app directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from database import get_db
from sqlalchemy.orm import Session
from sqlalchemy import text


class DataSeeder:
    def __init__(self):
        self.db: Session = next(get_db())
        self.sample_kids = []
        self.sample_events = []
    
    def create_sample_kids(self) -> List[Dict]:
        """Create sample kid data"""
        print("Creating sample kids...")
        
        sample_kids_data = [
            {
                "name": "小明",
                "color": "#FF6B6B",  # Red
                "avatar": "https://api.dicebear.com/7.x/avataaars/svg?seed=xiaoming"
            },
            {
                "name": "小红", 
                "color": "#4ECDC4",  # Teal
                "avatar": "https://api.dicebear.com/7.x/avataaars/svg?seed=xiaohong"
            },
            {
                "name": "小华",
                "color": "#45B7D1",  # Blue
                "avatar": "https://api.dicebear.com/7.x/avataaars/svg?seed=xiaohua"
            },
            {
                "name": "小丽",
                "color": "#96CEB4",  # Green
                "avatar": "https://api.dicebear.com/7.x/avataaars/svg?seed=xiaoli"
            }
        ]
        
        created_kids = []
        for kid_data in sample_kids_data:
            # Check if kid already exists
            result = self.db.execute(text("SELECT id FROM kids WHERE name = :name"), {"name": kid_data["name"]})
            existing_kid = result.fetchone()
            
            if existing_kid:
                print(f"  Kid '{kid_data['name']}' already exists, skipping...")
                created_kids.append({"id": existing_kid[0], **kid_data})
                continue
            
            # Insert new kid
            result = self.db.execute(text("""
                INSERT INTO kids (name, color, avatar, created_at, updated_at)
                VALUES (:name, :color, :avatar, :created_at, :updated_at)
                RETURNING id
            """), {
                "name": kid_data["name"],
                "color": kid_data["color"],
                "avatar": kid_data["avatar"],
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc)
            })
            
            kid_id = result.fetchone()[0]
            created_kids.append({"id": kid_id, **kid_data})
            print(f"  Created kid: {kid_data['name']} (ID: {kid_id})")
        
        self.db.commit()
        self.sample_kids = created_kids
        return created_kids
    
    def create_sample_events(self) -> List[Dict]:
        """Create sample recurring events"""
        print("Creating sample events...")
        
        # Get current week start (Monday)
        today = datetime.now(timezone.utc)
        days_since_monday = today.weekday()
        week_start = today - timedelta(days=days_since_monday)
        week_start = week_start.replace(hour=0, minute=0, second=0, microsecond=0)
        
        sample_events_data = [
            {
                "title": "钢琴课",
                "location": "音乐教室",
                "start_utc": week_start + timedelta(days=1, hours=16),  # Tuesday 4 PM
                "end_utc": week_start + timedelta(days=1, hours=17),    # Tuesday 5 PM
                "rrule": "FREQ=WEEKLY;BYDAY=TU;UNTIL=2025-12-31T23:59:59Z",
                "exdates": '["2025-10-01", "2025-12-25"]',
                "kid_ids": f'[{self.sample_kids[0]["id"]}]' if self.sample_kids else '[]',
                "category": "after-school",
                "source": "manual"
            },
            {
                "title": "游泳课",
                "location": "社区游泳池",
                "start_utc": week_start + timedelta(days=3, hours=15),  # Thursday 3 PM
                "end_utc": week_start + timedelta(days=3, hours=16),    # Thursday 4 PM
                "rrule": "FREQ=WEEKLY;BYDAY=TH;UNTIL=2025-12-31T23:59:59Z",
                "exdates": '[]',
                "kid_ids": f'[{self.sample_kids[1]["id"]}]' if len(self.sample_kids) > 1 else '[]',
                "category": "sports",
                "source": "manual"
            },
            {
                "title": "家庭聚餐",
                "location": "家里",
                "start_utc": week_start + timedelta(days=6, hours=18),  # Sunday 6 PM
                "end_utc": week_start + timedelta(days=6, hours=20),    # Sunday 8 PM
                "rrule": "FREQ=WEEKLY;BYDAY=SU;UNTIL=2025-12-31T23:59:59Z",
                "exdates": '[]',
                "kid_ids": f'[{",".join([str(kid["id"]) for kid in self.sample_kids])}]' if self.sample_kids else '[]',
                "category": "family",
                "source": "manual"
            },
            {
                "title": "数学补习",
                "location": "书房",
                "start_utc": week_start + timedelta(days=2, hours=19),  # Wednesday 7 PM
                "end_utc": week_start + timedelta(days=2, hours=20),    # Wednesday 8 PM
                "rrule": "FREQ=WEEKLY;BYDAY=WE;UNTIL=2025-12-31T23:59:59Z",
                "exdates": '[]',
                "kid_ids": f'[{self.sample_kids[0]["id"]}, {self.sample_kids[1]["id"]}]' if len(self.sample_kids) > 1 else '[]',
                "category": "education",
                "source": "manual"
            },
            {
                "title": "足球训练",
                "location": "学校操场",
                "start_utc": week_start + timedelta(days=5, hours=16),  # Saturday 4 PM
                "end_utc": week_start + timedelta(days=5, hours=17, minutes=30),  # Saturday 5:30 PM
                "rrule": "FREQ=WEEKLY;BYDAY=SA;UNTIL=2025-12-31T23:59:59Z",
                "exdates": '[]',
                "kid_ids": f'[{self.sample_kids[2]["id"]}]' if len(self.sample_kids) > 2 else '[]',
                "category": "sports",
                "source": "manual"
            },
            {
                "title": "美术课",
                "location": "艺术教室",
                "start_utc": week_start + timedelta(days=4, hours=14),  # Friday 2 PM
                "end_utc": week_start + timedelta(days=4, hours=15, minutes=30),  # Friday 3:30 PM
                "rrule": "FREQ=WEEKLY;BYDAY=FR;UNTIL=2025-12-31T23:59:59Z",
                "exdates": '[]',
                "kid_ids": f'[{self.sample_kids[3]["id"]}]' if len(self.sample_kids) > 3 else '[]',
                "category": "after-school",
                "source": "manual"
            },
            {
                "title": "医生预约",
                "location": "儿童医院",
                "start_utc": week_start + timedelta(days=0, hours=10),  # Monday 10 AM
                "end_utc": week_start + timedelta(days=0, hours=11),    # Monday 11 AM
                "rrule": None,  # One-time event
                "exdates": '[]',
                "kid_ids": f'[{self.sample_kids[0]["id"]}]' if self.sample_kids else '[]',
                "category": "health",
                "source": "manual"
            },
            {
                "title": "生日派对",
                "location": "家里",
                "start_utc": week_start + timedelta(days=6, hours=14),  # Sunday 2 PM
                "end_utc": week_start + timedelta(days=6, hours=17),    # Sunday 5 PM
                "rrule": None,  # One-time event
                "exdates": '[]',
                "kid_ids": f'[{",".join([str(kid["id"]) for kid in self.sample_kids])}]' if self.sample_kids else '[]',
                "category": "family",
                "source": "manual"
            }
        ]
        
        created_events = []
        for event_data in sample_events_data:
            # Check if similar event already exists
            result = self.db.execute(text("""
                SELECT id FROM events 
                WHERE title = :title AND start_utc = :start_utc
            """), {
                "title": event_data["title"],
                "start_utc": event_data["start_utc"]
            })
            existing_event = result.fetchone()
            
            if existing_event:
                print(f"  Event '{event_data['title']}' already exists, skipping...")
                created_events.append({"id": existing_event[0], **event_data})
                continue
            
            # Insert new event
            result = self.db.execute(text("""
                INSERT INTO events (title, location, start_utc, end_utc, rrule, exdates, kid_ids, category, source, created_at, updated_at)
                VALUES (:title, :location, :start_utc, :end_utc, :rrule, :exdates, :kid_ids, :category, :source, :created_at, :updated_at)
                RETURNING id
            """), {
                "title": event_data["title"],
                "location": event_data["location"],
                "start_utc": event_data["start_utc"],
                "end_utc": event_data["end_utc"],
                "rrule": event_data["rrule"],
                "exdates": event_data["exdates"],
                "kid_ids": event_data["kid_ids"],
                "category": event_data["category"],
                "source": event_data["source"],
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc)
            })
            
            event_id = result.fetchone()[0]
            created_events.append({"id": event_id, **event_data})
            print(f"  Created event: {event_data['title']} (ID: {event_id})")
        
        self.db.commit()
        self.sample_events = created_events
        return created_events
    
    def create_additional_test_events(self) -> List[Dict]:
        """Create additional test events for comprehensive testing"""
        print("Creating additional test events...")
        
        # Get current week start
        today = datetime.now(timezone.utc)
        days_since_monday = today.weekday()
        week_start = today - timedelta(days=days_since_monday)
        week_start = week_start.replace(hour=0, minute=0, second=0, microsecond=0)
        
        additional_events = [
            {
                "title": "重叠事件测试1",
                "location": "测试地点",
                "start_utc": week_start + timedelta(days=1, hours=9),   # Tuesday 9 AM
                "end_utc": week_start + timedelta(days=1, hours=10),   # Tuesday 10 AM
                "rrule": None,
                "exdates": '[]',
                "kid_ids": f'[{self.sample_kids[0]["id"]}]' if self.sample_kids else '[]',
                "category": "test",
                "source": "manual"
            },
            {
                "title": "重叠事件测试2",
                "location": "测试地点",
                "start_utc": week_start + timedelta(days=1, hours=9, minutes=30),  # Tuesday 9:30 AM
                "end_utc": week_start + timedelta(days=1, hours=10, minutes=30),  # Tuesday 10:30 AM
                "rrule": None,
                "exdates": '[]',
                "kid_ids": f'[{self.sample_kids[1]["id"]}]' if len(self.sample_kids) > 1 else '[]',
                "category": "test",
                "source": "manual"
            },
            {
                "title": "早间事件",
                "location": "学校",
                "start_utc": week_start + timedelta(days=1, hours=6),   # Tuesday 6 AM
                "end_utc": week_start + timedelta(days=1, hours=7),     # Tuesday 7 AM
                "rrule": "FREQ=WEEKLY;BYDAY=TU,TH;UNTIL=2025-12-31T23:59:59Z",
                "exdates": '[]',
                "kid_ids": f'[{",".join([str(kid["id"]) for kid in self.sample_kids])}]' if self.sample_kids else '[]',
                "category": "education",
                "source": "manual"
            },
            {
                "title": "晚间事件",
                "location": "家里",
                "start_utc": week_start + timedelta(days=1, hours=22),  # Tuesday 10 PM
                "end_utc": week_start + timedelta(days=1, hours=23),    # Tuesday 11 PM
                "rrule": "FREQ=WEEKLY;BYDAY=TU;UNTIL=2025-12-31T23:59:59Z",
                "exdates": '[]',
                "kid_ids": f'[{",".join([str(kid["id"]) for kid in self.sample_kids])}]' if self.sample_kids else '[]',
                "category": "family",
                "source": "manual"
            }
        ]
        
        created_events = []
        for event_data in additional_events:
            result = self.db.execute(text("""
                SELECT id FROM events 
                WHERE title = :title AND start_utc = :start_utc
            """), {
                "title": event_data["title"],
                "start_utc": event_data["start_utc"]
            })
            existing_event = result.fetchone()
            
            if existing_event:
                print(f"  Event '{event_data['title']}' already exists, skipping...")
                created_events.append({"id": existing_event[0], **event_data})
                continue
            
            result = self.db.execute(text("""
                INSERT INTO events (title, location, start_utc, end_utc, rrule, exdates, kid_ids, category, source, created_at, updated_at)
                VALUES (:title, :location, :start_utc, :end_utc, :rrule, :exdates, :kid_ids, :category, :source, :created_at, :updated_at)
                RETURNING id
            """), {
                "title": event_data["title"],
                "location": event_data["location"],
                "start_utc": event_data["start_utc"],
                "end_utc": event_data["end_utc"],
                "rrule": event_data["rrule"],
                "exdates": event_data["exdates"],
                "kid_ids": event_data["kid_ids"],
                "category": event_data["category"],
                "source": event_data["source"],
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc)
            })
            
            event_id = result.fetchone()[0]
            created_events.append({"id": event_id, **event_data})
            print(f"  Created event: {event_data['title']} (ID: {event_id})")
        
        self.db.commit()
        return created_events
    
    def validate_sample_data(self) -> bool:
        """Validate that sample data was created correctly"""
        print("Validating sample data...")
        
        # Check kids
        result = self.db.execute(text("SELECT COUNT(*) FROM kids"))
        kids_count = result.fetchone()[0]
        print(f"  Total kids in database: {kids_count}")
        
        # Check events
        result = self.db.execute(text("SELECT COUNT(*) FROM events"))
        events_count = result.fetchone()[0]
        print(f"  Total events in database: {events_count}")
        
        # Check recurring events
        result = self.db.execute(text("SELECT COUNT(*) FROM events WHERE rrule IS NOT NULL"))
        recurring_events = result.fetchone()[0]
        print(f"  Recurring events: {recurring_events}")
        
        # Check one-time events
        result = self.db.execute(text("SELECT COUNT(*) FROM events WHERE rrule IS NULL"))
        one_time_events = result.fetchone()[0]
        print(f"  One-time events: {one_time_events}")
        
        # Check categories
        result = self.db.execute(text("SELECT DISTINCT category FROM events"))
        categories = [row[0] for row in result.fetchall()]
        print(f"  Event categories: {categories}")
        
        return kids_count > 0 and events_count > 0
    
    def cleanup_sample_data(self) -> None:
        """Clean up sample data (for testing purposes)"""
        print("Cleaning up sample data...")
        
        # Delete sample events
        sample_titles = [
            "钢琴课", "游泳课", "家庭聚餐", "数学补习", "足球训练", "美术课",
            "医生预约", "生日派对", "重叠事件测试1", "重叠事件测试2",
            "早间事件", "晚间事件"
        ]
        
        deleted_events = 0
        for title in sample_titles:
            result = self.db.execute(text("DELETE FROM events WHERE title = :title"), {"title": title})
            deleted_events += result.rowcount
        
        # Delete sample kids
        sample_names = ["小明", "小红", "小华", "小丽"]
        deleted_kids = 0
        for name in sample_names:
            result = self.db.execute(text("DELETE FROM kids WHERE name = :name"), {"name": name})
            deleted_kids += result.rowcount
        
        self.db.commit()
        print(f"  Deleted {deleted_events} events and {deleted_kids} kids")
    
    def seed_all(self) -> None:
        """Seed all sample data"""
        print("🌱 Starting data seeding...")
        print("=" * 50)
        
        try:
            # Create sample kids
            self.create_sample_kids()
            print()
            
            # Create sample events
            self.create_sample_events()
            print()
            
            # Create additional test events
            self.create_additional_test_events()
            print()
            
            # Validate data
            if self.validate_sample_data():
                print("✅ Sample data created successfully!")
            else:
                print("❌ Sample data validation failed!")
                return
            
            print("=" * 50)
            print("🎉 Data seeding completed!")
            print(f"Created {len(self.sample_kids)} kids and {len(self.sample_events)} events")
            
        except Exception as e:
            print(f"❌ Error during seeding: {e}")
            self.db.rollback()
            raise
        finally:
            self.db.close()


def main():
    """Main function for command line usage"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Family Calendar Data Seeder')
    parser.add_argument('--cleanup', action='store_true', help='Clean up sample data')
    parser.add_argument('--validate', action='store_true', help='Validate existing data')
    parser.add_argument('--kids-only', action='store_true', help='Create only sample kids')
    parser.add_argument('--events-only', action='store_true', help='Create only sample events')
    
    args = parser.parse_args()
    
    seeder = DataSeeder()
    
    if args.cleanup:
        seeder.cleanup_sample_data()
    elif args.validate:
        seeder.validate_sample_data()
    elif args.kids_only:
        seeder.create_sample_kids()
    elif args.events_only:
        seeder.create_sample_events()
    else:
        seeder.seed_all()


if __name__ == "__main__":
    main()
