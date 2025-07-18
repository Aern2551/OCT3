from fastapi import FastAPI, HTTPException, Depends, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from typing import List, Optional
from passlib.context import CryptContext
import jwt
import uvicorn
import os
from datetime import datetime, timedelta
from uuid import uuid4
import shutil

# Secret key for JWT
SECRET_KEY = "your_secret_key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

app = FastAPI()

# CORS middleware to allow frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# In-memory "database" for demo purposes
users_db = {
    "doctor": {
        "username": "doctor",
        "hashed_password": pwd_context.hash("password123"),
    }
}

patients_db = {}
analyses_db = {}
notifications_db = {}

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Pydantic models
class User(BaseModel):
    username: str

class Patient(BaseModel):
    patient_id: str
    scan_date: datetime
    eye: str

class AnalysisResult(BaseModel):
    patient_id: str
    diagnosis: str
    confidence: float
    details: Optional[str] = None

class Notification(BaseModel):
    id: str
    message: str
    timestamp: datetime

# Utility functions
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def authenticate_user(username: str, password: str):
    user = users_db.get(username)
    if not user:
        return False
    if not verify_password(password, user["hashed_password"]):
        return False
    return User(username=username)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except jwt.PyJWTError:
        raise credentials_exception
    user = users_db.get(username)
    if user is None:
        raise credentials_exception
    return User(username=username)

# Routes
@app.post("/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/patients/", response_model=Patient)
async def create_patient(patient_id: str = Form(...), scan_date: str = Form(...), eye: str = Form(...), current_user: User = Depends(get_current_user)):
    if patient_id in patients_db:
        raise HTTPException(status_code=400, detail="Patient already exists")
    try:
        scan_date_dt = datetime.fromisoformat(scan_date)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid scan_date format")
    patient = Patient(patient_id=patient_id, scan_date=scan_date_dt, eye=eye)
    patients_db[patient_id] = patient
    return patient

@app.get("/patients/{patient_id}", response_model=Patient)
async def get_patient(patient_id: str, current_user: User = Depends(get_current_user)):
    patient = patients_db.get(patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    return patient

@app.post("/upload/")
async def upload_files(patient_id: str = Form(...), files: List[UploadFile] = File(...), current_user: User = Depends(get_current_user)):
    if patient_id not in patients_db:
        raise HTTPException(status_code=404, detail="Patient not found")
    saved_files = []
    patient_folder = os.path.join(UPLOAD_DIR, patient_id)
    os.makedirs(patient_folder, exist_ok=True)
    for file in files:
        filename = f"{uuid4().hex}_{file.filename}"
        file_path = os.path.join(patient_folder, filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        saved_files.append(filename)
    return {"filenames": saved_files}

@app.post("/analysis/", response_model=AnalysisResult)
async def submit_analysis(patient_id: str = Form(...), diagnosis: str = Form(...), confidence: float = Form(...), details: Optional[str] = Form(None), current_user: User = Depends(get_current_user)):
    if patient_id not in patients_db:
        raise HTTPException(status_code=404, detail="Patient not found")
    analysis = AnalysisResult(patient_id=patient_id, diagnosis=diagnosis, confidence=confidence, details=details)
    analyses_db[patient_id] = analysis
    return analysis

@app.get("/analysis/{patient_id}", response_model=AnalysisResult)
async def get_analysis(patient_id: str, current_user: User = Depends(get_current_user)):
    analysis = analyses_db.get(patient_id)
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")
    return analysis

@app.get("/history/", response_model=List[Patient])
async def search_history(patient_id: Optional[str] = None, diagnosis: Optional[str] = None, current_user: User = Depends(get_current_user)):
    results = []
    for pid, patient in patients_db.items():
        if patient_id and patient_id.lower() not in pid.lower():
            continue
        if diagnosis:
            analysis = analyses_db.get(pid)
            if not analysis or diagnosis.lower() not in analysis.diagnosis.lower():
                continue
        results.append(patient)
    return results

@app.get("/notifications/", response_model=List[Notification])
async def get_notifications(current_user: User = Depends(get_current_user)):
    return list(notifications_db.values())

@app.post("/notifications/")
async def create_notification(message: str = Form(...), current_user: User = Depends(get_current_user)):
    notif_id = uuid4().hex
    notification = Notification(id=notif_id, message=message, timestamp=datetime.utcnow())
    notifications_db[notif_id] = notification
    return notification

@app.get("/reports/{patient_id}")
async def download_report(patient_id: str, current_user: User = Depends(get_current_user)):
    # For demo, generate a simple PDF report on the fly
    from fastapi.responses import StreamingResponse
    from io import BytesIO
    from reportlab.pdfgen import canvas

    if patient_id not in patients_db:
        raise HTTPException(status_code=404, detail="Patient not found")

    buffer = BytesIO()
    p = canvas.Canvas(buffer)
    p.drawString(100, 750, f"RetinaView AI Report for Patient {patient_id}")
    analysis = analyses_db.get(patient_id)
    if analysis:
        p.drawString(100, 720, f"Diagnosis: {analysis.diagnosis}")
        p.drawString(100, 700, f"Confidence: {analysis.confidence}%")
        if analysis.details:
            p.drawString(100, 680, f"Details: {analysis.details}")
    else:
        p.drawString(100, 720, "No analysis available.")
    p.showPage()
    p.save()
    buffer.seek(0)
    return StreamingResponse(buffer, media_type="application/pdf", headers={"Content-Disposition": f"attachment; filename=report_{patient_id}.pdf"})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
