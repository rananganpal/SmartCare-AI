# SmartCare AI

A lightweight SIH prototype for hospital appointment and queue optimization.

## Features
- Patient, doctor and admin login
- Appointment booking
- AI-style best-slot recommendation
- Digital token
- Live queue
- Doctor queue controls
- Admin analytics
- FastAPI backend
- SQLite database (lightweight for laptop/SIH demo)

## Run

### 1. Open terminal in backend
```bash
cd backend
python -m pip install -r requirements.txt
python -m uvicorn main:app --reload
```

### 2. Open frontend
Use VS Code Live Server on `frontend/index.html`.

If browser blocks requests from file://, Live Server is recommended.

## Demo accounts
Patient:
patient@smartcare.com / 1234

Doctor:
doctor@smartcare.com / 1234

Admin:
admin@smartcare.com / 1234

## Important
This is a prototype. The AI recommendation currently uses a lightweight scoring/heuristic method. For a production/SIH advanced version, train a model using anonymized historical hospital data and add secure authentication, password hashing, role-based authorization, audit logs and proper database deployment.
