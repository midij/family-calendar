"""
Version tracking service for real-time updates.
Tracks data changes and provides version numbers for SSE clients.
"""
import time
import hashlib
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from app.models.event import Event
from app.models.kid import Kid


class VersionService:
    """Service for tracking data versions and changes"""
    
    _current_version: Optional[str] = None
    _last_updated: Optional[datetime] = None
    
    @classmethod
    def get_current_version(cls) -> str:
        """Get the current data version"""
        if cls._current_version is None:
            cls._current_version = cls._generate_version()
        return cls._current_version
    
    @classmethod
    def update_version(cls, db: Session) -> str:
        """Update the version based on current data state"""
        cls._current_version = cls._generate_version_from_db(db)
        cls._last_updated = datetime.now(timezone.utc)
        return cls._current_version
    
    @classmethod
    def get_last_updated(cls) -> Optional[datetime]:
        """Get the last update timestamp"""
        return cls._last_updated
    
    @classmethod
    def _generate_version(cls) -> str:
        """Generate a version string based on current timestamp"""
        timestamp = int(time.time() * 1000)  # milliseconds
        return f"v{timestamp}"
    
    @classmethod
    def _generate_version_from_db(cls, db: Session) -> str:
        """Generate a version string based on database state"""
        # Get the latest updated_at timestamp from events and kids
        latest_event = db.query(Event).order_by(Event.updated_at.desc()).first()
        latest_kid = db.query(Kid).order_by(Kid.updated_at.desc()).first()
        
        # Use the most recent timestamp, handling None values
        timestamps = []
        if latest_event and latest_event.updated_at:
            timestamps.append(latest_event.updated_at)
        if latest_kid and latest_kid.updated_at:
            timestamps.append(latest_kid.updated_at)
        
        if timestamps:
            latest_timestamp = max(timestamps)
        else:
            # No data, use current time
            latest_timestamp = datetime.now(timezone.utc)
        
        # Create a hash-based version using the timestamp rounded to seconds
        # This ensures consistency for the same data state
        timestamp_str = latest_timestamp.replace(microsecond=0).isoformat()
        version_hash = hashlib.md5(timestamp_str.encode()).hexdigest()[:8]
        return f"v{version_hash}"
    
    @classmethod
    def get_version_info(cls) -> Dict[str, Any]:
        """Get version information for SSE clients"""
        return {
            "version": cls.get_current_version(),
            "last_updated": cls.get_last_updated().isoformat() if cls._last_updated else None,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
