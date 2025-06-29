# Worker Tracking System

A simple web application built with Flask that allows you to track workers and their service jobs. Workers can log when they arrive at a location and when they finish their work.

## Features

- **Worker Management**: Add and manage workers with contact information
- **Job Creation**: Create service jobs and assign them to workers
- **Status Tracking**: Track job progress through three states:
  - **Assigned**: Job created and assigned to worker
  - **Arrived**: Worker has reached the location
  - **Completed**: Work has been finished
- **Worker Dashboard**: Individual dashboard for each worker showing their jobs
- **Activity Logging**: Complete log of all status changes with timestamps and notes
- **Modern UI**: Clean, responsive interface using Bootstrap

## Installation

1. Install the required dependencies:
```bash
pip install -r requirements.txt
```

2. Run the application:
```bash
python app.py
```

3. Open your web browser and go to: `http://localhost:5000`

## Usage

### Getting Started

1. **Add Workers**: First, add workers who will be performing the service jobs
   - Go to "Workers" → "Add Worker"
   - Fill in name, email, and optional phone number

2. **Create Service Jobs**: Create jobs and assign them to workers
   - Go to "New Job" or click the "+" button
   - Fill in job title, description, location, and select a worker

3. **Track Progress**: Workers can log their progress on assigned jobs
   - Click on any job to view details
   - Use the action buttons to log arrival and completion

### Worker Workflow

The typical workflow for a worker is:

1. **View Assignment**: Worker sees their assigned job in their dashboard
2. **Travel to Location**: Worker goes to the service location
3. **Log Arrival**: Worker clicks "Log Arrival" when they reach the location
4. **Perform Work**: Worker completes the assigned work
5. **Log Completion**: Worker clicks "Mark as Completed" when finished

### Features Overview

- **Dashboard**: Overview of all service jobs with status indicators
- **Worker Dashboard**: Individual view for each worker showing their jobs filtered by status
- **Job Details**: Detailed view with action buttons and activity log
- **Status Tracking**: Visual indicators and timestamps for each status change
- **Notes**: Optional notes can be added when logging arrival or completion

## API Endpoints

The application also provides simple API endpoints for integration:

- `GET /api/jobs/<worker_id>`: Get all jobs for a specific worker
- `POST /api/log_status/<job_id>`: Log status change (JSON: `{"status": "arrived|completed", "notes": "optional"}`)

## Database

The application uses SQLite database (`worker_tracking.db`) which will be created automatically when you first run the app.

## Customization

You can customize the application by:

- Modifying the CSS styles in `templates/base.html`
- Adding new fields to the database models in `app.py`
- Extending the functionality with additional routes and templates

## Support

This is a simple demonstration application. For production use, consider adding:

- User authentication and authorization
- More detailed job information (priority, due dates, etc.)
- Email notifications
- Mobile-optimized interface
- Data export capabilities

## Authentication

- Default admin account is created automatically on first run:
  - Username: admin
  - Password: adminpass
- Admin can add worker accounts (username + temporary password) when adding a worker.
- Workers log in with their credentials and see only their assigned jobs.

## Note

- If upgrading from an earlier version of this demo (without authentication), delete the existing `worker_tracking.db` file to rebuild the database schema with the new tables. 