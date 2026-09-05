CREATE TABLE users(
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 name TEXT NOT NULL,
 email TEXT UNIQUE NOT NULL,
 password TEXT NOT NULL,
 role TEXT NOT NULL
);

CREATE TABLE appointments(
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 patient_id INTEGER,
 department TEXT,
 doctor TEXT,
 date TEXT,
 time TEXT,
 token TEXT,
 status TEXT,
 estimated_wait INTEGER
);