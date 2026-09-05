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

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =========================================================
# DATABASE
# =========================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "smartcare.db")


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

    conn = sqlite3.connect(DB_PATH)

    conn.row_factory = sqlite3.Row

    return conn


# =========================================================
# DATABASE MIGRATION HELPERS
# =========================================================

def column_exists(conn, table_name, column_name):

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

    return dt.strftime("%I:%M %p")


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
def register(data: RegisterRequest):

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

        "department": department,

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

    # Find the largest existing token number.
    # This prevents duplicate tokens after cancellation.
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

            "id": appointment_id,

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


    # -----------------------------------------------------
    # previous_end = when previous patient finishes
    # -----------------------------------------------------

    previous_end = session_start


    for appointment in appointments:

        appointment_id = appointment["id"]

        status = appointment["status"]


        # -------------------------------------------------
        # ORIGINAL PLANNED TIME
        # -------------------------------------------------

        planned_datetime = parse_planned_time(
            appointment_date,
            appointment["planned_time"]
        )


        # =================================================
        # COMPLETED
        # =================================================

        if status == "completed":

            # ---------------------------------------------
            # Actual start
            # ---------------------------------------------

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


            # ---------------------------------------------
            # Actual consultation duration
            # ---------------------------------------------

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


            # ---------------------------------------------
            # ACTUAL END
            #
            # Example:
            # 09:10 + 25 min = 09:35
            # ---------------------------------------------

            actual_end = (
                actual_start
                +
                timedelta(
                    minutes=consultation
                )
            )


            # ---------------------------------------------
            # DELAY
            # ---------------------------------------------

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


            # ---------------------------------------------
            # SAVE
            # ---------------------------------------------

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


            # ---------------------------------------------
            # VERY IMPORTANT
            #
            # NEXT PATIENT STARTS AFTER THIS END TIME
            # ---------------------------------------------

            previous_end = actual_end


        # =================================================
        # IN PROGRESS
        # =================================================

        elif status == "in_progress":

            # ---------------------------------------------
            # Actual start
            # ---------------------------------------------

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


            # ---------------------------------------------
            # While consultation is running,
            # assume 10 minutes until doctor completes it.
            # ---------------------------------------------

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

            # ---------------------------------------------
            # Patient starts at the later of:
            #
            # 1. Original planned time
            # 2. Previous patient actual finish time
            #
            # ---------------------------------------------

            expected_start = max(
                planned_datetime,
                previous_end
            )


            # ---------------------------------------------
            # Calculate delay
            # ---------------------------------------------

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


            # ---------------------------------------------
            # Save delay
            # ---------------------------------------------

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


            # ---------------------------------------------
            # Normal patient = 10 minutes
            # ---------------------------------------------

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
                timedelta(
                    minutes=consultation
                )
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
                timedelta(
                    minutes=consultation
                )
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


        # -------------------------------------------------
        # CALCULATED INFORMATION
        # -------------------------------------------------

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


        # Estimated wait from now
        # is mainly useful for waiting patients.

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

        # Get first active appointment
        current_appointment = (
            today_appointments[0]
        )


        # Calculate queue information
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


    # -----------------------------------------------------
    # RESPONSE
    # -----------------------------------------------------

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


    # If date isn't provided, use today
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


    params.append(appointment_date)


    rows = conn.execute(
        query,
        params
    ).fetchall()


    conn.close()


    # -----------------------------------------------------
    # If department provided,
    # return calculated queue.
    # -----------------------------------------------------

    if department:

        return get_calculated_queue(
            department,
            appointment_date
        )


    # -----------------------------------------------------
    # Otherwise return normal records
    # -----------------------------------------------------

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


    # -----------------------------------------------------
    # TODAY'S APPOINTMENTS ONLY
    # -----------------------------------------------------

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


    # -----------------------------------------------------
    # CALCULATED QUEUE
    # -----------------------------------------------------

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


    # -----------------------------------------------------
    # COUNTS
    # -----------------------------------------------------

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

        "waiting": waiting,

        "completed": completed,

        "in_progress": in_progress,

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

        # Check if another patient is already in progress
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


        # ---------------------------------------------
        # Actual start = now
        # ---------------------------------------------

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

        # ---------------------------------------------
        # Doctor enters actual consultation duration.
        #
        # Example:
        # 10
        # 20
        # 25
        # 30
        # ---------------------------------------------

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


        # ---------------------------------------------
        # Get actual start
        # ---------------------------------------------

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

            # If doctor directly completes
            # without starting first.
            actual_start = datetime.now()


        # ---------------------------------------------
        # ACTUAL END
        # ---------------------------------------------

        actual_end = (
            actual_start
            +
            timedelta(
                minutes=consultation
            )
        )


        # ---------------------------------------------
        # PLANNED TIME
        # ---------------------------------------------

        planned_datetime = parse_planned_time(
            appointment[
                "appointment_date"
            ],
            appointment[
                "planned_time"
            ]
        )


        # ---------------------------------------------
        # DELAY
        # ---------------------------------------------

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


        # ---------------------------------------------
        # SAVE COMPLETED DATA
        # ---------------------------------------------

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


    # -----------------------------------------------------
    # RECALCULATE QUEUE
    # -----------------------------------------------------

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
# SERVER
# =========================================================

if __name__ == "__main__":

    import uvicorn

    uvicorn.run(
        app,
        host="127.0.0.1",
        port=8000
    )