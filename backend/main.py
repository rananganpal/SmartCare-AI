from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime, date, timedelta
import sqlite3
import os

try:
    import psycopg2
    from psycopg2.extras import DictCursor
except ImportError:
    psycopg2 = None
    DictCursor = None


# =========================================================
# APP CONFIGURATION
# =========================================================

app = FastAPI(title="SmartCare AI")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "smartcare.db")
DATABASE_URL = os.getenv("DATABASE_URL")
USE_POSTGRES = bool(DATABASE_URL)


# =========================================================
# QUEUE SETTINGS
# =========================================================

CONSULTATION_MINUTES = 10

# Every doctor session is 3 hours
SESSION_MINUTES = 180

# 3 hours / 10 minutes = 18 patients
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
# DATABASE
# =========================================================

class PostgreSQLConnection:
    """Small compatibility layer so existing SQLite-style SQL keeps working."""

    def __init__(self, connection):
        self.connection = connection

    def execute(self, query, params=None):
        # The existing SmartCare code uses SQLite's '?' placeholders.
        # PostgreSQL/psycopg2 uses '%s', so translate only for PostgreSQL.
        query = query.replace("?", "%s")
        cursor = self.connection.cursor()
        cursor.execute(query, params or ())
        return cursor

    def commit(self):
        self.connection.commit()

    def rollback(self):
        self.connection.rollback()

    def close(self):
        self.connection.close()


def get_db():
    # Render uses PostgreSQL when DATABASE_URL is configured.
    # Local VS Code development keeps using SQLite when DATABASE_URL is absent.
    if USE_POSTGRES:
        if psycopg2 is None:
            raise RuntimeError(
                "psycopg2-binary is required when DATABASE_URL is configured."
            )

        return PostgreSQLConnection(
            psycopg2.connect(
                DATABASE_URL,
                cursor_factory=DictCursor
            )
        )

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def column_exists(conn, table_name, column_name):
    if USE_POSTGRES:
        cursor = conn.execute("""
            SELECT 1
            FROM information_schema.columns
            WHERE table_schema = 'public'
            AND table_name = %s
            AND column_name = %s
        """, (table_name, column_name))
        return cursor.fetchone() is not None

    cursor = conn.execute(f"PRAGMA table_info({table_name})")
    columns = [row["name"] for row in cursor.fetchall()]
    return column_name in columns


def add_column_if_missing(conn, table_name, column_name, column_type):
    if not column_exists(conn, table_name, column_name):
        conn.execute(
            f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}"
        )


def init_db():

    conn = get_db()

    # -----------------------------------------------------
    # USERS TABLE
    # -----------------------------------------------------

    if USE_POSTGRES:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
                name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                role TEXT NOT NULL,
                department TEXT
            )
        """)
    else:
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
    # APPOINTMENTS TABLE
    # -----------------------------------------------------

    if USE_POSTGRES:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS appointments (
                id INTEGER GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
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
    else:
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
    # OLD DATABASE MIGRATION
    # -----------------------------------------------------

    add_column_if_missing(
        conn, "users", "department", "TEXT"
    )

    add_column_if_missing(
        conn, "appointments", "patient_name", "TEXT"
    )

    add_column_if_missing(
        conn, "appointments", "appointment_date", "TEXT"
    )

    add_column_if_missing(
        conn, "appointments", "time", "TEXT"
    )

    add_column_if_missing(
        conn, "appointments", "token", "TEXT"
    )

    add_column_if_missing(
        conn, "appointments", "status", "TEXT DEFAULT 'waiting'"
    )

    add_column_if_missing(
        conn, "appointments", "doctor", "TEXT"
    )

    add_column_if_missing(
        conn, "appointments", "planned_time", "TEXT"
    )

    add_column_if_missing(
        conn, "appointments", "actual_start_time", "TEXT"
    )

    add_column_if_missing(
        conn, "appointments", "actual_end_time", "TEXT"
    )

    add_column_if_missing(
        conn, "appointments", "consultation_minutes", "INTEGER DEFAULT 10"
    )

    add_column_if_missing(
        conn, "appointments", "delay_minutes", "INTEGER DEFAULT 0"
    )

    # -----------------------------------------------------
    # EMERGENCY REQUESTS TABLE
    # This is separate from normal appointments so the
    # existing appointment/queue system remains unchanged.
    # -----------------------------------------------------

    if USE_POSTGRES:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS emergency_requests (
                id INTEGER GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
                patient_id INTEGER NOT NULL,
                patient_name TEXT NOT NULL,
                emergency_type TEXT NOT NULL,
                description TEXT,
                location TEXT,
                emergency_contact TEXT,
                department TEXT NOT NULL,
                doctor TEXT NOT NULL,
                token TEXT UNIQUE NOT NULL,
                status TEXT DEFAULT 'requested',
                created_at TEXT NOT NULL,
                acknowledged_at TEXT,
                actual_start_time TEXT,
                resolved_at TEXT,
                response_minutes INTEGER
            )
        """)
    else:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS emergency_requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                patient_id INTEGER NOT NULL,
                patient_name TEXT NOT NULL,
                emergency_type TEXT NOT NULL,
                description TEXT,
                location TEXT,
                emergency_contact TEXT,
                department TEXT NOT NULL,
                doctor TEXT NOT NULL,
                token TEXT UNIQUE NOT NULL,
                status TEXT DEFAULT 'requested',
                created_at TEXT NOT NULL,
                acknowledged_at TEXT,
                actual_start_time TEXT,
                resolved_at TEXT,
                response_minutes INTEGER
            )
        """)

    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_emergency_department_status
        ON emergency_requests(department, status)
    """)

    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_emergency_patient
        ON emergency_requests(patient_id)
    """)

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
            "SELECT id FROM users WHERE email = ?",
            (user[1],)
        ).fetchone()

        if not existing:

            conn.execute("""
                INSERT INTO users
                (name, email, password, role, department)
                VALUES (?, ?, ?, ?, ?)
            """, user)

    conn.commit()
    conn.close()


def migrate_sqlite_to_postgres():
    """
    One-time best-effort migration of the existing local/Render SQLite file
    into PostgreSQL. Existing PostgreSQL rows are never overwritten.
    """

    if not USE_POSTGRES or not os.path.exists(DB_PATH):
        return

    pg = get_db()
    sqlite_conn = None

    try:
        user_count = pg.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        appointment_count = pg.execute("SELECT COUNT(*) FROM appointments").fetchone()[0]
        emergency_count = pg.execute("SELECT COUNT(*) FROM emergency_requests").fetchone()[0]

        # init_db creates the three demo accounts before this migration runs.
        # If PostgreSQL contains only those demo accounts and no application
        # data yet, continue so existing SQLite application data can be copied.
        if appointment_count > 0 or emergency_count > 0 or user_count > 3:
            return

        sqlite_conn = sqlite3.connect(DB_PATH)
        sqlite_conn.row_factory = sqlite3.Row

        tables = [
            "users",
            "appointments",
            "emergency_requests"
        ]

        for table in tables:
            exists = sqlite_conn.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table' AND name = ?",
                (table,)
            ).fetchone()

            if not exists:
                continue

            sqlite_columns = [
                row["name"]
                for row in sqlite_conn.execute(f"PRAGMA table_info({table})").fetchall()
            ]

            pg_columns = [
                row["column_name"]
                for row in pg.execute("""
                    SELECT column_name
                    FROM information_schema.columns
                    WHERE table_schema = 'public'
                    AND table_name = %s
                    ORDER BY ordinal_position
                """, (table,)).fetchall()
            ]

            columns = [column for column in sqlite_columns if column in pg_columns]
            if not columns:
                continue

            rows = sqlite_conn.execute(
                f"SELECT {', '.join(columns)} FROM {table}"
            ).fetchall()

            if not rows:
                continue

            column_sql = ", ".join(columns)
            placeholders = ", ".join(["%s"] * len(columns))

            for row in rows:
                values = [row[column] for column in columns]
                pg.execute(
                    f"INSERT INTO {table} ({column_sql}) VALUES ({placeholders}) ON CONFLICT DO NOTHING",
                    values
                )

        # Keep identity sequences ahead of imported IDs.
        for table in tables:
            pg.execute(f"""
                SELECT setval(
                    pg_get_serial_sequence('{table}', 'id'),
                    COALESCE((SELECT MAX(id) FROM {table}), 1),
                    true
                )
            """)

        pg.commit()
        print("SQLite data migration to PostgreSQL completed.")

    except Exception as error:
        pg.rollback()
        print("SQLite to PostgreSQL migration skipped:", error)

    finally:
        if sqlite_conn:
            sqlite_conn.close()
        pg.close()


init_db()

migrate_sqlite_to_postgres()


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


class AdminDeletePatientRequest(BaseModel):
    admin_id: int


class EmergencyRequest(BaseModel):
    patient_id: int
    emergency_type: str
    description: str | None = None
    location: str | None = None
    emergency_contact: str | None = None
    department: str


class EmergencyStatusRequest(BaseModel):
    status: str


# =========================================================
# HELPER FUNCTIONS
# =========================================================

def get_session_start(department):

    if department not in DEPARTMENT_SCHEDULE:
        raise HTTPException(
            status_code=400,
            detail="Invalid department"
        )

    return DEPARTMENT_SCHEDULE[department]["start"]


def get_session_end(department):

    if department not in DEPARTMENT_SCHEDULE:
        raise HTTPException(
            status_code=400,
            detail="Invalid department"
        )

    return DEPARTMENT_SCHEDULE[department]["end"]


def convert_time_to_datetime(date_string, time_string):

    return datetime.strptime(
        f"{date_string} {time_string}",
        "%Y-%m-%d %H:%M"
    )


def format_time(dt):

    return dt.strftime("%I:%M %p")


def format_datetime(dt):

    return dt.strftime("%Y-%m-%d %H:%M:%S")


# =========================================================
# ROOT
# =========================================================

@app.get("/")
def home():

    return {
        "message": "SmartCare AI Backend Running",
        "consultation_minutes": CONSULTATION_MINUTES,
        "session_minutes": SESSION_MINUTES,
        "max_patients": MAX_PATIENTS
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
            "session_minutes": SESSION_MINUTES,
            "max_patients": MAX_PATIENTS
        })

    return result


# =========================================================
# REGISTER
# =========================================================

@app.post("/register")
def register(data: RegisterRequest):

    conn = get_db()

    existing = conn.execute(
        "SELECT id FROM users WHERE email = ?",
        (data.email,)
    ).fetchone()

    if existing:

        conn.close()

        raise HTTPException(
            status_code=400,
            detail="Account already exists. Please login."
        )

    role = data.role.lower()

    if role not in ["patient", "doctor"]:

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
                detail="Doctor department is required"
            )

        if department not in DEPARTMENT_SCHEDULE:
            conn.close()

            raise HTTPException(
                status_code=400,
                detail="Invalid department"
            )

    else:
        department = None

    if USE_POSTGRES:
        cursor = conn.execute("""
            INSERT INTO users
            (name, email, password, role, department)
            VALUES (?, ?, ?, ?, ?)
            RETURNING id
        """, (
            data.name,
            data.email,
            data.password,
            role,
            department
        ))
        user_id = cursor.fetchone()[0]
    else:
        cursor = conn.execute("""
            INSERT INTO users
            (name, email, password, role, department)
            VALUES (?, ?, ?, ?, ?)
        """, (
            data.name,
            data.email,
            data.password,
            role,
            department
        ))
        user_id = cursor.lastrowid

    conn.commit()

    conn.close()

    return {
        "message": "Account created successfully",
        "user": {
            "id": user_id,
            "name": data.name,
            "email": data.email,
            "role": role,
            "department": department
        }
    }


# =========================================================
# LOGIN
# =========================================================

@app.post("/login")
def login(data: LoginRequest):

    conn = get_db()

    user = conn.execute("""
        SELECT *
        FROM users
        WHERE email = ?
    """, (data.email,)).fetchone()

    conn.close()

    if not user:

        raise HTTPException(
            status_code=404,
            detail="Account not found. Please create an account first."
        )

    if user["password"] != data.password:

        raise HTTPException(
            status_code=401,
            detail="Incorrect password"
        )

    return {
        "message": "Login successful",
        "user": {
            "id": user["id"],
            "name": user["name"],
            "email": user["email"],
            "role": user["role"],
            "department": user["department"]
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

    booked = conn.execute("""
        SELECT COUNT(*) AS total
        FROM appointments
        WHERE department = ?
        AND appointment_date = ?
        AND status != 'cancelled'
    """, (
        department,
        date
    )).fetchone()["total"]

    conn.close()

    if booked >= MAX_PATIENTS:

        return {
            "available": False,
            "message": "All 18 patient slots are already booked."
        }

    start_time = get_session_start(department)

    base_datetime = convert_time_to_datetime(
        date,
        start_time
    )

    slots = []

    # Give the next few available 10-minute slots
    for i in range(booked, min(booked + 5, MAX_PATIENTS)):

        slot_datetime = base_datetime + timedelta(
            minutes=i * CONSULTATION_MINUTES
        )

        slots.append({
            "time": format_time(slot_datetime),
            "wait_minutes": i * CONSULTATION_MINUTES
        })

    return {
        "available": True,
        "department": department,
        "doctor": DEPARTMENT_SCHEDULE[department]["doctor"],
        "session_start": DEPARTMENT_SCHEDULE[department]["start"],
        "session_end": DEPARTMENT_SCHEDULE[department]["end"],
        "max_patients": MAX_PATIENTS,
        "consultation_minutes": CONSULTATION_MINUTES,
        "booked_patients": booked,
        "remaining_patients": MAX_PATIENTS - booked,
        "slots": slots
    }


# =========================================================
# CREATE APPOINTMENT
# =========================================================

@app.post("/appointments")
def create_appointment(data: AppointmentRequest):

    if data.department not in DEPARTMENT_SCHEDULE:

        raise HTTPException(
            status_code=400,
            detail="Invalid department"
        )

    conn = get_db()

    # -----------------------------------------------------
    # CHECK PATIENT
    # -----------------------------------------------------

    patient = conn.execute("""
        SELECT *
        FROM users
        WHERE id = ?
        AND role = 'patient'
    """, (
        data.patient_id,
    )).fetchone()

    if not patient:

        conn.close()

        raise HTTPException(
            status_code=404,
            detail="Patient account not found"
        )

    # -----------------------------------------------------
    # COUNT PATIENTS
    # -----------------------------------------------------

    booked_count = conn.execute("""
        SELECT COUNT(*) AS total
        FROM appointments
        WHERE department = ?
        AND appointment_date = ?
        AND status != 'cancelled'
    """, (
        data.department,
        data.date
    )).fetchone()["total"]

    # -----------------------------------------------------
    # MAXIMUM 18 PATIENTS
    # -----------------------------------------------------

    if booked_count >= MAX_PATIENTS:

        conn.close()

        raise HTTPException(
            status_code=400,
            detail="This department has reached its maximum of 18 patients for this session."
        )

    # -----------------------------------------------------
    # GET DOCTOR
    # -----------------------------------------------------

    doctor = DEPARTMENT_SCHEDULE[data.department]["doctor"]

    # -----------------------------------------------------
    # TOKEN
    # -----------------------------------------------------

    token_number = booked_count + 1

    token = f"{data.department[0].upper()}-{token_number:02d}"

    # -----------------------------------------------------
    # PLANNED TIME
    # -----------------------------------------------------

    session_start = get_session_start(data.department)

    start_datetime = convert_time_to_datetime(
        data.date,
        session_start
    )

    planned_datetime = start_datetime + timedelta(
        minutes=(token_number - 1) * CONSULTATION_MINUTES
    )

    planned_time = format_time(planned_datetime)

    # -----------------------------------------------------
    # SAVE APPOINTMENT
    # -----------------------------------------------------

    if USE_POSTGRES:
        cursor = conn.execute("""
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
            RETURNING id
        """, (
            data.patient_id,
            patient["name"],
            data.department,
            doctor,
            data.date,
            data.time,
            token,
            planned_time,
            None,
            None,
            CONSULTATION_MINUTES,
            0,
            "waiting"
        ))
        appointment_id = cursor.fetchone()[0]
    else:
        cursor = conn.execute("""
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
        """, (
            data.patient_id,
            patient["name"],
            data.department,
            doctor,
            data.date,
            data.time,
            token,
            planned_time,
            None,
            None,
            CONSULTATION_MINUTES,
            0,
            "waiting"
        ))
        appointment_id = cursor.lastrowid

    conn.commit()

    conn.close()

    return {
        "message": "Appointment booked successfully",

        "appointment": {
            "id": appointment_id,
            "patient_id": data.patient_id,
            "patient_name": patient["name"],
            "department": data.department,
            "doctor": doctor,
            "date": data.date,
            "time": planned_time,
            "token": token,
            "planned_time": planned_time,
            "consultation_minutes": CONSULTATION_MINUTES,
            "status": "waiting"
        }
    }


# =========================================================
# CALCULATE QUEUE TIMES
# =========================================================

def calculate_queue_times(department, appointment_date):

    conn = get_db()

    appointments = conn.execute("""
        SELECT *
        FROM appointments
        WHERE department = ?
        AND appointment_date = ?
        AND status != 'cancelled'
        ORDER BY id ASC
    """, (
        department,
        appointment_date
    )).fetchall()

    if not appointments:

        conn.close()
        return

    session_start = convert_time_to_datetime(
        appointment_date,
        get_session_start(department)
    )

    previous_end = session_start

    for appointment in appointments:

        appointment_id = appointment["id"]
        status = appointment["status"]

        # -------------------------------------------------
        # COMPLETED PATIENT
        # -------------------------------------------------

        if status == "completed":

            if appointment["actual_start_time"]:

                actual_start = datetime.strptime(
                    appointment["actual_start_time"],
                    "%Y-%m-%d %H:%M:%S"
                )

            else:

                actual_start = previous_end

            consultation = appointment["consultation_minutes"]

            if not consultation or consultation <= 0:
                consultation = CONSULTATION_MINUTES

            actual_end = actual_start + timedelta(
                minutes=consultation
            )

            delay = max(
                0,
                int(
                    (
                        actual_start -
                        convert_time_to_datetime(
                            appointment_date,
                            appointment["planned_time"]
                        )
                    ).total_seconds() / 60
                )
            )

            conn.execute("""
                UPDATE appointments
                SET actual_start_time = ?,
                    actual_end_time = ?,
                    delay_minutes = ?
                WHERE id = ?
            """, (
                format_datetime(actual_start),
                format_datetime(actual_end),
                delay,
                appointment_id
            ))

            previous_end = actual_end

        # -------------------------------------------------
        # IN PROGRESS
        # -------------------------------------------------

        elif status == "in_progress":

            if appointment["actual_start_time"]:

                actual_start = datetime.strptime(
                    appointment["actual_start_time"],
                    "%Y-%m-%d %H:%M:%S"
                )

            else:

                actual_start = previous_end

                conn.execute("""
                    UPDATE appointments
                    SET actual_start_time = ?
                    WHERE id = ?
                """, (
                    format_datetime(actual_start),
                    appointment_id
                ))

            consultation = appointment["consultation_minutes"]

            if not consultation or consultation <= 0:
                consultation = CONSULTATION_MINUTES

            expected_end = actual_start + timedelta(
                minutes=consultation
            )

            previous_end = expected_end

        # -------------------------------------------------
        # WAITING
        # -------------------------------------------------

        else:

            planned = datetime.strptime(
                f"{appointment_date} {appointment['planned_time']}",
                "%Y-%m-%d %I:%M %p"
            )

            # If previous patient is delayed,
            # next patient starts after previous patient.
            actual_start = max(
                planned,
                previous_end
            )

            delay = max(
                0,
                int(
                    (
                        actual_start - planned
                    ).total_seconds() / 60
                )
            )

            conn.execute("""
                UPDATE appointments
                SET delay_minutes = ?
                WHERE id = ?
            """, (
                delay,
                appointment_id
            ))

            previous_end = actual_start + timedelta(
                minutes=CONSULTATION_MINUTES
            )

    conn.commit()
    conn.close()


# =========================================================
# PATIENT DASHBOARD
# =========================================================

@app.get("/patient/{patient_id}")
def patient_dashboard(patient_id: int):

    conn = get_db()

    appointments = conn.execute("""
        SELECT *
        FROM appointments
        WHERE patient_id = ?
        ORDER BY id DESC
    """, (
        patient_id,
    )).fetchall()

    conn.close()

    return [
        dict(appointment)
        for appointment in appointments
    ]


# =========================================================
# QUEUE
# =========================================================

@app.get("/queue")
def queue(
    department: str | None = None,
    appointment_date: str | None = None
):

    conn = get_db()

    query = """
        SELECT *
        FROM appointments
        WHERE status != 'cancelled'
    """

    params = []

    if department:

        query += " AND department = ?"
        params.append(department)

    if appointment_date:

        query += " AND appointment_date = ?"
        params.append(appointment_date)

    query += " ORDER BY id ASC"

    rows = conn.execute(
        query,
        params
    ).fetchall()

    conn.close()

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

    conn = get_db()

    if department:

        rows = conn.execute("""
            SELECT *
            FROM appointments
            WHERE department = ?
            AND status != 'cancelled'
            ORDER BY id ASC
        """, (
            department,
        )).fetchall()

    else:

        rows = conn.execute("""
            SELECT *
            FROM appointments
            WHERE status != 'cancelled'
            ORDER BY id ASC
        """).fetchall()

    conn.close()

    waiting = 0
    completed = 0
    in_progress = 0

    for row in rows:

        if row["status"] == "waiting":
            waiting += 1

        elif row["status"] == "completed":
            completed += 1

        elif row["status"] == "in_progress":
            in_progress += 1

    return {
        "waiting": waiting,
        "completed": completed,
        "in_progress": in_progress,
        "total": len(rows),
        "appointments": [
            dict(row)
            for row in rows
        ]
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

    appointment = conn.execute("""
        SELECT *
        FROM appointments
        WHERE id = ?
    """, (
        appointment_id,
    )).fetchone()

    if not appointment:

        conn.close()

        raise HTTPException(
            status_code=404,
            detail="Appointment not found"
        )

    # -----------------------------------------------------
    # START PATIENT
    # -----------------------------------------------------

    if data.status == "in_progress":

        now = datetime.now()

        conn.execute("""
            UPDATE appointments
            SET status = ?,
                actual_start_time = ?
            WHERE id = ?
        """, (
            "in_progress",
            format_datetime(now),
            appointment_id
        ))

    # -----------------------------------------------------
    # COMPLETE PATIENT
    # -----------------------------------------------------

    elif data.status == "completed":

        consultation = data.consultation_minutes

        if not consultation or consultation <= 0:

            consultation = CONSULTATION_MINUTES

        actual_start = appointment["actual_start_time"]

        if actual_start:

            start_datetime = datetime.strptime(
                actual_start,
                "%Y-%m-%d %H:%M:%S"
            )

        else:

            start_datetime = datetime.now()

        actual_end = start_datetime + timedelta(
            minutes=consultation
        )

        planned_datetime = convert_time_to_datetime(
            appointment["appointment_date"],
            datetime.strptime(
                appointment["planned_time"],
                "%I:%M %p"
            ).strftime("%H:%M")
        )

        delay = max(
            0,
            int(
                (
                    start_datetime -
                    planned_datetime
                ).total_seconds() / 60
            )
        )

        conn.execute("""
            UPDATE appointments
            SET status = ?,
                actual_end_time = ?,
                consultation_minutes = ?,
                delay_minutes = ?
            WHERE id = ?
        """, (
            "completed",
            format_datetime(actual_end),
            consultation,
            delay,
            appointment_id
        ))

    # -----------------------------------------------------
    # WAITING
    # -----------------------------------------------------

    elif data.status == "waiting":

        conn.execute("""
            UPDATE appointments
            SET status = ?,
                actual_start_time = NULL,
                actual_end_time = NULL
            WHERE id = ?
        """, (
            "waiting",
            appointment_id
        ))

    # -----------------------------------------------------
    # CANCELLED
    # -----------------------------------------------------

    elif data.status == "cancelled":

        conn.execute("""
            UPDATE appointments
            SET status = ?
            WHERE id = ?
        """, (
            "cancelled",
            appointment_id
        ))

    conn.commit()

    department = appointment["department"]
    appointment_date = appointment["appointment_date"]

    conn.close()

    # Recalculate queue after update
    calculate_queue_times(
        department,
        appointment_date
    )

    return {
        "message": "Queue updated successfully",
        "status": data.status
    }


# =========================================================
# EMERGENCY SUPPORT SYSTEM
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


def emergency_token(conn):
    today_prefix = datetime.now().strftime("%Y%m%d")
    count = conn.execute("""
        SELECT COUNT(*)
        FROM emergency_requests
        WHERE token LIKE ?
    """, (f"ER-{today_prefix}-%",)).fetchone()[0]
    return f"ER-{today_prefix}-{count + 1:03d}"


@app.post("/emergency")
def create_emergency(data: EmergencyRequest):

    if data.department not in DEPARTMENT_SCHEDULE:
        raise HTTPException(status_code=400, detail="Invalid department")

    if data.emergency_type not in EMERGENCY_TYPES:
        raise HTTPException(status_code=400, detail="Invalid emergency type")

    conn = get_db()

    patient = conn.execute("""
        SELECT id, name
        FROM users
        WHERE id = ? AND role = 'patient'
    """, (data.patient_id,)).fetchone()

    if not patient:
        conn.close()
        raise HTTPException(status_code=404, detail="Patient account not found")

    # Keep one active emergency request per patient at a time.
    active = conn.execute("""
        SELECT id, token, status
        FROM emergency_requests
        WHERE patient_id = ?
        AND status IN ('requested', 'acknowledged', 'in_progress')
        ORDER BY id DESC
        LIMIT 1
    """, (data.patient_id,)).fetchone()

    if active:
        conn.close()
        raise HTTPException(
            status_code=400,
            detail=f"You already have an active emergency request ({active['token']})."
        )

    doctor = DEPARTMENT_SCHEDULE[data.department]["doctor"]
    token = emergency_token(conn)
    created_at = format_datetime(datetime.now())

    if USE_POSTGRES:
        cursor = conn.execute("""
            INSERT INTO emergency_requests
            (patient_id, patient_name, emergency_type, description,
             location, emergency_contact, department, doctor, token,
             status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            RETURNING id
        """, (
            data.patient_id,
            patient["name"],
            data.emergency_type,
            data.description or "",
            data.location or "",
            data.emergency_contact or "",
            data.department,
            doctor,
            token,
            "requested",
            created_at
        ))
        request_id = cursor.fetchone()[0]
    else:
        cursor = conn.execute("""
            INSERT INTO emergency_requests
            (patient_id, patient_name, emergency_type, description,
             location, emergency_contact, department, doctor, token,
             status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data.patient_id,
            patient["name"],
            data.emergency_type,
            data.description or "",
            data.location or "",
            data.emergency_contact or "",
            data.department,
            doctor,
            token,
            "requested",
            created_at
        ))
        request_id = cursor.lastrowid

    conn.commit()
    conn.close()

    return {
        "message": "Emergency request submitted successfully.",
        "emergency": {
            "id": request_id,
            "patient_id": data.patient_id,
            "patient_name": patient["name"],
            "emergency_type": data.emergency_type,
            "description": data.description or "",
            "location": data.location or "",
            "emergency_contact": data.emergency_contact or "",
            "department": data.department,
            "doctor": doctor,
            "token": token,
            "status": "requested",
            "created_at": created_at,
            "response_minutes": None
        }
    }


@app.get("/emergency/patient/{patient_id}")
def patient_emergencies(patient_id: int):
    conn = get_db()
    rows = conn.execute("""
        SELECT *
        FROM emergency_requests
        WHERE patient_id = ?
        ORDER BY id DESC
    """, (patient_id,)).fetchall()
    conn.close()
    return [dict(row) for row in rows]


@app.get("/emergency")
def emergency_queue(department: str | None = None):
    conn = get_db()

    query = """
        SELECT *
        FROM emergency_requests
        WHERE status IN ('requested', 'acknowledged', 'in_progress')
    """
    params = []

    if department:
        query += " AND department = ?"
        params.append(department)

    query += " ORDER BY CASE status WHEN 'requested' THEN 0 WHEN 'acknowledged' THEN 1 ELSE 2 END, id ASC"

    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [dict(row) for row in rows]


@app.put("/emergency/{emergency_id}")
def update_emergency(emergency_id: int, data: EmergencyStatusRequest):

    if data.status not in EMERGENCY_STATUSES:
        raise HTTPException(status_code=400, detail="Invalid emergency status")

    conn = get_db()
    request = conn.execute("""
        SELECT *
        FROM emergency_requests
        WHERE id = ?
    """, (emergency_id,)).fetchone()

    if not request:
        conn.close()
        raise HTTPException(status_code=404, detail="Emergency request not found")

    now = datetime.now()
    now_text = format_datetime(now)

    if data.status == "acknowledged":
        conn.execute("""
            UPDATE emergency_requests
            SET status = ?, acknowledged_at = ?
            WHERE id = ?
        """, ("acknowledged", now_text, emergency_id))

    elif data.status == "in_progress":
        start_text = request["actual_start_time"] or now_text
        conn.execute("""
            UPDATE emergency_requests
            SET status = ?, actual_start_time = ?
            WHERE id = ?
        """, ("in_progress", start_text, emergency_id))

    elif data.status == "resolved":
        start = request["actual_start_time"]
        response_minutes = None
        if start:
            try:
                start_dt = datetime.strptime(start, "%Y-%m-%d %H:%M:%S")
                response_minutes = max(0, int((now - start_dt).total_seconds() / 60))
            except ValueError:
                response_minutes = None

        conn.execute("""
            UPDATE emergency_requests
            SET status = ?, resolved_at = ?, response_minutes = ?
            WHERE id = ?
        """, ("resolved", now_text, response_minutes, emergency_id))

    elif data.status == "cancelled":
        conn.execute("""
            UPDATE emergency_requests
            SET status = ?
            WHERE id = ?
        """, ("cancelled", emergency_id))

    else:
        conn.execute("""
            UPDATE emergency_requests
            SET status = ?
            WHERE id = ?
        """, (data.status, emergency_id))

    conn.commit()
    conn.close()

    return {"message": "Emergency status updated successfully.", "status": data.status}


@app.get("/admin/emergencies")
def admin_emergencies():
    conn = get_db()
    rows = conn.execute("""
        SELECT *
        FROM emergency_requests
        ORDER BY id DESC
    """).fetchall()
    conn.close()
    return [dict(row) for row in rows]


@app.get("/admin/emergency-analytics")
def admin_emergency_analytics():
    conn = get_db()

    total = conn.execute("SELECT COUNT(*) FROM emergency_requests").fetchone()[0]
    active = conn.execute("""
        SELECT COUNT(*) FROM emergency_requests
        WHERE status IN ('requested', 'acknowledged', 'in_progress')
    """).fetchone()[0]
    resolved = conn.execute("""
        SELECT COUNT(*) FROM emergency_requests
        WHERE status = 'resolved'
    """).fetchone()[0]
    cancelled = conn.execute("""
        SELECT COUNT(*) FROM emergency_requests
        WHERE status = 'cancelled'
    """).fetchone()[0]
    avg_response = conn.execute("""
        SELECT AVG(response_minutes)
        FROM emergency_requests
        WHERE response_minutes IS NOT NULL
    """).fetchone()[0]

    conn.close()

    return {
        "total": total,
        "active": active,
        "resolved": resolved,
        "cancelled": cancelled,
        "average_response_minutes": round(avg_response, 1) if avg_response is not None else 0
    }


# =========================================================
# ADMIN - PATIENT MANAGEMENT
# =========================================================

@app.get("/admin/patients")
def admin_patients():

    conn = get_db()

    patients = conn.execute("""
        SELECT
            id,
            name,
            email,
            department
        FROM users
        WHERE role = 'patient'
        ORDER BY id DESC
    """).fetchall()

    conn.close()

    return [
        dict(patient)
        for patient in patients
    ]


@app.delete("/admin/patients/{patient_id}")
def delete_patient(
    patient_id: int,
    data: AdminDeletePatientRequest
):

    conn = get_db()

    try:

        # -----------------------------------------------------
        # VERIFY ADMIN ACCOUNT
        # -----------------------------------------------------

        admin = conn.execute("""
            SELECT id
            FROM users
            WHERE id = ?
            AND role = 'admin'
        """, (
            data.admin_id,
        )).fetchone()

        if not admin:

            raise HTTPException(
                status_code=403,
                detail="Only an admin account can delete patients."
            )

        # -----------------------------------------------------
        # FIND PATIENT
        # -----------------------------------------------------

        patient = conn.execute("""
            SELECT id, name, email
            FROM users
            WHERE id = ?
            AND role = 'patient'
        """, (
            patient_id,
        )).fetchone()

        if not patient:

            raise HTTPException(
                status_code=404,
                detail="Patient account not found."
            )

        # -----------------------------------------------------
        # DELETE PATIENT APPOINTMENTS FIRST
        # -----------------------------------------------------

        deleted_appointments = conn.execute("""
            DELETE FROM appointments
            WHERE patient_id = ?
        """, (
            patient_id,
        )).rowcount

        # -----------------------------------------------------
        # DELETE PATIENT ACCOUNT
        # -----------------------------------------------------

        deleted_patient = conn.execute("""
            DELETE FROM users
            WHERE id = ?
            AND role = 'patient'
        """, (
            patient_id,
        )).rowcount

        if deleted_patient != 1:

            conn.rollback()

            raise HTTPException(
                status_code=500,
                detail="Patient account could not be deleted."
            )

        conn.commit()

        return {
            "message": "Patient account deleted successfully.",
            "patient_id": patient_id,
            "patient_name": patient["name"],
            "patient_email": patient["email"],
            "deleted_appointments": deleted_appointments
        }

    except HTTPException:

        conn.close()
        raise

    except Exception as error:

        conn.rollback()
        conn.close()

        print("Delete patient error:", error)

        raise HTTPException(
            status_code=500,
            detail="Unable to delete patient account safely."
        )

    finally:

        try:
            conn.close()
        except Exception:
            pass


# =========================================================
# ADMIN ANALYTICS
# =========================================================

@app.get("/admin/analytics")
def admin_analytics():

    conn = get_db()

    total = conn.execute("""
        SELECT COUNT(*)
        FROM appointments
        WHERE status != 'cancelled'
    """).fetchone()[0]

    waiting = conn.execute("""
        SELECT COUNT(*)
        FROM appointments
        WHERE status = 'waiting'
    """).fetchone()[0]

    completed = conn.execute("""
        SELECT COUNT(*)
        FROM appointments
        WHERE status = 'completed'
    """).fetchone()[0]

    cancelled = conn.execute("""
        SELECT COUNT(*)
        FROM appointments
        WHERE status = 'cancelled'
    """).fetchone()[0]

    departments = conn.execute("""
        SELECT
            department,
            COUNT(*) AS total
        FROM appointments
        WHERE status != 'cancelled'
        GROUP BY department
        ORDER BY total DESC
    """).fetchall()

    conn.close()

    return {
        "total_appointments": total,
        "waiting": waiting,
        "completed": completed,
        "cancelled": cancelled,
        "departments": [
            dict(row)
            for row in departments
        ]
    }


# =========================================================
# RUN SERVER
# =========================================================

if __name__ == "__main__":

    import uvicorn

    uvicorn.run(
        app,
        host="127.0.0.1",
        port=8000
    )