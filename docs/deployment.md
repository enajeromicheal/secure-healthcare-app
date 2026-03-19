# Deployment Guide – Secure Healthcare Record System

## 1. Introduction

This document explains how to set up and run the Secure Healthcare Record System on a local computer.

The system is a secure web application built using:

- Flask (web application framework)
- MongoDB (stores user accounts and roles)
- SQLite (stores patient records and medical data)

The system also includes several security features such as authentication, role-based access control, CSRF protection and secure session handling.

---

## 2. Security Features in the System

The application includes the following security protections:

- Passwords are securely hashed before storage
- Role-based access control (Admin, Clinician, Patient)
- Users must log in before accessing protected pages
- New users are forced to change their temporary password
- Important user actions are stored in an audit log
- SQL injection is prevented using parameterised queries
- All forms are protected using CSRF tokens
- Security headers are enabled using Flask-Talisman
- Secret keys and database settings are stored in environment variables

---

## 3. Requirements

Before running the system, make sure the following are installed:

- Python 3
- pip
- MongoDB (local installation or MongoDB Atlas)
- Virtual environment support

---

## 4. Install the Project

Open the project folder in the terminal.

Create a virtual environment:

```bash
python3 -m venv .venv
```

Activate the virtual environment:

Mac / Linux:

```bash
source .venv/bin/activate
```

Windows:

```bash
.venv\Scripts\activate
```

Install required packages:

```bash
pip install -r requirements.txt
```

---

## 5. Environment Setup

Create a file named `.env` in the project root folder.

Add the following settings:

```
SECRET_KEY=your_secret_key
MONGODB_URI=your_mongodb_connection_string
MONGODB_DB=healthcare
SQLITE_DB_PATH=healthcare.db
FLASK_ENV=development
```

This keeps sensitive information secure and outside the source code.

---

## 6. Prepare the Databases

Run the setup scripts to prepare the system:

```bash
python3 scripts/sqlite_setup.py
python3 scripts/seed_users.py
python3 scripts/create_clinician.py
```

These scripts will:

- Import the medical dataset into SQLite
- Create the audit log table
- Create default admin and patient users
- Create a clinician test account

---

## 7. Start the Application

Run the Flask server:

```bash
python3 app.py
```

Open the browser and go to:

```
http://127.0.0.1:5000
```

---

## 8. Run the Security Tests

The project includes automated tests to check security behaviour.

Run all tests using:

```bash
python3 -m unittest
```

These tests check:

- Login and logout security
- Session protection
- Role-based access control
- Access to protected pages

---

## 9. Important Notes for Real Deployment

For a real healthcare system, additional security steps would be required:

- Use Gunicorn or uWSGI instead of the Flask development server
- Use Nginx as a reverse proxy
- Enable HTTPS with SSL certificates
- Add login rate limiting to prevent brute-force attacks
- Add multi-factor authentication for admin users
- Encrypt databases at rest
- Restrict MongoDB access using IP restrictions
- Enable monitoring and intrusion detection
- Add automatic session timeout

---

## 10. Summary

This system demonstrates secure software development practices suitable for coursework demonstration.

Although the system is secure for academic purposes, further security improvements would be needed before using it in a real clinical environment.