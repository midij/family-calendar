# 🚀 Family Calendar Implementation Plan

## Overview
This document breaks down the family calendar MVP into sequential, testable tasks. Each task builds upon the previous ones, ensuring a working end-to-end system when all tasks are completed.

---

## Task 1: Project Setup & Infrastructure
**Status**: completed  
**Order**: 1  
**Goal**: Establish the basic project structure and development environment

**Implementation**:
- Create project directory structure
- Set up Docker and docker-compose files
- Initialize Python virtual environment
- Create requirements.txt with dependencies
- Set up PostgreSQL and Redis containers
- Create basic project configuration

**Test Plan**:
- Verify Docker containers start successfully
- Confirm database connections work
- Validate Python environment setup
- Test basic project structure

---

## Task 2: Database Schema & Models
**Status**: completed  
**Order**: 2  
**Goal**: Implement the core data models and database schema

**Implementation**:
- Create SQLAlchemy models for Kid and Event
- Implement database migrations
- Set up database indexes (startUtc, endUtc, GIN kidIds)
- Create database connection and session management
- Implement basic CRUD operations for models

**Test Plan**:
- Verify database tables are created correctly
- Test model validation with Pydantic
- Confirm indexes are properly created
- Test basic CRUD operations
- Validate data constraints and relationships

---

## Task 3: Core API Endpoints
**Status**: completed  
**Order**: 3  
**Goal**: Implement the basic REST API endpoints for events and kids

**Implementation**:
- Create FastAPI application structure
- Implement GET /v1/kids endpoint
- Implement POST /v1/kids endpoint
- Implement GET /v1/events endpoint with query parameters
- Implement POST /v1/events endpoint
- Add basic error handling and validation

**Test Plan**:
- Test API endpoints with sample data
- Verify proper HTTP status codes
- Test input validation and error handling
- Confirm database operations work correctly
- Test query parameters and filtering

---

## Task 4: RRULE & Event Expansion
**Status**: completed  
**Order**: 4  
**Goal**: Implement recurring event logic and event expansion

**Implementation**:
- ✅ Integrate python-dateutil for RRULE parsing
- ✅ Implement RRULE expansion logic (DAILY/WEEKLY/MONTHLY)
- ✅ Handle EXDATE exceptions
- ✅ Create event instance generation from recurring rules
- ✅ Implement timezone handling (UTC storage, local display)
- ✅ Create EventExpansionService for database integration
- ✅ Add API endpoints for expanded events (/expanded/, /weekly/, /daily/)
- ✅ Implement comprehensive error handling and validation

**Test Plan**:
- ✅ Test various RRULE patterns (daily, weekly, monthly)
- ✅ Verify EXDATE exceptions work correctly
- ✅ Test timezone conversions
- ✅ Validate event expansion performance
- ✅ Test edge cases (past dates, complex rules)
- ✅ 22 RRULE service tests passing
- ✅ 10 event expansion service tests passing
- ✅ API integration tests passing

---

## Task 5: Event Management API
**Status**: completed  
**Order**: 5  
**Goal**: Complete the full event management API

**Implementation**:
- ✅ Implement PATCH /v1/events/{id} endpoint
- ✅ Implement DELETE /v1/events/{id} endpoint
- ✅ Add idempotency support with Idempotency-Key header
- ✅ Implement event update logic
- ✅ Add proper error handling for all operations

**Test Plan**:
- ✅ Test event updates with various scenarios
- ✅ Verify event deletion works correctly
- ✅ Test idempotency functionality
- ✅ Validate error handling for invalid operations
- ✅ Test concurrent operations

---

## Task 6: Import Functionality
**Status**: completed  
**Order**: 6  
**Goal**: Implement CSV and ICS file import capabilities

**Implementation**:
- ✅ Create POST /v1/import/csv endpoint
- ✅ Implement CSV parsing with proper validation
- ✅ Create POST /v1/import/ics endpoint
- ✅ Implement ICS file parsing (VEVENT handling)
- ✅ Add file upload handling and validation
- ✅ Implement import error handling and reporting

**Test Plan**:
- ✅ Test CSV import with various formats
- ✅ Verify ICS import with different calendar files
- ✅ Test error handling for malformed files
- ✅ Validate imported data accuracy
- ✅ Test large file handling

---

## Task 7: Real-time Updates (Database Timestamp Polling)
**Status**: completed  
**Order**: 7  
**Goal**: Implement database timestamp-based polling for real-time updates

**Implementation**:
- ✅ Create GET /v1/events/version endpoint that returns latest updated_at timestamp
- ✅ Use existing database updated_at field from BaseModel (no additional tables needed)
- ✅ Implement lightweight version checking using MAX(updated_at) query
- ✅ Add proper error handling for version endpoint
- ✅ Document polling mechanism for frontend implementation
- ✅ Remove SSE-related code from create/update/delete endpoints
- ✅ Fix BaseModel to set updated_at on creation (not just updates)

**Test Plan**:
- ✅ Test version endpoint returns correct timestamp
- ✅ Verify timestamp updates when events are created/modified/deleted
- ✅ Test version endpoint performance with multiple events
- ✅ Validate timestamp format and timezone handling
- ✅ Test error handling when no events exist
- ✅ Verify endpoint works with existing database schema
- ✅ 7 comprehensive tests passing

---

## Task 8: Frontend Wall Display
**Status**: completed  
**Order**: 8  
**Goal**: Create the wall-mounted calendar display interface

**Implementation**:
- ✅ Create wall.html with responsive grid layout
- ✅ Implement weekly view (Mon-Sun columns)
- ✅ Add time axis (08:00-22:00 with auto-expansion)
- ✅ Implement child track rows with color coding
- ✅ Add navigation buttons (today, last week, next week)
- ✅ Implement responsive font sizing with clamp()
- ✅ Add event card rendering and positioning
- ✅ Integrate real-time updates via version endpoint polling
- ✅ Add comprehensive testing and documentation

**Test Plan**:
- ✅ Verify responsive design works on different screen sizes
- ✅ Test weekly navigation functionality
- ✅ Validate time axis expansion logic
- ✅ Confirm child track colors are distinct
- ✅ Test event rendering and positioning
- ✅ Verify font sizes are readable from 2-3 meters
- ✅ Test real-time update mechanism
- ✅ Validate API connectivity and error handling

---

## Task 9: Event Rendering & Layout
**Status**: not-started  
**Order**: 9  
**Goal**: Implement sophisticated event rendering and layout management

**Implementation**:
- Handle overlapping events (side-by-side or layered)
- Implement event time slot positioning
- Add event card styling and information display
- Handle events outside default time range (06:00-24:00)
- Implement event click interactions
- Add loading states and error handling

**Test Plan**:
- Test overlapping event handling
- Verify event positioning accuracy
- Test time range expansion logic
- Validate event card information display
- Test responsive layout on different devices
- Verify performance with many events (≤1s render time)

---

## Task 10: Real-time Frontend Integration
**Status**: not-started  
**Order**: 10  
**Goal**: Connect frontend to real-time backend updates

**Implementation**:
- Integrate SSE client in frontend
- Implement automatic refresh logic
- Add offline detection and cache display
- Show "last updated" timestamp
- Implement fallback polling when SSE fails
- Add connection status indicators

**Test Plan**:
- Test real-time updates from backend
- Verify offline behavior and cache display
- Test SSE fallback to polling
- Validate update frequency compliance
- Test network interruption scenarios
- Verify connection status indicators

---

## Task 11: Data Seeding & Sample Data
**Status**: not-started  
**Order**: 11  
**Goal**: Create sample data and seeding functionality for testing

**Implementation**:
- Create sample kid data (小明, 小红)
- Create sample recurring events (piano lessons, etc.)
- Implement database seeding script
- Add sample data validation
- Create test data cleanup functionality

**Test Plan**:
- Verify sample data is created correctly
- Test seeding script functionality
- Validate sample data relationships
- Test data cleanup operations
- Confirm sample data matches requirements

---

## Task 12: End-to-End Testing & Integration
**Status**: not-started  
**Order**: 12  
**Goal**: Comprehensive testing of the complete system

**Implementation**:
- Create integration test suite
- Test complete user workflows
- Validate performance requirements
- Test cross-browser compatibility
- Verify responsive design on tablets
- Test full-screen wall display mode

**Test Plan**:
- Test complete event creation → display workflow
- Verify performance meets requirements (≤150ms API, ≤1s render)
- Test on iPad Safari and Android Chrome
- Validate wall display readability from 2-3 meters
- Test real-time update performance (≤10s)
- Verify offline functionality and cache behavior

---

## Task 13: Documentation & Deployment
**Status**: not-started  
**Order**: 13  
**Goal**: Prepare the system for production deployment

**Implementation**:
- Create deployment documentation
- Add health check endpoints
- Implement logging and monitoring
- Create user manual for wall display
- Add API documentation
- Prepare production Docker configuration

**Test Plan**:
- Verify deployment process works correctly
- Test health check endpoints
- Validate logging functionality
- Test production configuration
- Verify documentation accuracy

---

## Success Criteria
- All API endpoints return correct responses
- Frontend displays events correctly in weekly view
- Real-time updates work with ≤10s delay
- Performance meets requirements (≤150ms API, ≤1s render)
- Wall display is readable from 2-3 meters
- System handles offline scenarios gracefully
- Cross-browser compatibility verified

## Notes
- Each task should be completed and tested before moving to the next
- Performance testing should be done with realistic data volumes
- UI testing should include actual tablet devices for wall display
- All error scenarios should be tested and handled gracefully 