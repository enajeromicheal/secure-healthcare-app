# Secure Healthcare Record System (Flask + SQLite + MongoDB)

A secure web application demonstrating authentication, role-based access control (RBAC), and secure handling of patient records.

## Tech Stack
- **Flask (Python)** – web server and routing
- **MongoDB** – user authentication store (username + password hash + role)
- **SQLite** – patient records database
- **Flask-Talisman** – security headers (CSP, HSTS, clickjacking protection)
- **Flask-WTF CSRF** – CSRF protection for form submissions
- **python-dotenv** – environment variable loading

---

## Features
- User registration (MongoDB)
- User login + session handling
- Dashboard showing logged-in user + role
- **RBAC:** `/patients` is **admin-only**
- Patient records stored in SQLite
- MongoDB health-check endpoint (for diagnostics)

---

## Security Controls Implemented
- Password hashing using PBKDF2 (Werkzeug)
- Unique username enforcement (MongoDB unique index)
- Session-based authentication with protected routes
- Role-based access control (admin-only patients page)
- CSRF protection for forms
- Secure HTTP headers via Flask-Talisman (CSP, HSTS, X-Frame-Options)
- SECRET_KEY stored in environment variable (not hard-coded)

---
## System Screenshots

### Home Page
![Home Page](docs/screenshots/home_page.png)

### Login Page
![Login Page](docs/screenshots/login_page.png)

### Register Page
![Register Page](docs/screenshots/register_page.png)

### Dashboard After Login
![Dashboard](docs/screenshots/patients_login_dashboard.png)

### Admin Patients Page
![Admin Patients](docs/screenshots/admin_login.png)

### Access Denied Page (RBAC Protection)
![Access Denied](docs/screenshots/access_denied.png)

### MongoDB Users Collection
![MongoDB](docs/screenshots/mongodb_users.png)

### SQLite Patient Records Table
![SQLite](docs/screenshots/sqlite_patient_table.png)

### Terminal Tests Passing
![Tests](docs/screenshots/terminal_tests.png)
## Project Structure
```text
.
├── app.py
├── db/
│   ├── mongo.py
│   └── users_mongo.py
├── templates/
├── static/
├── docs/
│   ├── threat_model_stride.md
│   ├── trust_boundary_diagram.md
│   └── evaluation_and_residual_risk.md
├── sqlite_setup.py
├── requirements.txt
└── README.md