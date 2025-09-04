import pytest
import io
from datetime import datetime, timezone
from fastapi.testclient import TestClient
from app.services.import_service import ImportService


class TestImportAPI:
    """Test suite for import functionality"""
    
    def test_get_csv_template(self, client):
        """Test getting CSV template"""
        response = client.get("/v1/import/templates/csv")
        
        assert response.status_code == 200
        data = response.json()
        assert "template" in data
        assert "description" in data
        assert "required_fields" in data
        assert "optional_fields" in data
        assert "title" in data["required_fields"]
        assert "start_date" in data["required_fields"]
    
    def test_import_csv_basic(self, client):
        """Test basic CSV import functionality"""
        csv_content = """title,start_date,start_time,end_date,end_time,location
Test Event,2025-09-01,08:00,2025-09-01,09:00,Test Location"""
        
        files = {"file": ("test.csv", csv_content, "text/csv")}
        data = {"category": "family", "source": "csv"}
        
        response = client.post("/v1/import/csv", files=files, data=data)
        
        assert response.status_code == 200
        result = response.json()
        assert result["total_rows"] == 1
        assert result["success_count"] == 1
        assert result["error_count"] == 0
        assert len(result["imported_events"]) == 1
        assert result["imported_events"][0]["title"] == "Test Event"
    
    def test_import_csv_with_rrule(self, client):
        """Test CSV import with RRULE"""
        csv_content = """title,start_date,start_time,end_date,end_time,rrule
Weekly Event,2025-09-01,08:00,2025-09-01,09:00,FREQ=WEEKLY;BYDAY=MO;UNTIL=2025-12-31T00:00:00Z"""
        
        files = {"file": ("test.csv", csv_content, "text/csv")}
        data = {"category": "family", "source": "csv"}
        
        response = client.post("/v1/import/csv", files=files, data=data)
        
        assert response.status_code == 200
        result = response.json()
        assert result["success_count"] == 1
        assert result["error_count"] == 0
    
    def test_import_csv_with_kid_ids(self, client):
        """Test CSV import with kid IDs"""
        csv_content = """title,start_date,start_time,kid_ids
Kid Event,2025-09-01,08:00,"1,2,3" """
        
        files = {"file": ("test.csv", csv_content, "text/csv")}
        data = {"category": "family", "source": "csv"}
        
        response = client.post("/v1/import/csv", files=files, data=data)
        
        assert response.status_code == 200
        result = response.json()
        assert result["success_count"] == 1
        assert result["error_count"] == 0
    
    def test_import_csv_missing_required_fields(self, client):
        """Test CSV import with missing required fields"""
        csv_content = """start_date,start_time
2025-09-01,08:00"""
        
        files = {"file": ("test.csv", csv_content, "text/csv")}
        data = {"category": "family", "source": "csv"}
        
        response = client.post("/v1/import/csv", files=files, data=data)
        
        assert response.status_code == 200
        result = response.json()
        assert result["success_count"] == 0
        assert result["error_count"] == 1
        assert "Title is required" in result["errors"][0]
    
    def test_import_csv_invalid_date_format(self, client):
        """Test CSV import with invalid date format"""
        csv_content = """title,start_date,start_time
Test Event,2025/09/01,08:00"""
        
        files = {"file": ("test.csv", csv_content, "text/csv")}
        data = {"category": "family", "source": "csv"}
        
        response = client.post("/v1/import/csv", files=files, data=data)
        
        assert response.status_code == 200
        result = response.json()
        assert result["success_count"] == 0
        assert result["error_count"] == 1
        assert "Invalid date format" in result["errors"][0]
    
    def test_import_csv_invalid_time_format(self, client):
        """Test CSV import with invalid time format"""
        csv_content = """title,start_date,start_time
Test Event,2025-09-01,8:00 AM"""
        
        files = {"file": ("test.csv", csv_content, "text/csv")}
        data = {"category": "family", "source": "csv"}
        
        response = client.post("/v1/import/csv", files=files, data=data)
        
        assert response.status_code == 200
        result = response.json()
        assert result["success_count"] == 0
        assert result["error_count"] == 1
        assert "Invalid time format" in result["errors"][0]
    
    def test_import_csv_invalid_time_range(self, client):
        """Test CSV import with invalid time range"""
        csv_content = """title,start_date,start_time,end_date,end_time
Test Event,2025-09-01,09:00,2025-09-01,08:00"""
        
        files = {"file": ("test.csv", csv_content, "text/csv")}
        data = {"category": "family", "source": "csv"}
        
        response = client.post("/v1/import/csv", files=files, data=data)
        
        assert response.status_code == 200
        result = response.json()
        assert result["success_count"] == 0
        assert result["error_count"] == 1
        assert "Start time must be before end time" in result["errors"][0]
    
    def test_import_csv_invalid_rrule(self, client):
        """Test CSV import with invalid RRULE"""
        csv_content = """title,start_date,start_time,rrule
Test Event,2025-09-01,08:00,INVALID=RULE"""
        
        files = {"file": ("test.csv", csv_content, "text/csv")}
        data = {"category": "family", "source": "csv"}
        
        response = client.post("/v1/import/csv", files=files, data=data)
        
        assert response.status_code == 200
        result = response.json()
        assert result["success_count"] == 0
        assert result["error_count"] == 1
        assert "Invalid RRULE" in result["errors"][0]
    
    def test_import_csv_multiple_rows(self, client):
        """Test CSV import with multiple rows"""
        csv_content = """title,start_date,start_time
Event 1,2025-09-01,08:00
Event 2,2025-09-02,09:00
Event 3,2025-09-03,10:00"""
        
        files = {"file": ("test.csv", csv_content, "text/csv")}
        data = {"category": "family", "source": "csv"}
        
        response = client.post("/v1/import/csv", files=files, data=data)
        
        assert response.status_code == 200
        result = response.json()
        assert result["total_rows"] == 3
        assert result["success_count"] == 3
        assert result["error_count"] == 0
        assert len(result["imported_events"]) == 3
    
    def test_import_csv_mixed_success_error(self, client):
        """Test CSV import with mixed success and error rows"""
        csv_content = """title,start_date,start_time
Valid Event,2025-09-01,08:00
Invalid Event,invalid-date,08:00
Another Valid Event,2025-09-03,10:00"""
        
        files = {"file": ("test.csv", csv_content, "text/csv")}
        data = {"category": "family", "source": "csv"}
        
        response = client.post("/v1/import/csv", files=files, data=data)
        
        assert response.status_code == 200
        result = response.json()
        assert result["total_rows"] == 3
        assert result["success_count"] == 2
        assert result["error_count"] == 1
        assert len(result["imported_events"]) == 2
        assert len(result["errors"]) == 1
    
    def test_import_csv_wrong_file_type(self, client):
        """Test CSV import with wrong file type"""
        files = {"file": ("test.txt", "not a csv", "text/plain")}
        data = {"category": "family", "source": "csv"}
        
        response = client.post("/v1/import/csv", files=files, data=data)
        
        assert response.status_code == 400
        assert "File must be a CSV file" in response.json()["detail"]
    
    def test_import_ics_basic(self, client):
        """Test basic ICS import functionality"""
        ics_content = """BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//Test//Test//EN
BEGIN:VEVENT
UID:test-event-1@example.com
DTSTART:20250901T080000Z
DTEND:20250901T090000Z
SUMMARY:Test ICS Event
LOCATION:Test Location
END:VEVENT
END:VCALENDAR"""
        
        files = {"file": ("test.ics", ics_content, "text/calendar")}
        data = {"category": "family", "source": "ics"}
        
        response = client.post("/v1/import/ics", files=files, data=data)
        
        assert response.status_code == 200
        result = response.json()
        assert result["total_events"] == 1
        assert result["success_count"] == 1
        assert result["error_count"] == 0
        assert len(result["imported_events"]) == 1
        assert result["imported_events"][0]["title"] == "Test ICS Event"
    
    def test_import_ics_with_rrule(self, client):
        """Test ICS import with RRULE"""
        ics_content = """BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//Test//Test//EN
BEGIN:VEVENT
UID:test-event-2@example.com
DTSTART:20250901T080000Z
DTEND:20250901T090000Z
SUMMARY:Weekly ICS Event
RRULE:FREQ=WEEKLY;BYDAY=MO;UNTIL=20251231T000000Z
END:VEVENT
END:VCALENDAR"""
        
        files = {"file": ("test.ics", ics_content, "text/calendar")}
        data = {"category": "family", "source": "ics"}
        
        response = client.post("/v1/import/ics", files=files, data=data)
        
        assert response.status_code == 200
        result = response.json()
        assert result["success_count"] == 1
        assert result["error_count"] == 0
    
    def test_import_ics_with_exdates(self, client):
        """Test ICS import with EXDATE"""
        ics_content = """BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//Test//Test//EN
BEGIN:VEVENT
UID:test-event-3@example.com
DTSTART:20250901T080000Z
DTEND:20250901T090000Z
SUMMARY:Event with Exceptions
RRULE:FREQ=WEEKLY;BYDAY=MO;UNTIL=20251231T000000Z
EXDATE:20250908T080000Z
EXDATE:20250915T080000Z
END:VEVENT
END:VCALENDAR"""
        
        files = {"file": ("test.ics", ics_content, "text/calendar")}
        data = {"category": "family", "source": "ics"}
        
        response = client.post("/v1/import/ics", files=files, data=data)
        
        assert response.status_code == 200
        result = response.json()
        assert result["success_count"] == 1
        assert result["error_count"] == 0
    
    def test_import_ics_with_custom_kid_ids(self, client):
        """Test ICS import with custom kid IDs"""
        ics_content = """BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//Test//Test//EN
BEGIN:VEVENT
UID:test-event-4@example.com
DTSTART:20250901T080000Z
DTEND:20250901T090000Z
SUMMARY:Event with Kid IDs
X-KID-IDS:1,2,3
END:VEVENT
END:VCALENDAR"""
        
        files = {"file": ("test.ics", ics_content, "text/calendar")}
        data = {"category": "family", "source": "ics"}
        
        response = client.post("/v1/import/ics", files=files, data=data)
        
        assert response.status_code == 200
        result = response.json()
        assert result["success_count"] == 1
        assert result["error_count"] == 0
    
    def test_import_ics_multiple_events(self, client):
        """Test ICS import with multiple events"""
        ics_content = """BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//Test//Test//EN
BEGIN:VEVENT
UID:test-event-5@example.com
DTSTART:20250901T080000Z
DTEND:20250901T090000Z
SUMMARY:Event 1
END:VEVENT
BEGIN:VEVENT
UID:test-event-6@example.com
DTSTART:20250902T090000Z
DTEND:20250902T100000Z
SUMMARY:Event 2
END:VEVENT
END:VCALENDAR"""
        
        files = {"file": ("test.ics", ics_content, "text/calendar")}
        data = {"category": "family", "source": "ics"}
        
        response = client.post("/v1/import/ics", files=files, data=data)
        
        assert response.status_code == 200
        result = response.json()
        assert result["total_events"] == 2
        assert result["success_count"] == 2
        assert result["error_count"] == 0
        assert len(result["imported_events"]) == 2
    
    def test_import_ics_invalid_format(self, client):
        """Test ICS import with invalid format"""
        ics_content = """This is not a valid ICS file"""
        
        files = {"file": ("test.ics", ics_content, "text/calendar")}
        data = {"category": "family", "source": "ics"}
        
        response = client.post("/v1/import/ics", files=files, data=data)
        
        assert response.status_code == 200
        result = response.json()
        assert result["success_count"] == 0
        assert result["error_count"] == 1
        assert "ICS parsing error" in result["errors"][0]
    
    def test_import_ics_wrong_file_type(self, client):
        """Test ICS import with wrong file type"""
        files = {"file": ("test.txt", "not an ics file", "text/plain")}
        data = {"category": "family", "source": "ics"}
        
        response = client.post("/v1/import/ics", files=files, data=data)
        
        assert response.status_code == 400
        assert "File must be an ICS file" in response.json()["detail"]
    
    def test_import_csv_with_default_kid_id(self, client):
        """Test CSV import with default kid ID"""
        csv_content = """title,start_date,start_time
Test Event,2025-09-01,08:00"""
        
        files = {"file": ("test.csv", csv_content, "text/csv")}
        data = {"kid_id": "1", "category": "family", "source": "csv"}
        
        response = client.post("/v1/import/csv", files=files, data=data)
        
        assert response.status_code == 200
        result = response.json()
        assert result["success_count"] == 1
        assert result["error_count"] == 0
    
    def test_import_ics_with_default_kid_id(self, client):
        """Test ICS import with default kid ID"""
        ics_content = """BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//Test//Test//EN
BEGIN:VEVENT
UID:test-event-7@example.com
DTSTART:20250901T080000Z
DTEND:20250901T090000Z
SUMMARY:Test Event with Default Kid ID
END:VEVENT
END:VCALENDAR"""
        
        files = {"file": ("test.ics", ics_content, "text/calendar")}
        data = {"kid_id": "1", "category": "family", "source": "ics"}
        
        response = client.post("/v1/import/ics", files=files, data=data)
        
        assert response.status_code == 200
        result = response.json()
        assert result["success_count"] == 1
        assert result["error_count"] == 0


class TestImportService:
    """Test suite for ImportService functionality"""
    
    def test_parse_csv_row_basic(self):
        """Test basic CSV row parsing"""
        row = {
            "title": "Test Event",
            "start_date": "2025-09-01",
            "start_time": "08:00",
            "end_date": "2025-09-01",
            "end_time": "09:00",
            "location": "Test Location"
        }
        
        result = ImportService._parse_csv_row(row, None, "family", "csv")
        
        assert result["title"] == "Test Event"
        assert result["location"] == "Test Location"
        assert result["category"] == "family"
        assert result["source"] == "csv"
        assert result["created_by"] == "import"
    
    def test_parse_csv_row_missing_title(self):
        """Test CSV row parsing with missing title"""
        row = {
            "start_date": "2025-09-01",
            "start_time": "08:00"
        }
        
        with pytest.raises(ValueError, match="Title is required"):
            ImportService._parse_csv_row(row, None, "family", "csv")
    
    def test_parse_csv_row_missing_start_date(self):
        """Test CSV row parsing with missing start date"""
        row = {
            "title": "Test Event",
            "start_time": "08:00"
        }
        
        with pytest.raises(ValueError, match="Start date is required"):
            ImportService._parse_csv_row(row, None, "family", "csv")
    
    def test_parse_csv_row_invalid_date(self):
        """Test CSV row parsing with invalid date"""
        row = {
            "title": "Test Event",
            "start_date": "invalid-date",
            "start_time": "08:00"
        }
        
        with pytest.raises(ValueError, match="Invalid date format"):
            ImportService._parse_csv_row(row, None, "family", "csv")
    
    def test_parse_csv_row_invalid_time(self):
        """Test CSV row parsing with invalid time"""
        row = {
            "title": "Test Event",
            "start_date": "2025-09-01",
            "start_time": "invalid-time"
        }
        
        with pytest.raises(ValueError, match="Invalid time format"):
            ImportService._parse_csv_row(row, None, "family", "csv")
    
    def test_parse_csv_row_invalid_time_range(self):
        """Test CSV row parsing with invalid time range"""
        row = {
            "title": "Test Event",
            "start_date": "2025-09-01",
            "start_time": "09:00",
            "end_date": "2025-09-01",
            "end_time": "08:00"
        }
        
        with pytest.raises(ValueError, match="Start time must be before end time"):
            ImportService._parse_csv_row(row, None, "family", "csv")
    
    def test_parse_csv_row_with_kid_ids(self):
        """Test CSV row parsing with kid IDs"""
        row = {
            "title": "Test Event",
            "start_date": "2025-09-01",
            "start_time": "08:00",
            "kid_ids": "1, 2, 3"
        }
        
        result = ImportService._parse_csv_row(row, None, "family", "csv")
        
        assert result["kid_ids"] == ["1", "2", "3"]
    
    def test_parse_csv_row_with_default_kid_id(self):
        """Test CSV row parsing with default kid ID"""
        row = {
            "title": "Test Event",
            "start_date": "2025-09-01",
            "start_time": "08:00"
        }
        
        result = ImportService._parse_csv_row(row, "1", "family", "csv")
        
        assert result["kid_ids"] == ["1"]
    
    def test_parse_csv_row_with_rrule(self):
        """Test CSV row parsing with RRULE"""
        row = {
            "title": "Test Event",
            "start_date": "2025-09-01",
            "start_time": "08:00",
            "rrule": "FREQ=WEEKLY;BYDAY=MO;UNTIL=2025-12-31T00:00:00Z"
        }
        
        result = ImportService._parse_csv_row(row, None, "family", "csv")
        
        assert result["rrule"] == "FREQ=WEEKLY;BYDAY=MO;UNTIL=2025-12-31T00:00:00Z"
    
    def test_parse_csv_row_with_invalid_rrule(self):
        """Test CSV row parsing with invalid RRULE"""
        row = {
            "title": "Test Event",
            "start_date": "2025-09-01",
            "start_time": "08:00",
            "rrule": "INVALID=RULE"
        }
        
        with pytest.raises(ValueError, match="Invalid RRULE"):
            ImportService._parse_csv_row(row, None, "family", "csv")
