# Fake Job Detection System

A machine learning and FastAPI-based system that detects whether a job posting is **real or fake**. Built as a Python project for learning and practical application.

## Features

* Predicts if a job post is **real or fake**
* Provides **confidence score**
* Full-stack **FastAPI backend**
* Admin dashboard for monitoring and analytics
* CSV and PDF export functionality
* Deployable on cloud platforms

## Live Demo

### Main Application

https://fake-job-detector-production-cb70.up.railway.app/

### Admin Dashboard

https://fake-job-detector-production-cb70.up.railway.app/admin

### Health Check API

https://fake-job-detector-production-cb70.up.railway.app/health

## Technologies

* Python 3.x
* FastAPI
* Scikit-learn
* Joblib
* SQLite
* Firebase Authentication
* Railway
* Git & GitHub

## Project Structure

```text
app/
├── auth/
├── frontend/
├── models/
├── services/
├── storage/
├── static/
└── main.py
```

## How to Run Locally

### 1. Clone the Repository

```bash
git clone https://github.com/Akhilagoud907/Fake-Job-detection-system.git
cd Fake-Job-detection-system
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Run FastAPI Backend

```bash
uvicorn app.main:app --reload
```

### 4. Access the Application

Frontend:

```text
http://127.0.0.1:8000/
```

Admin Dashboard:

```text
http://127.0.0.1:8000/admin
```

API Documentation:

```text
http://127.0.0.1:8000/docs
```

## API Endpoints

### Prediction

```http
POST /predict
```

### Flag Suspicious Job

```http
POST /feedback/flag
```

### Health Check

```http
GET /health
```

### Admin Dashboard

```http
GET /admin
```

## Deployment

The application is deployed on Railway:

https://fake-job-detector-production-cb70.up.railway.app/

## Author

Akhila Goud

GitHub:
https://github.com/Akhilagoud907
