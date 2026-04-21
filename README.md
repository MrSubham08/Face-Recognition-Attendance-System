# 🎯 FaceAttend — Face Recognition Attendance System

> **AI-powered attendance system** that uses real-time face recognition to automate student attendance. Built with Python, Flask, OpenCV & face_recognition.

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| 🎥 **Live Face Registration** | Register students using webcam — face encodings stored securely |
| 🔍 **AI Face Matching** | Mark attendance by face recognition with confidence scoring |
| 📊 **Admin Dashboard** | Branch-wise filtering, attendance %, all student details |
| ✏️ **Full CRUD** | Create, Read, Update & Delete student records |
| 📅 **Attendance History** | Date-wise attendance records for each student |
| 🔐 **Forgot Credentials** | Recover login details using face — no email/OTP needed |
| 🛡️ **Role-based Access** | Separate student & admin authentication |
| 📱 **Responsive Design** | Works on desktop, tablet & mobile |

---

## 🛠️ Tech Stack

| Technology | Purpose |
|-----------|---------|
| **Python 3** | Backend logic |
| **Flask** | Web framework |
| **face_recognition** | AI face detection & matching |
| **OpenCV** | Image processing |
| **SQLite** | Database |
| **Bootstrap 5** | Responsive UI |
| **JavaScript** | Camera, validation, AJAX |

---

## 📂 Project Structure

```
📁 Face-Recognition-Attendance-System/
├── 📄 app.py                    # Flask routes & controllers
├── 📄 database.py               # SQLite models, CRUD, calculations
├── 📄 face_utils.py             # Face encoding & matching logic
├── 📄 requirements.txt          # Python dependencies
├── 📁 static/
│   ├── 📁 css/style.css         # Premium dark theme UI
│   └── 📁 js/main.js           # Camera, validation, AJAX
└── 📁 templates/
    ├── base.html                # Shared layout
    ├── index.html               # Landing page
    ├── register.html            # Student registration + webcam
    ├── student_login.html       # Login (Reg No. + DOB)
    ├── student_dashboard.html   # Attendance marking
    ├── student_history.html     # Attendance records
    ├── forgot_credentials.html  # Face-based recovery
    ├── admin_login.html         # Admin authentication
    ├── admin_dashboard.html     # Student management
    └── admin_edit.html          # Edit student details
```

---

## 🚀 Getting Started

### Prerequisites
- Python 3.8+
- pip
- Webcam

### Installation

```bash
# Clone the repo
git clone https://github.com/MrSubham08/Face-Recognition-Attendance-System.git
cd Face-Recognition-Attendance-System

# Install dependencies
pip install -r requirements.txt

# Run the application
python app.py
```

Open **http://127.0.0.1:5000** in your browser.

---

## 🔑 Login Credentials

| Role | Username / ID | Password |
|------|--------------|----------|
| **Admin** | `subham` | `admin@1234` |
| **Student** | Registration Number | Date of Birth |

---

## 📋 Registration Number Format

```
21  103  135  014
──  ───  ───  ───
YY  Branch 135  Roll
    Code  (fixed)  No.
```

| Code | Branch |
|------|--------|
| 101 | CE — Civil Engineering |
| 102 | ME — Mechanical Engineering |
| 103 | EE — Electrical Engineering |
| 104 | ECE — Electronics & Communication |
| 105 | CSE — Computer Science |
| 106 | IT — Information Technology |
| 107 | EEE — Electrical & Electronics |

---

## 📸 How It Works

1. **Register** → Fill details + capture face via webcam
2. **Login** → Enter Registration Number + Date of Birth
3. **Mark Attendance** → Camera captures face → AI verifies → Attendance marked
4. **Forgot Credentials?** → Capture face → System recovers your login details
5. **Admin Panel** → View all students, edit/delete, track attendance

---

## ⚙️ Validation Rules

- ✅ Name: Only alphabets allowed
- ✅ Registration Number: Exactly 11 digits with valid branch code
- ✅ DOB: Must be 18+ years old
- ✅ Phone: +91 format, starts with 6/7/8/9
- ✅ Duplicate registration blocked with redirect to login
- ✅ Attendance: Once per day per student

---

## 👨‍💻 Developer

**Subham Kumar**

---

## 📄 License

This project is open source and available for educational purposes.
