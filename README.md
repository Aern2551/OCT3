# RetinaView AI Backend

This is the backend API for the RetinaView AI OCT Retinal Diagnostic Tool.

## Features

- User authentication with JWT
- Patient data management (create, read)
- File upload for OCT images
- Submit and retrieve analysis results
- Search patient history with filters
- Notifications management
- Generate and download PDF reports

## Technology Stack

- Python 3.8+
- FastAPI
- Uvicorn ASGI server
- In-memory data storage (for demo purposes)
- ReportLab for PDF generation

## Setup Instructions

1. Create and activate a Python virtual environment:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:

```bash
pip install fastapi uvicorn sqlalchemy databases pydantic python-multipart passlib[bcrypt] pyjwt aiofiles jinja2 reportlab
```

3. Run the server:

```bash
uvicorn main:app --reload
```

4. The API will be available at `http://localhost:8000`

## API Endpoints

- `POST /token` - Obtain JWT token (login)
- `POST /patients/` - Create a new patient
- `GET /patients/{patient_id}` - Get patient info
- `POST /upload/` - Upload OCT image files for a patient
- `POST /analysis/` - Submit analysis results
- `GET /analysis/{patient_id}` - Get analysis results
- `GET /history/` - Search patient history
- `GET /notifications/` - Get notifications
- `POST /notifications/` - Create notification
- `GET /reports/{patient_id}` - Download PDF report

## Notes

- This backend uses in-memory storage for demonstration. For production, integrate a persistent database.
- Adjust CORS settings in `main.py` as needed.
- Secure the secret key and sensitive data properly in production.
