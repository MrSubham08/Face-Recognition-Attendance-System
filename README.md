# 🎯 FaceAttend — Enterprise Face Recognition Attendance System

> An AI-powered, scalable, web-based attendance system that eliminates manual tracking using real-time facial recognition technology. Upgraded with an enterprise-ready architecture.

### 🌐 [Live Production Demo](https://face-recognition-attendance-system-xr13.onrender.com) &nbsp;·&nbsp; ⚡ Free tier — may take ~30s to wake up

---

## ✨ Enterprise Features

- 🎥 **Live Face Registration** — One-time webcam-based enrollment
- 🔍 **AI-Powered Attendance** — Instantly mark attendance via face match (128-dimensional facial encoding with configurable tolerance)
- 📊 **Admin Dashboard** — Branch-wise analytics, student management & real-time tracking
- 🔄 **Scalable Architecture** — Built with Flask Blueprints and Application Factories
- 🔐 **Bank-Grade Security** — Flask-Login integration, cryptographically secure sessions, and hidden environment variables
- 🗄️ **Robust Persistence** — Fully migrated to PostgreSQL to support high-concurrency read/writes
- 📱 **Responsive UI** — Premium dark-themed design that works across all devices
- ✅ **Smart Validation** — 11-digit reg number format, age verification (18+), Indian phone number validation

---

## 🛠️ Tech Stack

| Layer | Technologies |
|-------|-------------|
| **Backend** | Python · Flask Blueprints · Flask-Login · Gunicorn |
| **Database** | PostgreSQL · psycopg2 |
| **AI/ML** | face_recognition · OpenCV · dlib · NumPy |
| **Frontend** | HTML5 · Vanilla CSS3 · JavaScript · Bootstrap 5 |
| **Deployment** | Docker (Python 3.10-slim) · Render |

---

## 🚀 Quick Start (Local Development)

```bash
# Clone & setup
git clone https://github.com/MrSubham08/Face-Recognition-Attendance-System.git
cd Face-Recognition-Attendance-System

# Install dependencies
pip install -r requirements.txt

# Environment Setup
# Create a .env file based on .env.example
cp .env.example .env

# Run the Application Factory
python run.py
```

Open → **http://127.0.0.1:5000**

> **Requirements:** Python 3.10 · pip · Webcam · PostgreSQL (optional for local)

---

## 🐳 Docker Deployment

```bash
docker build -t faceattend .
docker run -p 5000:5000 faceattend
```

Deployed on [Render](https://render.com) with Docker for production use.

---

## 📂 Enterprise Project Structure

```
├── app/
│   ├── admin/           # Admin-specific routes
│   ├── auth/            # Authentication & Registration
│   ├── student/         # Student dashboard & logic
│   ├── __init__.py      # Flask Application Factory & Flask-Login
│   ├── database.py      # PostgreSQL business logic
│   └── face_utils.py    # Face detection & matching engine
├── run.py               # Application entry point
├── Dockerfile           # Production Docker config
├── requirements.txt     # Python dependencies
├── static/              # CSS & JavaScript assets
└── templates/           # HTML templates (Jinja2)
```

---

## 🔑 Admin Access

For security reasons, hardcoded credentials have been completely removed.
Admin access is now managed securely via `.env` Environment Variables:
- `ADMIN_USERNAME`
- `ADMIN_PASSWORD`

---

## 👨‍💻 Developer

Built with ❤️ by **Subham Kumar**

---

## 📄 License

Open source — available for educational purposes.
