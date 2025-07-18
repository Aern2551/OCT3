import streamlit as st
import pandas as pd
import os
import shutil
from datetime import datetime, timedelta
from uuid import uuid4
from typing import List, Optional
import hashlib
import json
from io import BytesIO
import base64

# Custom CSS from the original app.py
custom_css = """
<style>
.upload-area {
    border: 2px dashed #d1d5db;
    transition: all 0.3s ease;
}

.upload-area:hover {
    border-color: #3EB489;
    background-color: #f0fdf4;
}

.login-container {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    padding: 2rem;
    border-radius: 12px;
    max-width: 400px;
    margin: auto;
    color: white;
}

.main-container {
    background: #f8fafc;
    padding: 1rem;
    border-radius: 8px;
    margin: 1rem 0;
}

.patient-card {
    background: white;
    padding: 1.5rem;
    border-radius: 8px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    margin: 1rem 0;
}

.analysis-result {
    background: #f0fdf4;
    border: 1px solid #3EB489;
    padding: 1rem;
    border-radius: 8px;
    margin: 1rem 0;
}

.notification {
    background: #fff3cd;
    border: 1px solid #ffeaa7;
    padding: 1rem;
    border-radius: 8px;
    margin: 0.5rem 0;
}

input[type="text"], input[type="password"] {
    width: 100%;
    padding: 12px 15px;
    margin: 8px 0 16px 0;
    border: 1px solid #ccc;
    border-radius: 8px;
    box-sizing: border-box;
    outline: none;
    transition: border-color 0.3s ease;
}

input[type="text"]:focus, input[type="password"]:focus {
    border-color: #3EB489;
    box-shadow: 0 0 5px #3EB489;
}

button {
    background-color: #3EB489;
    color: white;
    padding: 12px;
    border: none;
    border-radius: 8px;
    cursor: pointer;
    font-weight: bold;
    width: 100%;
    transition: background-color 0.3s ease;
}

button:hover {
    background-color: #2e8b6f;
}
</style>
"""

# Data storage directories
UPLOAD_DIR = "uploads"
DATA_DIR = "data"
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(DATA_DIR, exist_ok=True)

# Data models and storage
class DataManager:
    def __init__(self):
        self.users_file = os.path.join(DATA_DIR, "users.json")
        self.patients_file = os.path.join(DATA_DIR, "patients.json")
        self.analyses_file = os.path.join(DATA_DIR, "analyses.json")
        self.notifications_file = os.path.join(DATA_DIR, "notifications.json")
        
        self.users_db = self.load_data(self.users_file, {
            "doctor": {
                "username": "doctor",
                "hashed_password": self.hash_password("password123")
            }
        })
        self.patients_db = self.load_data(self.patients_file, {})
        self.analyses_db = self.load_data(self.analyses_file, {})
        self.notifications_db = self.load_data(self.notifications_file, {})

    def load_data(self, file_path, default_data):
        try:
            if os.path.exists(file_path):
                with open(file_path, 'r') as f:
                    return json.load(f)
            return default_data
        except:
            return default_data

    def save_data(self, file_path, data):
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2, default=str)

    def hash_password(self, password):
        return hashlib.sha256(password.encode()).hexdigest()

    def verify_password(self, password, hashed_password):
        return self.hash_password(password) == hashed_password

    def authenticate_user(self, username, password):
        user = self.users_db.get(username)
        if not user:
            return False
        return self.verify_password(password, user["hashed_password"])

    def create_patient(self, patient_id, scan_date, eye):
        if patient_id in self.patients_db:
            return False
        patient = {
            "patient_id": patient_id,
            "scan_date": scan_date,
            "eye": eye,
            "created_at": datetime.now().isoformat()
        }
        self.patients_db[patient_id] = patient
        self.save_data(self.patients_file, self.patients_db)
        return True

    def get_patient(self, patient_id):
        return self.patients_db.get(patient_id)

    def save_analysis(self, patient_id, diagnosis, confidence, details=None):
        analysis = {
            "patient_id": patient_id,
            "diagnosis": diagnosis,
            "confidence": confidence,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        self.analyses_db[patient_id] = analysis
        self.save_data(self.analyses_file, self.analyses_db)
        return analysis

    def get_analysis(self, patient_id):
        return self.analyses_db.get(patient_id)

    def search_patients(self, patient_id_filter=None, diagnosis_filter=None):
        results = []
        for pid, patient in self.patients_db.items():
            if patient_id_filter and patient_id_filter.lower() not in pid.lower():
                continue
            if diagnosis_filter:
                analysis = self.analyses_db.get(pid)
                if not analysis or diagnosis_filter.lower() not in analysis.get("diagnosis", "").lower():
                    continue
            results.append(patient)
        return results

    def add_notification(self, message):
        notif_id = uuid4().hex
        notification = {
            "id": notif_id,
            "message": message,
            "timestamp": datetime.now().isoformat()
        }
        self.notifications_db[notif_id] = notification
        self.save_data(self.notifications_file, self.notifications_db)
        return notification

    def get_notifications(self):
        return list(self.notifications_db.values())

# Initialize data manager
@st.cache_resource
def get_data_manager():
    return DataManager()

def login_form():
    st.markdown(custom_css, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown('<div class="login-container">', unsafe_allow_html=True)
        st.markdown("<h2 style='text-align: center; margin-bottom: 2rem;'>RetinaView AI</h2>", unsafe_allow_html=True)
        
        with st.form("login_form"):
            username = st.text_input("Username", placeholder="Enter your username")
            password = st.text_input("Password", type="password", placeholder="Enter your password")
            submitted = st.form_submit_button("Sign In")
            
            if submitted:
                dm = get_data_manager()
                if dm.authenticate_user(username, password):
                    st.session_state.authenticated = True
                    st.session_state.username = username
                    st.rerun()
                else:
                    st.error("Invalid username or password")
        
        st.markdown("</div>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; margin-top: 1rem; color: #666;'>Demo credentials: doctor / password123</p>", unsafe_allow_html=True)

def main_dashboard():
    st.markdown(custom_css, unsafe_allow_html=True)
    
    # Header
    col1, col2 = st.columns([3, 1])
    with col1:
        st.title("RetinaView AI Dashboard")
        st.markdown(f"Welcome, **{st.session_state.username}**!")
    
    with col2:
        if st.button("Logout"):
            st.session_state.authenticated = False
            st.session_state.username = None
            st.rerun()

    # Sidebar navigation
    st.sidebar.title("Navigation")
    page = st.sidebar.selectbox("Select Page", [
        "Patient Registration",
        "Image Upload & Analysis",
        "Patient History",
        "Notifications",
        "Reports"
    ])

    dm = get_data_manager()

    if page == "Patient Registration":
        patient_registration_page(dm)
    elif page == "Image Upload & Analysis":
        image_upload_page(dm)
    elif page == "Patient History":
        patient_history_page(dm)
    elif page == "Notifications":
        notifications_page(dm)
    elif page == "Reports":
        reports_page(dm)

def patient_registration_page(dm):
    st.header("Patient Registration")
    
    with st.form("patient_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            patient_id = st.text_input("Patient ID", placeholder="Enter unique patient ID")
            scan_date = st.date_input("Scan Date", datetime.now())
        
        with col2:
            eye = st.selectbox("Eye", ["Left", "Right", "Both"])
        
        submitted = st.form_submit_button("Register Patient")
        
        if submitted:
            if not patient_id:
                st.error("Patient ID is required")
            elif dm.create_patient(patient_id, scan_date.isoformat(), eye):
                st.success(f"Patient {patient_id} registered successfully!")
                dm.add_notification(f"New patient registered: {patient_id}")
            else:
                st.error("Patient ID already exists")

def image_upload_page(dm):
    st.header("Image Upload & Analysis")
    
    # Patient selection
    patients = list(dm.patients_db.keys())
    if not patients:
        st.warning("No patients registered. Please register a patient first.")
        return
    
    selected_patient = st.selectbox("Select Patient", patients)
    
    if selected_patient:
        patient_info = dm.get_patient(selected_patient)
        st.markdown(f"**Patient:** {patient_info['patient_id']} | **Eye:** {patient_info['eye']} | **Scan Date:** {patient_info['scan_date']}")
        
        # File upload
        uploaded_files = st.file_uploader(
            "Upload Retinal Images",
            type=['png', 'jpg', 'jpeg', 'tiff'],
            accept_multiple_files=True
        )
        
        if uploaded_files:
            st.success(f"Uploaded {len(uploaded_files)} file(s)")
            
            # Save uploaded files
            patient_folder = os.path.join(UPLOAD_DIR, selected_patient)
            os.makedirs(patient_folder, exist_ok=True)
            
            saved_files = []
            for file in uploaded_files:
                filename = f"{uuid4().hex}_{file.name}"
                file_path = os.path.join(patient_folder, filename)
                with open(file_path, "wb") as f:
                    f.write(file.getbuffer())
                saved_files.append(filename)
            
            # Display uploaded images
            cols = st.columns(min(len(uploaded_files), 3))
            for i, file in enumerate(uploaded_files):
                with cols[i % 3]:
                    st.image(file, caption=file.name, use_column_width=True)
            
            # Analysis form
            st.subheader("Analysis Results")
            with st.form("analysis_form"):
                diagnosis = st.selectbox("Diagnosis", [
                    "Normal",
                    "Diabetic Retinopathy",
                    "Macular Degeneration",
                    "Glaucoma",
                    "Retinal Detachment",
                    "Other"
                ])
                
                confidence = st.slider("Confidence Level (%)", 0, 100, 85)
                details = st.text_area("Additional Details", placeholder="Enter any additional observations...")
                
                if st.form_submit_button("Save Analysis"):
                    dm.save_analysis(selected_patient, diagnosis, confidence, details)
                    st.success("Analysis saved successfully!")
                    dm.add_notification(f"Analysis completed for patient {selected_patient}: {diagnosis}")

def patient_history_page(dm):
    st.header("Patient History")
    
    # Search filters
    col1, col2 = st.columns(2)
    with col1:
        patient_filter = st.text_input("Search by Patient ID", placeholder="Enter patient ID...")
    with col2:
        diagnosis_filter = st.text_input("Search by Diagnosis", placeholder="Enter diagnosis...")
    
    # Search results
    patients = dm.search_patients(patient_filter, diagnosis_filter)
    
    if patients:
        st.subheader(f"Found {len(patients)} patient(s)")
        
        for patient in patients:
            with st.expander(f"Patient: {patient['patient_id']} - {patient['eye']} Eye"):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write(f"**Patient ID:** {patient['patient_id']}")
                    st.write(f"**Scan Date:** {patient['scan_date']}")
                    st.write(f"**Eye:** {patient['eye']}")
                
                with col2:
                    analysis = dm.get_analysis(patient['patient_id'])
                    if analysis:
                        st.write(f"**Diagnosis:** {analysis['diagnosis']}")
                        st.write(f"**Confidence:** {analysis['confidence']}%")
                        if analysis.get('details'):
                            st.write(f"**Details:** {analysis['details']}")
                    else:
                        st.write("No analysis available")
                
                # Show uploaded images if any
                patient_folder = os.path.join(UPLOAD_DIR, patient['patient_id'])
                if os.path.exists(patient_folder):
                    image_files = [f for f in os.listdir(patient_folder) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.tiff'))]
                    if image_files:
                        st.write(f"**Images:** {len(image_files)} file(s) uploaded")
    else:
        st.info("No patients found matching the search criteria.")

def notifications_page(dm):
    st.header("Notifications")
    
    # Add new notification
    with st.form("notification_form"):
        message = st.text_input("Add Notification", placeholder="Enter notification message...")
        if st.form_submit_button("Add Notification"):
            if message:
                dm.add_notification(message)
                st.success("Notification added!")
                st.rerun()
    
    # Display notifications
    notifications = dm.get_notifications()
    if notifications:
        # Sort by timestamp (newest first)
        notifications.sort(key=lambda x: x['timestamp'], reverse=True)
        
        for notification in notifications:
            timestamp = datetime.fromisoformat(notification['timestamp']).strftime("%Y-%m-%d %H:%M:%S")
            st.markdown(f"""
            <div class="notification">
                <strong>{notification['message']}</strong><br>
                <small>{timestamp}</small>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("No notifications available.")

def reports_page(dm):
    st.header("Reports")
    
    patients = list(dm.patients_db.keys())
    if not patients:
        st.warning("No patients available for reports.")
        return
    
    selected_patient = st.selectbox("Select Patient for Report", patients)
    
    if selected_patient:
        patient_info = dm.get_patient(selected_patient)
        analysis = dm.get_analysis(selected_patient)
        
        st.subheader(f"Report for Patient: {selected_patient}")
        
        # Display report content
        report_content = f"""
        # RetinaView AI Medical Report
        
        **Patient ID:** {patient_info['patient_id']}
        **Scan Date:** {patient_info['scan_date']}
        **Eye:** {patient_info['eye']}
        **Report Generated:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
        
        ---
        
        ## Analysis Results
        """
        
        if analysis:
            report_content += f"""
        **Diagnosis:** {analysis['diagnosis']}
        **Confidence Level:** {analysis['confidence']}%
        **Analysis Date:** {analysis['timestamp']}
        
        **Details:** {analysis.get('details', 'No additional details provided.')}
        """
        else:
            report_content += "No analysis results available."
        
        # Show uploaded images
        patient_folder = os.path.join(UPLOAD_DIR, selected_patient)
        if os.path.exists(patient_folder):
            image_files = [f for f in os.listdir(patient_folder) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.tiff'))]
            if image_files:
                report_content += f"\n\n**Images:** {len(image_files)} retinal image(s) analyzed"
        
        st.markdown(report_content)
        
        # Download report button
        if st.button("Download Report as Text"):
            st.download_button(
                label="Download Report",
                data=report_content,
                file_name=f"report_{selected_patient}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                mime="text/plain"
            )

def main():
    st.set_page_config(
        page_title="RetinaView AI",
        page_icon="👁️",
        layout="wide"
    )
    
    # Initialize session state
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'username' not in st.session_state:
        st.session_state.username = None
    
    # Check authentication
    if not st.session_state.authenticated:
        login_form()
    else:
        main_dashboard()

if __name__ == "__main__":
    main()
