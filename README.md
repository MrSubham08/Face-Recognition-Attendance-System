# 🎯 FaceAttend — Face Recognition Attendance System

> An AI-powered, web-based attendance system that eliminates manual tracking using real-time face recognition technology.

### 🌐 [Live Demo](https://face-recognition-attendance-system-xr13.onrender.com) &nbsp;·&nbsp; ⚡ Free tier — may take ~30s to wake up

---

## ✨ Key Features

- 🎥 **Live Face Registration** — One-time webcam-based enrollment
- 🔍 **AI-Powered Attendance** — Instantly mark attendance via face match (128-dimensional facial encoding with configurable tolerance)
- 📊 **Admin Dashboard** — Branch-wise analytics, student management & real-time tracking
- 🔄 **Full CRUD Operations** — Complete student record management
- 🔐 **Face-Based Credential Recovery** — Forgot your login? Just show your face
- 📱 **Responsive UI** — Premium dark-themed design that works everywhere
- ✅ **Smart Validation** — 11-digit reg number format, age verification (18+), Indian phone number validation

---

## 🛠️ Tech Stack

| Layer | Technologies |
|-------|-------------|
| **Backend** | Python · Flask · SQLite · Gunicorn |
| **AI/ML** | face_recognition · OpenCV · dlib · NumPy |
| **Frontend** | HTML5 · CSS3 · JavaScript · Bootstrap 5 |
| **Deployment** | Docker · Render |

---

## 🚀 Quick Start

```bash
# Clone & setup
git clone https://github.com/MrSubham08/Face-Recognition-Attendance-System.git
cd Face-Recognition-Attendance-System

# Install dependencies
pip install -r requirements.txt

# Run
python app.py
```

Open → **http://127.0.0.1:5000**

> **Requirements:** Python 3.8+ · pip · Webcam

---

## 🐳 Docker Deployment

```bash
docker build -t faceattend .
docker run -p 5000:5000 faceattend
```

Deployed on [Render](https://render.com) with Docker for production use.

---

## 📂 Project Structure

```
├── app.py               # Routes & controllers
├── database.py          # Database models & business logic
├── face_utils.py        # Face detection & matching engine
├── Dockerfile           # Production Docker config
├── requirements.txt
├── static/              # CSS & JavaScript
└── templates/           # 10 HTML templates
```

---

## 📸 How It Works

1. **Register** → Capture face via webcam + fill student details
2. **Login** → Authenticate with Registration Number & DOB
3. **Mark Attendance** → Face is matched against stored encoding in real-time
4. **Admin Panel** → Monitor, manage & analyze attendance data

---

## 🔑 Admin Access

| Field | Value |
|-------|-------|
| Username | `subham` |
| Password | `admin@1234` |

---

## 👨‍💻 Developer

Built with ❤️ by **Subham Kumar**

---

## 📄 License

Open source — available for educational purposes.
