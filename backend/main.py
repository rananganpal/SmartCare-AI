from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime, timedelta
import sqlite3
import os


# =========================================================
# SMARTCARE AI
# Hospital Appointment & Queue Optimization System
# =========================================================


app = FastAPI(title="SmartCare AI")


# =========================================================
# CORS
# =========================================================
# Allows the public GitHub Pages frontend to communicate
# with the Render-hosted FastAPI backend.
#
# GitHub Pages:
# https://rananganpal.github.io/SmartCare-AI/
#
# IMPORTANT:
# The origin is only https://rananganpal.github.io
# Do NOT add /SmartCare-AI here.
# =========================================================

app.add_middleware(
    CORSMiddleware,

    allow_origins=[
        "https://rananganpal.github.io",

        # Local VS Code / Live Server
        "http://localhost:5500",
        "http://127.0.0.1:5500",

        # Local FastAPI testing
        "http://localhost:8000",
        "https://smartcare-ai-oqq2.onrender.com"
    ],

    allow_credentials=False,

    allow_methods=["*"],

    allow_headers=["*"],
)


# =========================================================
# DATABASE
# =========================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DB_PATH = os.path.join(
    BASE_DIR,
    "smartcare.db"
)


# =========================================================
# QUEUE SETTINGS
# =========================================================

# Normal consultation time for one patient
CONSULTATION_MINUTES = 10

# Doctor's OPD session = 3 hours
SESSION_MINUTES = 180

# 180 / 10 = 18 planned patients
MAX_PATIENTS = SESSION_MINUTES // CONSULTATION_MINUTES


# =========================================================
# DEPARTMENT SCHEDULE
# =========================================================

DEPARTMENT_SCHEDULE = {

    "Cardiology": {
        "doctor": "Dr. Sharma",
        "start": "09:00",
        "end": "12:00"
    },

    "Orthopedics": {
        "doctor": "Dr. Das",
        "start": "09:00",
        "end": "12:00"
    },

    "Dermatology": {
        "doctor": "Dr. Roy",
        "start": "10:00",
        "end": "13:00"
    },

    "Neurology": {
        "doctor": "Dr. Mehta",
        "start": "10:00",
        "end": "13:00"
    },

    "Ophthalmology": {
        "doctor": "Dr. Priya",
        "start": "11:00",
        "end": "14:00"
    },

    "ENT": {
        "doctor": "Dr. Verma",
        "start": "11:00",
        "end": "14:00"
    },

    "General Medicine": {
        "doctor": "Dr. Singh",
        "start": "08:00",
        "end": "11:00"
    },

    "Pediatrics": {
        "doctor": "Dr. Ananya",
        "start": "09:00",
        "end": "12:00"
    },

    "Gynecology": {
        "doctor": "Dr. Neha",
        "start": "10:00",
        "end": "13:00"
    },

    "Dental": {
        "doctor": "Dr. Kapoor",
        "start": "11:00",
        "end": "14:00"
    },

    "Pulmonology": {
        "doctor": "Dr. Arjun",
        "start": "12:00",
        "end": "15:00"
    },

    "Oncology": {
        "doctor": "Dr. Iyer",
        "start": "14:00",
        "end": "17:00"
    }
}


# =========================================================
# DATABASE CONNECTION
# =========================================================

def get_db():

    conn = sqlite3.connect(
        DB_PATH
    )

    conn.row_factory = sqlite3.Row

    return conn


# =========================================================
# DATABASE MIGRATION HELPERS
# =========================================================

def column_exists(
    conn,
    table_name,
    column_name
):

    cursor = conn.execute(
        f"PRAGMA table_info({table_name})"
    )

    columns = [
        row["name"]
        for row in cursor.fetchall()
    ]

    return column_name in columns


def add_column_if_missing(
    conn,
    table_name,
    column_name,
    column_type
):

    if not column_exists(
        conn,
        table_name,
        column_name
    ):

        conn.execute(
            f"""
            ALTER TABLE {table_name}
            ADD COLUMN {column_name} {column_type}
            """
        )


# =========================================================
# INITIALIZE DATABASE
# =========================================================

def init_db():

    conn = get_db()


    # -----------------------------------------------------
    # USERS
    # -----------------------------------------------------

    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            name TEXT NOT NULL,

            email TEXT UNIQUE NOT NULL,

            password TEXT NOT NULL,

            role TEXT NOT NULL,

            department TEXT

        )
    """)


    # -----------------------------------------------------
    # APPOINTMENTS
    # -----------------------------------------------------

    conn.execute("""
        CREATE TABLE IF NOT EXISTS appointments (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            patient_id INTEGER,

            patient_name TEXT,

            department TEXT,

            doctor TEXT,

            appointment_date TEXT,

            time TEXT,

            token TEXT,

            planned_time TEXT,

            actual_start_time TEXT,

            actual_end_time TEXT,

            consultation_minutes INTEGER DEFAULT 10,

            delay_minutes INTEGER DEFAULT 0,

            status TEXT DEFAULT 'waiting'

        )
    """)


    # -----------------------------------------------------
    # MIGRATE OLD DATABASE
    # -----------------------------------------------------

    add_column_if_missing(
        conn,
        "users",
        "department",
        "TEXT"
    )

    add_column_if_missing(
        conn,
        "appointments",
        "patient_name",
        "TEXT"
    )

    add_column_if_missing(
        conn,
        "appointments",
        "doctor",
        "TEXT"
    )

    add_column_if_missing(
        conn,
        "appointments",
        "appointment_date",
        "TEXT"
    )

    add_column_if_missing(
        conn,
        "appointments",
        "time",
        "TEXT"
    )

    add_column_if_missing(
        conn,
        "appointments",
        "token",
        "TEXT"
    )

    add_column_if_missing(
        conn,
        "appointments",
        "planned_time",
        "TEXT"
    )

    add_column_if_missing(
        conn,
        "appointments",
        "actual_start_time",
        "TEXT"
    )

    add_column_if_missing(
        conn,
        "appointments",
        "actual_end_time",
        "TEXT"
    )

    add_column_if_missing(
        conn,
        "appointments",
        "consultation_minutes",
        "INTEGER DEFAULT 10"
    )

    add_column_if_missing(
        conn,
        "appointments",
        "delay_minutes",
        "INTEGER DEFAULT 0"
    )

    add_column_if_missing(
        conn,
        "appointments",
        "status",
        "TEXT DEFAULT 'waiting'"
    )


    # =====================================================
    # 🚨 EMERGENCY REQUESTS
    # =====================================================

    conn.execute("""
        CREATE TABLE IF NOT EXISTS emergency_requests (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            patient_id INTEGER NOT NULL,

            patient_name TEXT NOT NULL,

            emergency_type TEXT NOT NULL,

            description TEXT,

            location TEXT,

            emergency_contact TEXT,

            department TEXT,

            doctor TEXT,

            status TEXT DEFAULT 'requested',

            token TEXT UNIQUE,

            created_at TEXT NOT NULL,

            acknowledged_at TEXT,

            actual_start_time TEXT,

            resolved_at TEXT,

            response_minutes INTEGER

        )
    """)


    # -----------------------------------------------------
    # 🚨 EMERGENCY TABLE MIGRATION
    # -----------------------------------------------------

    add_column_if_missing(
        conn,
        "emergency_requests",
        "patient_id",
        "INTEGER"
    )

    add_column_if_missing(
        conn,
        "emergency_requests",
        "patient_name",
        "TEXT"
    )

    add_column_if_missing(
        conn,
        "emergency_requests",
        "emergency_type",
        "TEXT"
    )

    add_column_if_missing(
        conn,
        "emergency_requests",
        "description",
        "TEXT"
    )

    add_column_if_missing(
        conn,
        "emergency_requests",
        "location",
        "TEXT"
    )

    add_column_if_missing(
        conn,
        "emergency_requests",
        "emergency_contact",
        "TEXT"
    )

    add_column_if_missing(
        conn,
        "emergency_requests",
        "department",
        "TEXT"
    )

    add_column_if_missing(
        conn,
        "emergency_requests",
        "doctor",
        "TEXT"
    )

    add_column_if_missing(
        conn,
        "emergency_requests",
        "status",
        "TEXT DEFAULT 'requested'"
    )

    add_column_if_missing(
        conn,
        "emergency_requests",
        "token",
        "TEXT"
    )

    add_column_if_missing(
        conn,
        "emergency_requests",
        "created_at",
        "TEXT"
    )

    add_column_if_missing(
        conn,
        "emergency_requests",
        "acknowledged_at",
        "TEXT"
    )

    add_column_if_missing(
        conn,
        "emergency_requests",
        "actual_start_time",
        "TEXT"
    )

    add_column_if_missing(
        conn,
        "emergency_requests",
        "resolved_at",
        "TEXT"
    )

    add_column_if_missing(
        conn,
        "emergency_requests",
        "response_minutes",
        "INTEGER"
    )


    # -----------------------------------------------------
    # DEMO ACCOUNTS
    # -----------------------------------------------------

    demo_users = [

        (
            "Demo Patient",
            "patient@smartcare.com",
            "1234",
            "patient",
            None
        ),

        (
            "Dr. Sharma",
            "doctor@smartcare.com",
            "1234",
            "doctor",
            "Cardiology"
        ),

        (
            "Hospital Admin",
            "admin@smartcare.com",
            "1234",
            "admin",
            None
        )
    ]


    for user in demo_users:

        existing = conn.execute(
            """
            SELECT id
            FROM users
            WHERE email = ?
            """,
            (user[1],)
        ).fetchone()


        if not existing:

            conn.execute(
                """
                INSERT INTO users
                (
                    name,
                    email,
                    password,
                    role,
                    department
                )
                VALUES (?, ?, ?, ?, ?)
                """,
                user
            )


    conn.commit()

    conn.close()


# Run database initialization
init_db()


# =========================================================
# PYDANTIC MODELS
# =========================================================

class RegisterRequest(BaseModel):

    name: str

    email: str

    password: str

    role: str = "patient"

    department: str | None = None


class LoginRequest(BaseModel):

    email: str

    password: str


class AppointmentRequest(BaseModel):

    patient_id: int

    department: str

    doctor: str

    date: str

    time: str


class QueueUpdateRequest(BaseModel):

    status: str

    consultation_minutes: int | None = None


# =========================================================
# 🚨 EMERGENCY MODELS
# =========================================================

class EmergencyRequest(BaseModel):

    patient_id: int

    emergency_type: str

    description: str = ""

    location: str = ""

    emergency_contact: str = ""

    department: str


class EmergencyStatusRequest(BaseModel):

    status: str


# =========================================================
# TIME HELPERS
# =========================================================

def get_session_start(department):

    if department not in DEPARTMENT_SCHEDULE:

        raise HTTPException(
            status_code=400,
            detail="Invalid department"
        )

    return DEPARTMENT_SCHEDULE[
        department
    ]["start"]


def get_session_end(department):

    if department not in DEPARTMENT_SCHEDULE:

        raise HTTPException(
            status_code=400,
            detail="Invalid department"
        )

    return DEPARTMENT_SCHEDULE[
        department
    ]["end"]


def convert_time_to_datetime(
    date_string,
    time_string
):

    return datetime.strptime(
        f"{date_string} {time_string}",
        "%Y-%m-%d %H:%M"
    )


def format_time(dt):

    return dt.strftime(
        "%I:%M %p"
    )


def format_datetime(dt):

    return dt.strftime(
        "%Y-%m-%d %H:%M:%S"
    )


def parse_planned_time(
    appointment_date,
    planned_time
):

    return datetime.strptime(
        f"{appointment_date} {planned_time}",
        "%Y-%m-%d %I:%M %p"
    )


# =========================================================
# ROOT
# =========================================================

@app.get("/")
def home():

    return {

        "message":
            "SmartCare AI Backend Running",

        "consultation_minutes":
            CONSULTATION_MINUTES,

        "session_minutes":
            SESSION_MINUTES,

        "max_patients":
            MAX_PATIENTS

    }


# =========================================================
# DEPARTMENTS
# =========================================================

@app.get("/departments")
def departments():

    result = []


    for name, info in DEPARTMENT_SCHEDULE.items():

        result.append({

            "department": name,

            "doctor": info["doctor"],

            "start": info["start"],

            "end": info["end"],

            "session_minutes":
                SESSION_MINUTES,

            "consultation_minutes":
                CONSULTATION_MINUTES,

            "max_patients":
                MAX_PATIENTS

        })


    return result


# =========================================================
# REGISTER
# =========================================================

@app.post("/register")
def register(
    data: RegisterRequest
):

    conn = get_db()


    existing = conn.execute(
        """
        SELECT id
        FROM users
        WHERE email = ?
        """,
        (data.email,)
    ).fetchone()


    if existing:

        conn.close()

        raise HTTPException(
            status_code=400,
            detail=
            "Account already exists. Please login."
        )


    role = data.role.lower()


    if role not in [
        "patient",
        "doctor"
    ]:

        conn.close()

        raise HTTPException(
            status_code=400,
            detail="Invalid account type"
        )


    department = data.department


    if role == "doctor":

        if not department:

            conn.close()

            raise HTTPException(
                status_code=400,
                detail=
                "Doctor department is required"
            )


        if department not in DEPARTMENT_SCHEDULE:

            conn.close()

            raise HTTPException(
                status_code=400,
                detail="Invalid department"
            )

    else:

        department = None


    cursor = conn.execute(
        """
        INSERT INTO users
        (
            name,
            email,
            password,
            role,
            department
        )
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            data.name,
            data.email,
            data.password,
            role,
            department
        )
    )


    conn.commit()


    user_id = cursor.lastrowid


    conn.close()


    return {

        "message":
            "Account created successfully",

        "user": {

            "id": user_id,

            "name":
                data.name,

            "email":
                data.email,

            "role":
                role,

            "department":
                department

        }

    }


# =========================================================
# LOGIN
# =========================================================

@app.post("/login")
def login(
    data: LoginRequest
):

    conn = get_db()


    user = conn.execute(
        """
        SELECT *
        FROM users
        WHERE email = ?
        """,
        (data.email,)
    ).fetchone()


    conn.close()


    if not user:

        raise HTTPException(
            status_code=404,
            detail=
            "Account not found. Please create an account first."
        )


    if user["password"] != data.password:

        raise HTTPException(
            status_code=401,
            detail="Incorrect password"
        )


    return {

        "message":
            "Login successful",

        "user": {

            "id":
                user["id"],

            "name":
                user["name"],

            "email":
                user["email"],

            "role":
                user["role"],

            "department":
                user["department"]

        }

    }


# =========================================================
# RECOMMENDATION
# =========================================================

@app.get("/recommendation")
def recommendation(
    department: str,
    date: str
):

    if department not in DEPARTMENT_SCHEDULE:

        raise HTTPException(
            status_code=400,
            detail="Invalid department"
        )


    conn = get_db()


    appointments = conn.execute(
        """
        SELECT *
        FROM appointments
        WHERE department = ?
        AND appointment_date = ?
        AND status != 'cancelled'
        ORDER BY id ASC
        """,
        (
            department,
            date
        )
    ).fetchall()


    conn.close()


    booked = len(appointments)


    if booked >= MAX_PATIENTS:

        return {

            "available": False,

            "message":
                "All 18 patient slots are already booked.",

            "slots": []

        }


    # -----------------------------------------------------
    # NEXT AVAILABLE SLOTS
    # -----------------------------------------------------

    start_datetime = convert_time_to_datetime(
        date,
        get_session_start(department)
    )


    slots = []


    for i in range(
        booked,
        min(
            booked + 5,
            MAX_PATIENTS
        )
    ):

        slot_datetime = (
            start_datetime
            +
            timedelta(
                minutes=
                i * CONSULTATION_MINUTES
            )
        )


        slots.append({

            "time":
                format_time(slot_datetime),

            "wait_minutes":
                i * CONSULTATION_MINUTES,

            "slot_number":
                i + 1

        })


    return {

        "available": True,

        "department":
            department,

        "doctor":
            DEPARTMENT_SCHEDULE[
                department
            ]["doctor"],

        "session_start":
            DEPARTMENT_SCHEDULE[
                department
            ]["start"],

        "session_end":
            DEPARTMENT_SCHEDULE[
                department
            ]["end"],

        "session_minutes":
            SESSION_MINUTES,

        "consultation_minutes":
            CONSULTATION_MINUTES,

        "max_patients":
            MAX_PATIENTS,

        "booked_patients":
            booked,

        "remaining_patients":
            MAX_PATIENTS - booked,

        "slots":
            slots

    }


# =========================================================
# CREATE APPOINTMENT
# =========================================================

@app.post("/appointments")
def create_appointment(
    data: AppointmentRequest
):

    # -----------------------------------------------------
    # CHECK DEPARTMENT
    # -----------------------------------------------------

    if data.department not in DEPARTMENT_SCHEDULE:

        raise HTTPException(
            status_code=400,
            detail="Invalid department"
        )


    conn = get_db()


    # -----------------------------------------------------
    # CHECK PATIENT
    # -----------------------------------------------------

    patient = conn.execute(
        """
        SELECT *
        FROM users
        WHERE id = ?
        AND role = 'patient'
        """,
        (data.patient_id,)
    ).fetchone()


    if not patient:

        conn.close()

        raise HTTPException(
            status_code=404,
            detail="Patient account not found"
        )


    # -----------------------------------------------------
    # GET ACTIVE APPOINTMENTS
    # -----------------------------------------------------

    appointments = conn.execute(
        """
        SELECT *
        FROM appointments
        WHERE department = ?
        AND appointment_date = ?
        AND status != 'cancelled'
        ORDER BY id ASC
        """,
        (
            data.department,
            data.date
        )
    ).fetchall()


    booked_count = len(appointments)


    # -----------------------------------------------------
    # MAXIMUM 18 PATIENTS
    # -----------------------------------------------------

    if booked_count >= MAX_PATIENTS:

        conn.close()

        raise HTTPException(
            status_code=400,
            detail=
            "This department has reached its maximum of 18 patients for this session."
        )


    # -----------------------------------------------------
    # CHECK IF SAME PATIENT ALREADY BOOKED
    # -----------------------------------------------------

    existing_patient = conn.execute(
        """
        SELECT id
        FROM appointments
        WHERE patient_id = ?
        AND appointment_date = ?
        AND status != 'cancelled'
        """,
        (
            data.patient_id,
            data.date
        )
    ).fetchone()


    if existing_patient:

        conn.close()

        raise HTTPException(
            status_code=400,
            detail=
            "You already have an appointment for this date."
        )


    # -----------------------------------------------------
    # DOCTOR
    # -----------------------------------------------------

    doctor = DEPARTMENT_SCHEDULE[
        data.department
    ]["doctor"]


    # -----------------------------------------------------
    # TOKEN NUMBER
    # -----------------------------------------------------

    max_token_number = 0


    for appointment in appointments:

        token = appointment["token"]


        if token and "-" in token:

            try:

                number = int(
                    token.split("-")[-1]
                )

                max_token_number = max(
                    max_token_number,
                    number
                )

            except ValueError:

                pass


    token_number = max_token_number + 1


    if token_number > MAX_PATIENTS:

        conn.close()

        raise HTTPException(
            status_code=400,
            detail=
            "No more slots are available."
        )


    # -----------------------------------------------------
    # TOKEN
    # -----------------------------------------------------

    token = (
        f"{data.department[0].upper()}"
        f"-{token_number:02d}"
    )


    # -----------------------------------------------------
    # PLANNED TIME
    # -----------------------------------------------------

    session_start = get_session_start(
        data.department
    )


    start_datetime = convert_time_to_datetime(
        data.date,
        session_start
    )


    planned_datetime = (
        start_datetime
        +
        timedelta(
            minutes=
            (token_number - 1)
            *
            CONSULTATION_MINUTES
        )
    )


    planned_time = format_time(
        planned_datetime
    )


    # -----------------------------------------------------
    # SAVE APPOINTMENT
    # -----------------------------------------------------

    cursor = conn.execute(
        """
        INSERT INTO appointments
        (
            patient_id,
            patient_name,
            department,
            doctor,
            appointment_date,
            time,
            token,
            planned_time,
            actual_start_time,
            actual_end_time,
            consultation_minutes,
            delay_minutes,
            status
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            data.patient_id,

            patient["name"],

            data.department,

            doctor,

            data.date,

            planned_time,

            token,

            planned_time,

            None,

            None,

            CONSULTATION_MINUTES,

            0,

            "waiting"
        )
    )


    conn.commit()


    appointment_id = cursor.lastrowid


    conn.close()


    # -----------------------------------------------------
    # RECALCULATE QUEUE
    # -----------------------------------------------------

    calculate_queue_times(
        data.department,
        data.date
    )


    return {

        "message":
            "Appointment booked successfully",

        "appointment": {

            "id":
                appointment_id,

            "patient_id":
                data.patient_id,

            "patient_name":
                patient["name"],

            "department":
                data.department,

            "doctor":
                doctor,

            "date":
                data.date,

            "time":
                planned_time,

            "token":
                token,

            "planned_time":
                planned_time,

            "consultation_minutes":
                CONSULTATION_MINUTES,

            "status":
                "waiting"

        }

    }


# =========================================================
# QUEUE CALCULATION
# =========================================================

def calculate_queue_times(
    department,
    appointment_date
):

    conn = get_db()


    appointments = conn.execute(
        """
        SELECT *
        FROM appointments
        WHERE department = ?
        AND appointment_date = ?
        AND status != 'cancelled'
        ORDER BY id ASC
        """,
        (
            department,
            appointment_date
        )
    ).fetchall()


    if not appointments:

        conn.close()

        return


    # -----------------------------------------------------
    # SESSION START
    # -----------------------------------------------------

    session_start = convert_time_to_datetime(
        appointment_date,
        get_session_start(department)
    )


    previous_end = session_start


    for appointment in appointments:

        appointment_id = appointment["id"]

        status = appointment["status"]


        # =================================================
        # COMPLETED
        # =================================================

        if status == "completed":

            if appointment["actual_start_time"]:

                actual_start = datetime.strptime(
                    appointment[
                        "actual_start_time"
                    ],
                    "%Y-%m-%d %H:%M:%S"
                )

            else:

                actual_start = max(
                    planned_datetime,
                    previous_end
                )


            consultation = (
                appointment[
                    "consultation_minutes"
                ]
            )


            if (
                not consultation
                or consultation <= 0
            ):

                consultation = (
                    CONSULTATION_MINUTES
                )


            actual_end = (
                actual_start
                +
                timedelta(
                    minutes=consultation
                )
            )


            delay = max(
                0,
                int(
                    (
                        actual_start
                        -
                        planned_datetime
                    ).total_seconds()
                    / 60
                )
            )


            conn.execute(
                """
                UPDATE appointments

                SET actual_start_time = ?,
                    actual_end_time = ?,
                    consultation_minutes = ?,
                    delay_minutes = ?

                WHERE id = ?
                """,
                (
                    format_datetime(
                        actual_start
                    ),

                    format_datetime(
                        actual_end
                    ),

                    consultation,

                    delay,

                    appointment_id
                )
            )


            previous_end = actual_end


        # =================================================
        # IN PROGRESS
        # =================================================

        elif status == "in_progress":

            if appointment["actual_start_time"]:

                actual_start = datetime.strptime(
                    appointment[
                        "actual_start_time"
                    ],
                    "%Y-%m-%d %H:%M:%S"
                )

            else:

                actual_start = max(
                    planned_datetime,
                    previous_end
                )


                conn.execute(
                    """
                    UPDATE appointments

                    SET actual_start_time = ?

                    WHERE id = ?
                    """,
                    (
                        format_datetime(
                            actual_start
                        ),

                        appointment_id
                    )
                )


            consultation = (
                appointment[
                    "consultation_minutes"
                ]
            )


            if (
                not consultation
                or consultation <= 0
            ):

                consultation = (
                    CONSULTATION_MINUTES
                )


            previous_end = (
                actual_start
                +
                timedelta(
                    minutes=consultation
                )
            )


        # =================================================
        # WAITING
        # =================================================

        elif status == "waiting":

            planned_datetime = parse_planned_time(
                appointment_date,
                appointment["planned_time"]
            )


            expected_start = max(
                planned_datetime,
                previous_end
            )


            delay = max(
                0,
                int(
                    (
                        expected_start
                        -
                        planned_datetime
                    ).total_seconds()
                    / 60
                )
            )


            conn.execute(
                """
                UPDATE appointments

                SET delay_minutes = ?

                WHERE id = ?
                """,
                (
                    delay,
                    appointment_id
                )
            )


            previous_end = (
                expected_start
                +
                timedelta(
                    minutes=CONSULTATION_MINUTES
                )
            )


    conn.commit()

    conn.close()


# =========================================================
# GET CALCULATED QUEUE
# =========================================================

def get_calculated_queue(
    department,
    appointment_date
):

    conn = get_db()


    appointments = conn.execute(
        """
        SELECT *
        FROM appointments
        WHERE department = ?
        AND appointment_date = ?
        AND status != 'cancelled'
        ORDER BY id ASC
        """,
        (
            department,
            appointment_date
        )
    ).fetchall()


    conn.close()


    result = []


    session_start = convert_time_to_datetime(
        appointment_date,
        get_session_start(department)
    )


    previous_end = session_start


    for appointment in appointments:

        item = dict(appointment)


        planned_datetime = parse_planned_time(
            appointment_date,
            appointment["planned_time"]
        )


        status = appointment["status"]


        # -------------------------------------------------
        # COMPLETED
        # -------------------------------------------------

        if status == "completed":

            if appointment["actual_start_time"]:

                actual_start = datetime.strptime(
                    appointment[
                        "actual_start_time"
                    ],
                    "%Y-%m-%d %H:%M:%S"
                )

            else:

                actual_start = max(
                    planned_datetime,
                    previous_end
                )


            consultation = (
                appointment[
                    "consultation_minutes"
                ]
                or
                CONSULTATION_MINUTES
            )


            actual_end = (
                actual_start
                +
                timedelta(minutes=consultation)
            )


            expected_start = actual_start

            previous_end = actual_end


        # -------------------------------------------------
        # IN PROGRESS
        # -------------------------------------------------

        elif status == "in_progress":

            if appointment["actual_start_time"]:

                actual_start = datetime.strptime(
                    appointment[
                        "actual_start_time"
                    ],
                    "%Y-%m-%d %H:%M:%S"
                )

            else:

                actual_start = max(
                    planned_datetime,
                    previous_end
                )


            consultation = (
                appointment[
                    "consultation_minutes"
                ]
                or
                CONSULTATION_MINUTES
            )


            expected_start = actual_start


            previous_end = (
                actual_start
                +
                timedelta(minutes=consultation)
            )


        # -------------------------------------------------
        # WAITING
        # -------------------------------------------------

        else:

            expected_start = max(
                planned_datetime,
                previous_end
            )


            previous_end = (
                expected_start
                +
                timedelta(
                    minutes=CONSULTATION_MINUTES
                )
            )


        delay = max(
            0,
            int(
                (
                    expected_start
                    -
                    planned_datetime
                ).total_seconds()
                / 60
            )
        )


        patients_ahead = 0


        for previous in appointments:

            if previous["id"] == appointment["id"]:

                break


            if previous["status"] in [
                "waiting",
                "in_progress"
            ]:

                patients_ahead += 1


        item["expected_start_time"] = (
            format_time(expected_start)
        )

        item["calculated_delay_minutes"] = (
            delay
        )

        item["patients_ahead"] = (
            patients_ahead
        )


        item["estimated_wait_minutes"] = (

            max(
                0,
                int(
                    (
                        expected_start
                        -
                        datetime.now()
                    ).total_seconds()
                    / 60
                )
            )

            if status == "waiting"

            else 0
        )


        result.append(item)


    return result


# =========================================================
# PATIENT DASHBOARD
# =========================================================

@app.get("/patient/{patient_id}")
def patient_dashboard(
    patient_id: int
):

    conn = get_db()


    appointments = conn.execute(
        """
        SELECT *
        FROM appointments
        WHERE patient_id = ?
        ORDER BY appointment_date DESC, id DESC
        """,
        (patient_id,)
    ).fetchall()


    conn.close()


    appointment_list = [
        dict(row)
        for row in appointments
    ]


    # -----------------------------------------------------
    # FIND TODAY'S ACTIVE APPOINTMENT
    # -----------------------------------------------------

    today = datetime.now().strftime(
        "%Y-%m-%d"
    )


    today_appointments = [

        item

        for item in appointment_list

        if item["appointment_date"] == today

        and item["status"] != "cancelled"

    ]


    current_appointment = None


    if today_appointments:

        current_appointment = (
            today_appointments[0]
        )


        queue_data = get_calculated_queue(
            current_appointment[
                "department"
            ],
            today
        )


        for item in queue_data:

            if item["id"] == current_appointment["id"]:

                current_appointment = item

                break


    return {

        "appointment":
            current_appointment,

        "current_appointment":
            current_appointment,

        "today_appointment":
            current_appointment,

        "appointments":
            appointment_list,

        "my_appointments":
            appointment_list

    }


# =========================================================
# QUEUE
# =========================================================

@app.get("/queue")
def queue(
    department: str | None = None,
    appointment_date: str | None = None
):

    conn = get_db()


    if not appointment_date:

        appointment_date = (
            datetime.now()
            .strftime("%Y-%m-%d")
        )


    query = """
        SELECT *
        FROM appointments
        WHERE status != 'cancelled'
    """


    params = []


    if department:

        query += """
            AND department = ?
        """

        params.append(department)


    query += """
        AND appointment_date = ?
        ORDER BY id ASC
    """


    params.append(
        appointment_date
    )


    rows = conn.execute(
        query,
        params
    ).fetchall()


    conn.close()


    if department:

        return get_calculated_queue(
            department,
            appointment_date
        )


    return [
        dict(row)
        for row in rows
    ]


# =========================================================
# DOCTOR DASHBOARD
# =========================================================

@app.get("/doctor")
def doctor_dashboard(
    department: str | None = None
):

    today = datetime.now().strftime(
        "%Y-%m-%d"
    )


    conn = get_db()


    if department:

        rows = conn.execute(
            """
            SELECT *
            FROM appointments
            WHERE department = ?
            AND appointment_date = ?
            AND status != 'cancelled'
            ORDER BY id ASC
            """,
            (
                department,
                today
            )
        ).fetchall()

    else:

        rows = conn.execute(
            """
            SELECT *
            FROM appointments
            WHERE appointment_date = ?
            AND status != 'cancelled'
            ORDER BY id ASC
            """,
            (today,)
        ).fetchall()


    conn.close()


    if department:

        appointments = get_calculated_queue(
            department,
            today
        )

    else:

        appointments = [
            dict(row)
            for row in rows
        ]


    waiting = 0

    completed = 0

    in_progress = 0


    for row in appointments:

        if row["status"] == "waiting":

            waiting += 1

        elif row["status"] == "completed":

            completed += 1

        elif row["status"] == "in_progress":

            in_progress += 1


    return {

        "waiting":
            waiting,

        "completed":
            completed,

        "in_progress":
            in_progress,

        "total":
            len(appointments),

        "appointments":
            appointments

    }


# =========================================================
# UPDATE QUEUE
# =========================================================

@app.put("/queue/{appointment_id}")
def update_queue(
    appointment_id: int,
    data: QueueUpdateRequest
):

    allowed_status = [

        "waiting",

        "in_progress",

        "completed",

        "cancelled"

    ]


    if data.status not in allowed_status:

        raise HTTPException(
            status_code=400,
            detail="Invalid queue status"
        )


    conn = get_db()


    appointment = conn.execute(
        """
        SELECT *
        FROM appointments
        WHERE id = ?
        """,
        (appointment_id,)
    ).fetchone()


    if not appointment:

        conn.close()

        raise HTTPException(
            status_code=404,
            detail="Appointment not found"
        )


    # =====================================================
    # START PATIENT
    # =====================================================

    if data.status == "in_progress":

        active = conn.execute(
            """
            SELECT id
            FROM appointments
            WHERE department = ?
            AND appointment_date = ?
            AND status = 'in_progress'
            AND id != ?
            """,
            (
                appointment["department"],
                appointment["appointment_date"],
                appointment_id
            )
        ).fetchone()


        if active:

            conn.close()

            raise HTTPException(
                status_code=400,
                detail=
                "Another patient is currently in progress."
            )


        now = datetime.now()


        conn.execute(
            """
            UPDATE appointments

            SET status = ?,
                actual_start_time = ?,
                consultation_minutes = ?

            WHERE id = ?
            """,
            (
                "in_progress",

                format_datetime(now),

                CONSULTATION_MINUTES,

                appointment_id
            )
        )


    # =====================================================
    # COMPLETE PATIENT
    # =====================================================

    elif data.status == "completed":

        consultation = (
            data.consultation_minutes
        )


        if (
            not consultation
            or consultation <= 0
        ):

            consultation = (
                CONSULTATION_MINUTES
            )


        actual_start_value = (
            appointment[
                "actual_start_time"
            ]
        )


        if actual_start_value:

            actual_start = datetime.strptime(
                actual_start_value,
                "%Y-%m-%d %H:%M:%S"
            )

        else:

            actual_start = datetime.now()


        actual_end = (
            actual_start
            +
            timedelta(minutes=consultation)
        )


        planned_datetime = parse_planned_time(
            appointment[
                "appointment_date"
            ],
            appointment[
                "planned_time"
            ]
        )


        delay = max(
            0,
            int(
                (
                    actual_start
                    -
                    planned_datetime
                ).total_seconds()
                / 60
            )
        )


        conn.execute(
            """
            UPDATE appointments

            SET status = ?,

                actual_start_time = ?,

                actual_end_time = ?,

                consultation_minutes = ?,

                delay_minutes = ?

            WHERE id = ?
            """,
            (
                "completed",

                format_datetime(
                    actual_start
                ),

                format_datetime(
                    actual_end
                ),

                consultation,

                delay,

                appointment_id
            )
        )


    # =====================================================
    # BACK TO WAITING
    # =====================================================

    elif data.status == "waiting":

        conn.execute(
            """
            UPDATE appointments

            SET status = ?,

                actual_start_time = NULL,

                actual_end_time = NULL,

                consultation_minutes = ?,

                delay_minutes = 0

            WHERE id = ?
            """,
            (
                "waiting",

                CONSULTATION_MINUTES,

                appointment_id
            )
        )


    # =====================================================
    # CANCEL
    # =====================================================

    elif data.status == "cancelled":

        conn.execute(
            """
            UPDATE appointments

            SET status = ?

            WHERE id = ?
            """,
            (
                "cancelled",

                appointment_id
            )
        )


    conn.commit()


    department = appointment[
        "department"
    ]

    appointment_date = appointment[
        "appointment_date"
    ]


    conn.close()


    calculate_queue_times(
        department,
        appointment_date
    )


    return {

        "message":
            "Queue updated successfully",

        "status":
            data.status

    }


# =========================================================
# ADMIN ANALYTICS
# =========================================================

@app.get("/admin/analytics")
def admin_analytics():

    conn = get_db()


    total = conn.execute(
        """
        SELECT COUNT(*)
        FROM appointments
        WHERE status != 'cancelled'
        """
    ).fetchone()[0]


    waiting = conn.execute(
        """
        SELECT COUNT(*)
        FROM appointments
        WHERE status = 'waiting'
        """
    ).fetchone()[0]


    completed = conn.execute(
        """
        SELECT COUNT(*)
        FROM appointments
        WHERE status = 'completed'
        """
    ).fetchone()[0]


    cancelled = conn.execute(
        """
        SELECT COUNT(*)
        FROM appointments
        WHERE status = 'cancelled'
        """
    ).fetchone()[0]


    departments = conn.execute(
        """
        SELECT
            department,
            COUNT(*) AS total

        FROM appointments

        WHERE status != 'cancelled'

        GROUP BY department

        ORDER BY total DESC
        """
    ).fetchall()


    conn.close()


    return {

        "total_appointments":
            total,

        "waiting":
            waiting,

        "completed":
            completed,

        "cancelled":
            cancelled,

        "departments": [

            dict(row)

            for row in departments

        ]

    }


# =========================================================
# ADMIN PATIENT LIST
# =========================================================

@app.get("/admin/patients")
def admin_patients():

    conn = get_db()


    patients = conn.execute(
        """
        SELECT
            id,
            name,
            email,
            department
        FROM users
        WHERE role = 'patient'
        ORDER BY id DESC
        """
    ).fetchall()


    conn.close()


    return [
        dict(row)
        for row in patients
    ]


# =========================================================
# ADMIN DELETE PATIENT MODEL
# =========================================================

class AdminDeletePatientRequest(BaseModel):

    admin_id: int


# =========================================================
# ADMIN DELETE PATIENT
# =========================================================

@app.delete("/admin/patients/{patient_id}")
def delete_patient(
    patient_id: int,
    data: AdminDeletePatientRequest
):

    conn = get_db()


    try:

        # -------------------------------------------------
        # VERIFY ADMIN
        # -------------------------------------------------

        admin = conn.execute(
            """
            SELECT id
            FROM users
            WHERE id = ?
            AND role = 'admin'
            """,
            (data.admin_id,)
        ).fetchone()


        if not admin:

            raise HTTPException(
                status_code=403,
                detail="Only an admin can delete a patient."
            )


        # -------------------------------------------------
        # VERIFY PATIENT
        # -------------------------------------------------

        patient = conn.execute(
            """
            SELECT id, name
            FROM users
            WHERE id = ?
            AND role = 'patient'
            """,
            (patient_id,)
        ).fetchone()


        if not patient:

            raise HTTPException(
                status_code=404,
                detail="Patient account not found."
            )


        # -------------------------------------------------
        # DELETE APPOINTMENTS FIRST
        # -------------------------------------------------

        appointment_count = conn.execute(
            """
            SELECT COUNT(*)
            FROM appointments
            WHERE patient_id = ?
            """,
            (patient_id,)
        ).fetchone()[0]


        conn.execute(
            """
            DELETE FROM appointments
            WHERE patient_id = ?
            """,
            (patient_id,)
        )


        # -------------------------------------------------
        # 🚨 DELETE EMERGENCY REQUESTS
        # -------------------------------------------------

        conn.execute(
            """
            DELETE FROM emergency_requests
            WHERE patient_id = ?
            """,
            (patient_id,)
        )


        # -------------------------------------------------
        # DELETE PATIENT ACCOUNT
        # -------------------------------------------------

        conn.execute(
            """
            DELETE FROM users
            WHERE id = ?
            AND role = 'patient'
            """,
            (patient_id,)
        )


        conn.commit()


        return {

            "message":
                "Patient account deleted successfully.",

            "patient_id":
                patient_id,

            "patient_name":
                patient["name"],

            "deleted_appointments":
                appointment_count

        }


    except HTTPException:

        conn.rollback()

        raise


    except Exception as error:

        conn.rollback()

        raise HTTPException(
            status_code=500,
            detail=
            f"Unable to delete patient: {str(error)}"
        )


    finally:

        conn.close()


# =========================================================
# 🚨 EMERGENCY SUPPORT
# =========================================================
#
# IMPORTANT:
# This feature is workflow support only.
# It does NOT diagnose patients and does NOT autonomously
# decide medical priority.
#
# Hospital staff / doctors make the final clinical decision.
# For life-threatening emergencies, contact local emergency
# services immediately.
# =========================================================


EMERGENCY_TYPES = [

    "Breathing difficulty",

    "Chest pain",

    "Severe bleeding",

    "Accident / injury",

    "Loss of consciousness",

    "Severe pain",

    "Other emergency"

]


EMERGENCY_STATUSES = [

    "requested",

    "acknowledged",

    "in_progress",

    "resolved",

    "cancelled"

]


# =========================================================
# EMERGENCY TOKEN
# =========================================================

def generate_emergency_token(
    conn
):

    today = datetime.now().strftime(
        "%Y%m%d"
    )


    prefix = f"ER-{today}-"


    rows = conn.execute(
        """
        SELECT token
        FROM emergency_requests
        WHERE token LIKE ?
        ORDER BY id DESC
        """,
        (
            f"{prefix}%"
        )
    ).fetchall()


    max_number = 0


    for row in rows:

        token = row["token"]


        if not token:

            continue


        try:

            number = int(
                token.split("-")[-1]
            )

            max_number = max(
                max_number,
                number
            )

        except ValueError:

            pass


    return (
        f"{prefix}"
        f"{max_number + 1:03d}"
    )


# =========================================================
# CREATE EMERGENCY REQUEST
# =========================================================

@app.post("/emergency")
def create_emergency(
    data: EmergencyRequest
):

    # -----------------------------------------------------
    # CHECK EMERGENCY TYPE
    # -----------------------------------------------------

    if data.emergency_type not in EMERGENCY_TYPES:

        raise HTTPException(
            status_code=400,
            detail="Invalid emergency type."
        )


    # -----------------------------------------------------
    # CHECK DEPARTMENT
    # -----------------------------------------------------

    if data.department not in DEPARTMENT_SCHEDULE:

        raise HTTPException(
            status_code=400,
            detail="Invalid department."
        )


    conn = get_db()


    try:

        # -------------------------------------------------
        # CHECK PATIENT
        # -------------------------------------------------

        patient = conn.execute(
            """
            SELECT *
            FROM users
            WHERE id = ?
            AND role = 'patient'
            """,
            (data.patient_id,)
        ).fetchone()


        if not patient:

            raise HTTPException(
                status_code=404,
                detail="Patient account not found."
            )


        # -------------------------------------------------
        # ONE ACTIVE EMERGENCY PER PATIENT
        # -------------------------------------------------

        active_emergency = conn.execute(
            """
            SELECT *
            FROM emergency_requests
            WHERE patient_id = ?
            AND status IN (
                'requested',
                'acknowledged',
                'in_progress'
            )
            ORDER BY id DESC
            LIMIT 1
            """,
            (data.patient_id,)
        ).fetchone()


        if active_emergency:

            raise HTTPException(
                status_code=400,
                detail=
                "You already have an active emergency request."
            )


        # -------------------------------------------------
        # DOCTOR
        # -------------------------------------------------

        doctor = DEPARTMENT_SCHEDULE[
            data.department
        ]["doctor"]


        # -------------------------------------------------
        # CREATED TIME
        # -------------------------------------------------

        now = datetime.now()


        # -------------------------------------------------
        # EMERGENCY TOKEN
        # -------------------------------------------------

        token = generate_emergency_token(
            conn
        )


        # -------------------------------------------------
        # SAVE EMERGENCY
        # -------------------------------------------------

        cursor = conn.execute(
            """
            INSERT INTO emergency_requests
            (
                patient_id,
                patient_name,
                emergency_type,
                description,
                location,
                emergency_contact,
                department,
                doctor,
                status,
                token,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                data.patient_id,

                patient["name"],

                data.emergency_type,

                data.description,

                data.location,

                data.emergency_contact,

                data.department,

                doctor,

                "requested",

                token,

                format_datetime(now)
            )
        )


        conn.commit()


        emergency_id = cursor.lastrowid


        return {

            "message":
                "Emergency request submitted successfully.",

            "emergency": {

                "id":
                    emergency_id,

                "patient_id":
                    data.patient_id,

                "patient_name":
                    patient["name"],

                "emergency_type":
                    data.emergency_type,

                "description":
                    data.description,

                "location":
                    data.location,

                "emergency_contact":
                    data.emergency_contact,

                "department":
                    data.department,

                "doctor":
                    doctor,

                "status":
                    "requested",

                "token":
                    token,

                "created_at":
                    format_datetime(now)

            }

        }


    except HTTPException:

        conn.rollback()

        raise


    except sqlite3.IntegrityError:

        conn.rollback()

        raise HTTPException(
            status_code=500,
            detail=
            "Unable to create emergency request."
        )


    except Exception as error:

        conn.rollback()

        raise HTTPException(
            status_code=500,
            detail=
            f"Unable to create emergency request: {str(error)}"
        )


    finally:

        conn.close()


# =========================================================
# GET PATIENT EMERGENCY REQUESTS
# =========================================================

@app.get("/emergency/patient/{patient_id}")
def patient_emergencies(
    patient_id: int
):

    conn = get_db()


    # -----------------------------------------------------
    # CHECK PATIENT
    # -----------------------------------------------------

    patient = conn.execute(
        """
        SELECT id
        FROM users
        WHERE id = ?
        AND role = 'patient'
        """,
        (patient_id,)
    ).fetchone()


    if not patient:

        conn.close()

        raise HTTPException(
            status_code=404,
            detail="Patient account not found."
        )


    emergencies = conn.execute(
        """
        SELECT *
        FROM emergency_requests
        WHERE patient_id = ?
        ORDER BY id DESC
        """,
        (patient_id,)
    ).fetchall()


    conn.close()


    return [
        dict(row)
        for row in emergencies
    ]


# =========================================================
# GET EMERGENCY QUEUE
# =========================================================
#
# Used by doctor/staff dashboard.
#
# Optional department filter:
#
# /emergency?department=Cardiology
#
# Without department:
#
# /emergency
#
# returns today's emergency requests.
# =========================================================

@app.get("/emergency")
def emergency_queue(
    department: str | None = None
):

    today = datetime.now().strftime(
        "%Y-%m-%d"
    )


    conn = get_db()


    if department:

        if department not in DEPARTMENT_SCHEDULE:

            conn.close()

            raise HTTPException(
                status_code=400,
                detail="Invalid department."
            )


        emergencies = conn.execute(
            """
            SELECT *
            FROM emergency_requests
            WHERE department = ?
            AND date(created_at) = ?
            ORDER BY
                CASE status
                    WHEN 'requested' THEN 1
                    WHEN 'acknowledged' THEN 2
                    WHEN 'in_progress' THEN 3
                    WHEN 'resolved' THEN 4
                    WHEN 'cancelled' THEN 5
                    ELSE 6
                END,
                id ASC
            """,
            (
                department,
                today
            )
        ).fetchall()

    else:

        emergencies = conn.execute(
            """
            SELECT *
            FROM emergency_requests
            WHERE date(created_at) = ?
            ORDER BY
                CASE status
                    WHEN 'requested' THEN 1
                    WHEN 'acknowledged' THEN 2
                    WHEN 'in_progress' THEN 3
                    WHEN 'resolved' THEN 4
                    WHEN 'cancelled' THEN 5
                    ELSE 6
                END,
                id ASC
            """,
            (today,)
        ).fetchall()


    conn.close()


    return [
        dict(row)
        for row in emergencies
    ]


# =========================================================
# UPDATE EMERGENCY STATUS
# =========================================================

@app.put("/emergency/{emergency_id}")
def update_emergency(
    emergency_id: int,
    data: EmergencyStatusRequest
):

    if data.status not in EMERGENCY_STATUSES:

        raise HTTPException(
            status_code=400,
            detail="Invalid emergency status."
        )


    conn = get_db()


    try:

        emergency = conn.execute(
            """
            SELECT *
            FROM emergency_requests
            WHERE id = ?
            """,
            (emergency_id,)
        ).fetchone()


        if not emergency:

            raise HTTPException(
                status_code=404,
                detail="Emergency request not found."
            )


        now = datetime.now()


        # =================================================
        # REQUESTED
        # =================================================

        if data.status == "requested":

            conn.execute(
                """
                UPDATE emergency_requests

                SET status = ?

                WHERE id = ?
                """,
                (
                    "requested",

                    emergency_id
                )
            )


        # =================================================
        # ACKNOWLEDGED
        # =================================================

        elif data.status == "acknowledged":

            acknowledged_at = (
                emergency["acknowledged_at"]
            )


            if not acknowledged_at:

                acknowledged_at = (
                    format_datetime(now)
                )


            conn.execute(
                """
                UPDATE emergency_requests

                SET status = ?,
                    acknowledged_at = ?

                WHERE id = ?
                """,
                (
                    "acknowledged",

                    acknowledged_at,

                    emergency_id
                )
            )


        # =================================================
        # IN PROGRESS
        # =================================================

        elif data.status == "in_progress":

            actual_start_time = (
                emergency[
                    "actual_start_time"
                ]
            )


            if not actual_start_time:

                actual_start_time = (
                    format_datetime(now)
                )


            acknowledged_at = (
                emergency["acknowledged_at"]
            )


            if not acknowledged_at:

                acknowledged_at = (
                    format_datetime(now)
                )


            conn.execute(
                """
                UPDATE emergency_requests

                SET status = ?,

                    acknowledged_at = ?,

                    actual_start_time = ?

                WHERE id = ?
                """,
                (
                    "in_progress",

                    acknowledged_at,

                    actual_start_time,

                    emergency_id
                )
            )


        # =================================================
        # RESOLVED
        # =================================================

        elif data.status == "resolved":

            resolved_at = (
                format_datetime(now)
            )


            response_minutes = (
                emergency["response_minutes"]
            )


            # -------------------------------------------------
            # Response time = acknowledged/start/resolution
            # from original emergency request.
            # -------------------------------------------------

            start_reference = (
                emergency["actual_start_time"]
                or
                emergency["acknowledged_at"]
                or
                emergency["created_at"]
            )


            if start_reference:

                try:

                    start_time = datetime.strptime(
                        start_reference,
                        "%Y-%m-%d %H:%M:%S"
                    )


                    response_minutes = max(
                        0,
                        int(
                            (
                                now
                                -
                                start_time
                            ).total_seconds()
                            / 60
                        )
                    )

                except ValueError:

                    pass


            conn.execute(
                """
                UPDATE emergency_requests

                SET status = ?,

                    resolved_at = ?,

                    response_minutes = ?

                WHERE id = ?
                """,
                (
                    "resolved",

                    resolved_at,

                    response_minutes,

                    emergency_id
                )
            )


        # =================================================
        # CANCELLED
        # =================================================

        elif data.status == "cancelled":

            conn.execute(
                """
                UPDATE emergency_requests

                SET status = ?

                WHERE id = ?
                """,
                (
                    "cancelled",

                    emergency_id
                )
            )


        conn.commit()


        updated = conn.execute(
            """
            SELECT *
            FROM emergency_requests
            WHERE id = ?
            """,
            (emergency_id,)
        ).fetchone()


        return {

            "message":
                "Emergency status updated successfully.",

            "emergency":
                dict(updated)

        }


    except HTTPException:

        conn.rollback()

        raise


    except Exception as error:

        conn.rollback()

        raise HTTPException(
            status_code=500,
            detail=
            f"Unable to update emergency: {str(error)}"
        )


    finally:

        conn.close()


# =========================================================
# ADMIN EMERGENCY MANAGEMENT
# =========================================================

@app.get("/admin/emergencies")
def admin_emergencies():

    conn = get_db()


    emergencies = conn.execute(
        """
        SELECT *
        FROM emergency_requests
        ORDER BY id DESC
        """
    ).fetchall()


    conn.close()


    return [
        dict(row)
        for row in emergencies
    ]


# =========================================================
# ADMIN EMERGENCY ANALYTICS
# =========================================================

@app.get("/admin/emergency-analytics")
def admin_emergency_analytics():

    conn = get_db()


    total = conn.execute(
        """
        SELECT COUNT(*)
        FROM emergency_requests
        """
    ).fetchone()[0]


    active = conn.execute(
        """
        SELECT COUNT(*)
        FROM emergency_requests
        WHERE status IN (
            'requested',
            'acknowledged',
            'in_progress'
        )
        """
    ).fetchone()[0]


    resolved = conn.execute(
        """
        SELECT COUNT(*)
        FROM emergency_requests
        WHERE status = 'resolved'
        """
    ).fetchone()[0]


    cancelled = conn.execute(
        """
        SELECT COUNT(*)
        FROM emergency_requests
        WHERE status = 'cancelled'
        """
    ).fetchone()[0]


    average_response = conn.execute(
        """
        SELECT AVG(response_minutes)
        FROM emergency_requests
        WHERE response_minutes IS NOT NULL
        """
    ).fetchone()[0]


    departments = conn.execute(
        """
        SELECT
            department,
            COUNT(*) AS total
        FROM emergency_requests
        GROUP BY department
        ORDER BY total DESC
        """
    ).fetchall()


    emergency_types = conn.execute(
        """
        SELECT
            emergency_type,
            COUNT(*) AS total
        FROM emergency_requests
        GROUP BY emergency_type
        ORDER BY total DESC
        """
    ).fetchall()


    conn.close()


    return {

        "total_emergencies":
            total,

        "active":
            active,

        "resolved":
            resolved,

        "cancelled":
            cancelled,

        "average_response_minutes":
            round(
                average_response,
                2
            )
            if average_response is not None
            else 0,

        "departments": [

            dict(row)

            for row in departments

        ],

        "emergency_types": [

            dict(row)

            for row in emergency_types

        ]

    }


# =========================================================
# SERVER
# =========================================================

if __name__ == "__main__":

    import uvicorn

    uvicorn.run(
        app,
        host="127.0.0.1",
        port=8000
    )