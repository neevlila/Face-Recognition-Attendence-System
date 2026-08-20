# AuraPass AI — Next-Gen Facial Biometric Attendance & Analytics Platform

[![Python 3.12](https://img.shields.io/badge/Python-3.12-3776AB.svg?logo=python&logoColor=white)](https://www.python.org/)
[![Flask 3.1](https://img.shields.io/badge/Flask-3.1-000000.svg?logo=flask&logoColor=white)](https://palletsprojects.com/p/flask/)
[![OpenCV](https://img.shields.io/badge/OpenCV-LBPH%20Recognition-5C3EE8.svg?logo=opencv&logoColor=white)](https://opencv.org/)
[![SQLite](https://img.shields.io/badge/Database-SQLite%20WAL-003B57.svg?logo=sqlite&logoColor=white)](https://sqlite.org/)
[![UI](https://img.shields.io/badge/UI-Glassmorphism%20%2B%20Theme%20Toggle-6366F1.svg)](https://github.com/)

**AuraPass AI** is an enterprise-grade, real-time biometric presence platform powered by high-performance Computer Vision (OpenCV Haar Cascade Face Detection + Local Binary Patterns Histograms [LBPH] Recognition) and a SaaS Admin Dashboard built on Flask, Chart.js, and a responsive Glassmorphism design system.

---

## 🌟 Key Features

### 1. ⚡ High-FPS Real-Time Recognition & HUD Console
- **Instant Video Stream**: Background multi-threaded grabber (`CameraManager`) with zero spin-up lag and DirectShow hardware backend.
- **Pyramid Downscaled Detection**: 3.5x faster face detection (~2.9ms per frame) on 640×480 streams.
- **Dynamic Computer Vision HUD**:
  - 🟩 **Emerald Green**: Recognized & attendance marked.
  - 🟦 **Cyan**: Recognized & already marked today (Duplicate Protected).
  - 🟥 **Crimson**: Unregistered / unknown face.
  - 🟧 **Amber**: Match below certainty threshold.

### 2. 📸 6-Shot Step-by-Step Face Capture Studio
- **Guided Poses**:
  - Shot 1: Frontal Neutral Expression
  - Shot 2: Slight Head Turn to Right (~15°)
  - Shot 3: Slight Head Turn to Left (~15°)
  - Shot 4: Natural Smile
  - Shot 5: Slight Tilt Upwards (~10°)
  - Shot 6: Slight Tilt Downwards (~10°)
- **Manual Shutter Control**: Takes crisp snapshots on demand with visual shutter flash feedback (no continuous camera spam).
- **Interactive Retake Suite**: Click any of the 6 slots to retake or delete individual photos.

### 3. 🌓 Glassmorphism & Dynamic Theme Switching
- **Glassmorphism Header**: Translucent frosted glass navigation (`backdrop-filter: blur(20px) saturate(180%)`) with specular lighting borders.
- **Light & Dark Themes**: Interactive sliding toggle pill with Sun ☀️ and Moon 🌙 icons and smooth CSS physics.
- **Modern Login Portal**: Ambient animated glow mesh orbs, laser-scanning biometric face animation, and 1-click credentials auto-fill.

### 4. 🛡️ Duplicate Attendance & Database Integrity
- **Multi-Layer Duplicate Guard**: In-memory rapid lookup cache (`marked_today_set`) + SQLite relational constraint (`UNIQUE(student_id, attendance_date)`).
- **Auto-Sync Model Lifecycle**: Deleting students or resetting datasets automatically synchronizes and clears model weights (`models/trainer.yml`).

### 5. 📊 Analytics & Academic Reporting
- **Real-Time KPIs**: Total Enrolled Students, Present Today, Absent Today, Attendance Rate %.
- **7-Day Trend Charts**: Smooth Chart.js trend visualization and department breakdown graphs.
- **Smart Date Range Filter**: Chronological date constraint lock ensuring "To Date" is always after "From Date".
- **Spreadsheet Exports**: 1-click export to **CSV** and **Excel (`.xlsx`)** spreadsheets.

---

## 🏗️ System Architecture

```text
Face Recognition Attendence System/
├── app/
│   ├── __init__.py               # Flask application factory, DB bootstrap & context processors
│   ├── config.py                 # Central configuration (paths, thresholds, parameters)
│   ├── database/
│   │   ├── db.py                 # SQLite connection manager (WAL mode, busy timeouts, foreign keys)
│   │   ├── schema.py             # Relational DDL definitions & default admin seeding
│   │   └── models.py             # Model layers: Admin, Student, Attendance, Settings, ActivityLog
│   ├── routes/
│   │   ├── auth.py               # Admin authentication (Login, Logout, Session guard)
│   │   ├── dashboard.py          # KPI metrics, chart feeds, live activity logs
│   │   ├── students.py           # Student directory CRUD, search, filter, profile view
│   │   ├── recognition.py        # Non-blocking MJPEG streams, 6-shot capture API, training routes
│   │   ├── attendance.py         # Verified attendance logs, date range constraints, record deletion
│   │   ├── reports.py            # Academic attendance reports, CSV & Excel generators
│   │   └── settings.py           # Calibration thresholds, camera device index, password manager
│   ├── services/
│   │   ├── face_detection.py     # Fast pyramid Haar Cascade detector & quality evaluator
│   │   ├── face_capture.py       # 6-shot studio collector, pose guide, and slot manager
│   │   ├── face_recognition.py   # LBPH training pipeline, auto-clear, and prediction engine
│   │   ├── attendance_service.py # Live video processor, HUD drawer, in-memory duplicate cache
│   │   ├── analytics_service.py  # Aggregator for KPIs, trends, and department breakdowns
│   │   └── report_service.py     # Pandas / OpenPyXL CSV & Excel export generator
│   ├── static/
│   │   ├── css/style.css         # Glassmorphic SaaS design system & theme tokens
│   │   └── js/
│   │       ├── main.js           # Theme toggle, date range locks, modals, toast alerts
│   │       ├── live_attendance.js# Real-time event polling & live recognition updates
│   │       ├── face_capture.js   # 6-shot step-by-step studio controller & slot retake
│   │       └── charts.js         # Chart.js dark/light theme graph initializers
│   └── templates/
│       ├── base.html             # Master layout with Glassmorphic header & sidebar
│       ├── auth/login.html       # Animated biometric login portal
│       ├── dashboard/index.html  # Live KPIs, 7-day trend chart, today's log, recent activity
│       ├── recognition/live.html # Real-time Computer Vision monitoring console
│       ├── students/             # Student index, 6-slot dataset gallery, registration
│       ├── attendance/           # Filterable attendance logs with date lock
│       ├── reports/              # Cumulative student statistics & exam eligibility table
│       └── settings/             # System calibration & credentials form
├── dataset/                      # Face image datasets organized by student_id
├── models/                       # Trained LBPH model (trainer.yml) & labels (labels.json)
├── exports/                      # Generated CSV and Excel reports
├── tests/                        # 19 automated unit & integration tests
├── app.py                        # Application entry point
├── requirements.txt              # Project dependencies
├── .gitignore                    # Git ignore configuration
└── .env.example                  # Environment configuration template
```

---

## ⚙️ Installation & Quick Start

### 1. Prerequisites
- Python 3.10, 3.11, or 3.12 installed.
- A built-in webcam or USB camera.

### 2. Setup Virtual Environment & Install Dependencies
```bash
# Clone or open workspace directory
cd "c:\Users\hp\Documents\Face Recognition Attendence System"

# Create virtual environment (optional)
python -m venv venv
venv\Scripts\activate

# Install required dependencies
pip install -r requirements.txt
```

### 3. Run the Application
```bash
python app.py
```

Open your browser and navigate to:
👉 **`http://127.0.0.1:5000`**

---

## 🔑 Default Credentials

| Username | Password | Access Level |
| :--- | :--- | :--- |
| `admin` | `admin123` | Master System Administrator |

*(Credentials can be updated anytime from the **System Settings** page).*

---

## 🎓 Academic Viva & Technical Explanation Guide

### 1. What is the difference between Face Detection and Face Recognition?
- **Face Detection**: Answers *"Where is a face in the image?"* Locates bounding box coordinates $(x, y, w, h)$ regardless of identity using OpenCV's **Haar Cascade Classifier**.
- **Face Recognition**: Answers *"Whose face is this?"* Extracts texture features from the cropped face region and compares them against enrolled biometric profiles using **LBPH (Local Binary Patterns Histograms)**.

### 2. How does the LBPH Algorithm work?
1. **Histogram Equalization**: Normalizes lighting variations across grayscale crops.
2. **Local Binary Pattern Operator**: For each $3 \times 3$ window, compares surrounding 8 pixels to the center pixel:
   $$\text{LBP}(x_c, y_c) = \sum_{p=0}^{P-1} s(i_p - i_c) 2^p \quad \text{where } s(x) = \begin{cases} 1 & x \ge 0 \\ 0 & x < 0 \end{cases}$$
3. **Spatial Grid Concatenation**: Splits the image into $8 \times 8$ local grids, calculates histograms of texture patterns per grid, and concatenates them into a single descriptor vector.
4. **Chi-Square Distance Matching**: Compares test face vectors to stored training vectors using Chi-Square Distance. Lower distance indicates a closer match.

### 3. How is Confidence calculated?
$$\text{Confidence (\%)} = \max(0, \min(100, 100 - (\text{Distance} \times 0.65)))$$
Attendance is automatically verified and recorded when $\text{Confidence} \ge 70\%$.

---

## 🧪 Automated Testing

Run the full automated test suite (19 test cases):
```bash
python -m unittest discover -s tests
```

---

## 🔒 Privacy & Local Security
All facial biometric data and SQLite databases are stored strictly on the local server filesystem and are never transmitted over the internet or sent to external cloud APIs.

---

## 📄 License
Developed for Academic Research & Enterprise Deployment. MIT License.
