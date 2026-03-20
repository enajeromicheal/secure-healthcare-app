# app.py — Secure Healthcare Record System (Flask)
# - MongoDB: authentication + roles (admin/patient)
# - SQLite: patient_records (ONE record per patient, linked by username)
# - Security: CSRF protection + secure headers (Talisman), sessions, RBAC
# - Admin features: create patient (auto-username + temp password + record), search records, reset passwords
# - Patient features: view own record, change password

import os
import re
import sqlite3
import secrets
import string

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_SQLITE_PATH = os.path.join(BASE_DIR, "healthcare.db")

from dotenv import load_dotenv
from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_talisman import Talisman
from flask_wtf.csrf import CSRFProtect
from werkzeug.security import generate_password_hash, check_password_hash
from collections import defaultdict
import time
from utils.validators import validate_age, validate_sex, validate_blood_pressure
from db.users_mongo import (
    create_user,
    find_user,
    update_password_hash,
    ensure_user_indexes,
    delete_user,
    deactivate_user,
    set_must_change_password,
)
from db.mongo import ping_mongo


# -------------------------
# Environment setup
# -------------------------
load_dotenv(override=True)

# -------------------------
# Flask app setup
# -------------------------
app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-only-change-me")  # Replace in production

# =========================
# Simple login rate limiter
# =========================
login_attempts = defaultdict(list)
MAX_LOGIN_ATTEMPTS = 5
BLOCK_TIME = 300  # seconds

# =========================
# Session Security Settings
# =========================

app.config["SESSION_COOKIE_HTTPONLY"] = True
# Prevents JavaScript from accessing cookies (protects against XSS)

app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
# Prevents CSRF attacks from external sites

app.config["SESSION_COOKIE_SECURE"] = False
# Should be True in HTTPS production. False for local development.

app.config["PERMANENT_SESSION_LIFETIME"] = 900
# Session expires after 15 minutes of inactivity
# -------------------------
# Security headers (Talisman)
# -------------------------
csp = {
    "default-src": ["'self'"],
    "style-src": ["'self'"],
    "img-src": ["'self'"],
    "script-src": ["'self'"],
}
# Only force HTTPS in production, not during local development or testing
is_production = os.environ.get("FLASK_ENV") == "production"

Talisman(
    app,
    content_security_policy=csp,
    frame_options="DENY",
    force_https=is_production,
    strict_transport_security=is_production,
    strict_transport_security_preload=is_production,
    strict_transport_security_include_subdomains=is_production,
)

# ----------------------------
# CSRF Protection
# ----------------------------
csrf = CSRFProtect(app)

# ----------------------------
# Session Timeout Enforcement
# ----------------------------
from datetime import timedelta

@app.before_request
def make_session_permanent():
    # Ensures session timeout is enforced
    session.permanent = True
# -------------------------
# SQLite helpers
# -------------------------
def get_db_connection():
    # # Connects to SQLite patient database (path can be overridden via env)
    db_path = os.environ.get("SQLITE_DB_PATH", DEFAULT_SQLITE_PATH)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def log_audit(username, action):
    conn = get_db_connection()
    conn.execute(
        "INSERT INTO audit_logs (username, action) VALUES (?, ?)",
        (username, action)
    )
    conn.commit()
    conn.close()

def ensure_sqlite_schema():
    # # Ensures the patient_records table exists with username linkage
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS patient_records (
            username TEXT UNIQUE NOT NULL,
            patient_id INTEGER PRIMARY KEY,
            age INTEGER NOT NULL,
            sex TEXT NOT NULL,
            blood_pressure INTEGER NOT NULL,
            cholesterol_level INTEGER NOT NULL,
            fasting_blood_sugar_over_120mg_dl TEXT NOT NULL,
            resting_ecg TEXT NOT NULL,
            exercise_induced_angina TEXT NOT NULL
        );
    """)
        # Appointments table (basic booking + viewing)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS appointments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_username TEXT NOT NULL,
            clinician_username TEXT,
            appointment_datetime TEXT NOT NULL,
            reason TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'booked',
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        );
    """)

    # Prescriptions table (issued by clinician/admin, viewed by patient)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS prescriptions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_username TEXT NOT NULL,
            clinician_username TEXT NOT NULL,
            medication_name TEXT NOT NULL,
            dosage TEXT NOT NULL,
            instructions TEXT NOT NULL,
            issue_date TEXT NOT NULL DEFAULT (date('now')),
            status TEXT NOT NULL DEFAULT 'active'
        );
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS audit_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            action TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        );
    """)
    conn.commit()
    conn.close()


# Ensure DB schema and Mongo indexes at startup (idempotent)
ensure_sqlite_schema()
ensure_user_indexes()

# -------------------------
# Utility: username + password generation
# -------------------------
def slugify_name(name: str) -> str:
    # # Converts a full name into a safe base string for usernames
    name = name.strip().lower()
    name = re.sub(r"[^a-z0-9\s-]", "", name)
    name = re.sub(r"\s+", "-", name)
    name = re.sub(r"-{2,}", "-", name)
    base = name.strip("-")
    return base if base else "patient"


def generate_unique_username(patient_name: str) -> str:
    # # Produces username format: name + 4-digit suffix, ensuring uniqueness
    base = slugify_name(patient_name)

    for _ in range(30):
        suffix = str(secrets.randbelow(9000) + 1000)  # 4 digits
        candidate = f"{base}-{suffix}"

        # Check Mongo uniqueness
        if find_user(candidate):
            continue

        # Check SQLite uniqueness
        conn = get_db_connection()
        exists = conn.execute(
            "SELECT 1 FROM patient_records WHERE username = ? LIMIT 1;",
            (candidate,)
        ).fetchone()
        conn.close()

        if exists is None:
            return candidate

    # Fallback (very unlikely)
    return f"{base}-{secrets.token_hex(3)}"


def generate_temp_password(length: int = 14) -> str:
    # # Generates a strong temporary password (shown once to admin)
    alphabet = string.ascii_letters + string.digits + "!@#$%&*_-"
    return "".join(secrets.choice(alphabet) for _ in range(length))


# -------------------------
# Auth helpers (session + RBAC)
# -------------------------
def require_login():
    # # Redirects unauthenticated users to login
    if "username" not in session:
        flash("Please log in first.", "warning")
        return redirect(url_for("login"))
    return None


def require_admin():
    # # Restricts access to admins only
    if session.get("role") != "admin":
        flash("Access denied. Admins only.", "error")
        return redirect(url_for("dashboard"))
    return None

def require_admin_or_clinician():
    # Restricts access to admins or clinicians only
    if session.get("role") not in {"admin", "clinician"}:
        flash("Access denied. Admins/clinicians only.", "error")
        return redirect(url_for("dashboard"))
    return None


# -------------------------
# Routes: public
# -------------------------
@app.route("/")
def home():
    # # public landing page 
    if "username" in session:
        return redirect(url_for("dashboard"))
    return render_template("home.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    # # Optional public registration (patient role only)
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        if not username or not password:
            flash("Username and password are required.", "error")
            return redirect(url_for("register"))

        # Hash password securely
        password_hash = generate_password_hash(
            password, method="pbkdf2:sha256", salt_length=16
        )

        # Force patient role (prevents privilege escalation)
        ok, reason = create_user(username, password_hash, role="patient", must_change_password=True)

        if not ok:
            if reason == "duplicate":
                flash("Username already exists.", "error")
            else:
                flash("Registration failed. Please check terminal logs.", "error")
            return redirect(url_for("register"))

        flash("Registration successful. Please log in.", "success")
        return redirect(url_for("login"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    # User login: verifies password and starts session

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        # Login rate limiting (brute-force protection)
        ip = request.remote_addr
        now = time.time()

        # Remove expired attempts
        login_attempts[ip] = [t for t in login_attempts[ip] if now - t < BLOCK_TIME]

        if len(login_attempts[ip]) >= MAX_LOGIN_ATTEMPTS:
            flash("Too many login attempts. Try again later.", "error")
            return redirect(url_for("login"))

        user = find_user(username)

        if user and check_password_hash(user["password_hash"], password):

            if user.get("is_active") is False:
                flash("This account has been deactivated.", "error")
                return redirect(url_for("login"))

            session.clear()
            session["username"] = user["username"]
            session["role"] = user.get("role", "patient")
            session.permanent = True
            log_audit(username, "login_success")
            
            if user.get("must_change_password", False):
                flash("You must change your temporary password.", "warning")
                return redirect(url_for("change_password"))

            flash("Login successful.", "success")
            return redirect(url_for("dashboard"))

        # Record failed login attempt
        login_attempts[ip].append(now)
        log_audit(username or ip, "login_failed")

        flash("Invalid login details.", "error")
        return redirect(url_for("login"))

    return render_template("login.html")

@app.route("/logout")
def logout():
    # Clears session and logs user out
    session.clear()
    flash("You have been logged out.", "success")
    return redirect(url_for("home"))


# -------------------------
# Routes: authenticated
# -------------------------
@app.route("/dashboard")
def dashboard():
    # # Dashboard for logged-in users
    gate = require_login()
    if gate:
        return gate

    return render_template(
        "dashboard.html",
        username=session["username"],
        role=session["role"],
    )


@app.route("/my-record")
def my_record():
    # # Patient-only record view (one record linked to username)
    gate = require_login()
    if gate:
        return gate

    if session.get("role") != "patient":
        flash("Only patient accounts can view a personal record.", "warning")
        return redirect(url_for("dashboard"))

    conn = get_db_connection()
    record = conn.execute(
        "SELECT * FROM patient_records WHERE username = ? LIMIT 1;",
        (session["username"],)
    ).fetchone()
    conn.close()

    if record is None:
        flash("No record is linked to your account yet. Please contact an administrator.", "warning")
        return redirect(url_for("dashboard"))
    log_audit(session["username"], "view_patient_record")
    return render_template("my_record.html", record=record)


@app.route("/change-password", methods=["GET", "POST"])
def change_password():
    # # Allows any logged-in user to change their password
    gate = require_login()
    if gate:
        return gate

    if request.method == "POST":
        current_password = request.form.get("current_password", "")
        new_password = request.form.get("new_password", "")
        confirm_password = request.form.get("confirm_password", "")

        if not current_password or not new_password or not confirm_password:
            flash("All fields are required.", "error")
            return redirect(url_for("change_password"))

        if new_password != confirm_password:
            flash("New passwords do not match.", "error")
            return redirect(url_for("change_password"))

        user = find_user(session["username"])
        if not user or not check_password_hash(user["password_hash"], current_password):
            flash("Current password is incorrect.", "error")
            return redirect(url_for("change_password"))

        if len(new_password) < 10:
            flash("New password must be at least 10 characters long.", "error")
            return redirect(url_for("change_password"))

        new_hash = generate_password_hash(
            new_password, method="pbkdf2:sha256", salt_length=16
        )
        ok = update_password_hash(session["username"], new_hash)

        if ok:
            log_audit(session["username"], "change_password")
            flash("Password updated successfully.", "success")
            return redirect(url_for("dashboard"))

        flash("Password update failed. Please check logs.", "error")
        return redirect(url_for("change_password"))

    return render_template("change_password.html")


@app.route("/my-prescriptions")
def my_prescriptions():
    # Patient-only: view own prescriptions
    gate = require_login()
    if gate:
        return gate

    if session.get("role") != "patient":
        flash("Only patient accounts can view personal prescriptions.", "warning")
        return redirect(url_for("dashboard"))

    conn = get_db_connection()
    rows = conn.execute("""
        SELECT * FROM prescriptions
        WHERE patient_username = ?
        ORDER BY issue_date DESC, id DESC
        LIMIT 100;
    """, (session["username"],)).fetchall()
    conn.close()

    return render_template("my_prescriptions.html", prescriptions=rows)


@app.route("/prescriptions")
def prescriptions():
    # Admin/clinician: view all prescriptions (search)
    gate = require_login()
    if gate:
        return gate
    gate = require_admin_or_clinician()
    if gate:
        return gate

    q = request.args.get("q", "").strip()

    conn = get_db_connection()
    if q:
        like = f"%{q}%"
        rows = conn.execute("""
            SELECT * FROM prescriptions
            WHERE patient_username LIKE ?
               OR clinician_username LIKE ?
               OR medication_name LIKE ?
               OR status LIKE ?
            ORDER BY issue_date DESC, id DESC
            LIMIT 200;
        """, (like, like, like, like)).fetchall()
    else:
        rows = conn.execute("""
            SELECT * FROM prescriptions
            ORDER BY issue_date DESC, id DESC
            LIMIT 200;
        """).fetchall()
    conn.close()

    return render_template("prescriptions.html", prescriptions=rows, q=q)


@app.route("/prescriptions/create", methods=["GET", "POST"])
def create_prescription():
    # Admin/clinician: create a prescription for a patient username
    gate = require_login()
    if gate:
        return gate
    gate = require_admin_or_clinician()
    if gate:
        return gate

    if request.method == "POST":
        patient_username = request.form.get("patient_username", "").strip()
        medication_name = request.form.get("medication_name", "").strip()
        dosage = request.form.get("dosage", "").strip()
        instructions = request.form.get("instructions", "").strip()

        if not patient_username or not medication_name or not dosage or not instructions:
            flash("All fields are required.", "error")
            return redirect(url_for("create_prescription"))

        patient = find_user(patient_username)
        if not patient or patient.get("role") != "patient":
            flash("Patient username not found (or not a patient).", "error")
            return redirect(url_for("create_prescription"))

        conn = get_db_connection()
        conn.execute("""
            INSERT INTO prescriptions (
                patient_username, clinician_username,
                medication_name, dosage, instructions,
                status
            )
            VALUES (?, ?, ?, ?, ?, 'active');
        """, (patient_username, session["username"], medication_name, dosage, instructions))
        conn.commit()
        conn.close()
        log_audit(session["username"], f"create_prescription_for:{patient_username}")

        flash("Prescription created successfully.", "success")
        return redirect(url_for("prescriptions"))

    return render_template("create_prescription.html")


# -------------------------
# Routes: admin
# -------------------------
@app.route("/patients")
def patients():
    gate = require_login()
    if gate:
        return gate

    gate = require_admin_or_clinician()
    if gate:
        return gate

    q = request.args.get("q", "").strip()

    conn = get_db_connection()

    if q:
        like = f"%{q}%"
        rows = conn.execute("""
            SELECT * FROM patient_records
            WHERE (
                COALESCE(username, '') LIKE ?
                OR CAST(patient_id AS TEXT) LIKE ?
                OR CAST(age AS TEXT) LIKE ?
                OR sex LIKE ?
            )
            ORDER BY patient_id ASC
            LIMIT 100;
        """, (like, like, like, like)).fetchall()
    else:
        rows = conn.execute("""
            SELECT * FROM patient_records
            ORDER BY patient_id ASC
            LIMIT 100;
        """).fetchall()

    conn.close()

    return render_template("patients.html", patients=rows, q=q)

@app.route("/admin/create-patient", methods=["GET", "POST"])
def admin_create_patient():
    # Admin-only: creates a patient user + their linked SQLite record
    gate = require_login()
    if gate:
        return gate

    gate = require_admin()
    if gate:
        return gate

    if request.method == "POST":
        # Account input
        patient_name = request.form.get("patient_name", "").strip()

        # Record input (matches SQLite schema)
        patient_id = request.form.get("patient_id", "").strip()
        age = request.form.get("age", "").strip()
        sex = request.form.get("sex", "").strip()
        blood_pressure = request.form.get("blood_pressure", "").strip()
        cholesterol_level = request.form.get("cholesterol_level", "").strip()
        fasting = request.form.get("fasting_blood_sugar_over_120mg_dl", "").strip()
        resting_ecg = request.form.get("resting_ecg", "").strip()
        angina = request.form.get("exercise_induced_angina", "").strip()

        if not validate_age(age):
            flash("Invalid age value", "error")
            return redirect(url_for("admin_create_patient"))

        if not validate_sex(sex):
            flash("Invalid sex value", "error")
            return redirect(url_for("admin_create_patient"))

        if not validate_blood_pressure(blood_pressure):
            flash("Invalid blood pressure value", "error")
            return redirect(url_for("admin_create_patient"))

                # Validation
        if not patient_name:
            flash("Patient full name is required.", "error")
            return redirect(url_for("admin_create_patient"))

        required = {
            "Patient ID": patient_id,
            "Age": age,
            "Sex": sex,
            "Blood Pressure": blood_pressure,
            "Cholesterol Level": cholesterol_level,
            "Fasting Blood Sugar": fasting,
            "Resting ECG": resting_ecg,
            "Exercise Induced Angina": angina,
        }

        for label, value in required.items():
            if value == "":
                flash(f"{label} is required.", "error")
                return redirect(url_for("admin_create_patient"))
        # Generate credentials
        username = generate_unique_username(patient_name)
        temp_password = generate_temp_password()
        password_hash = generate_password_hash(
            temp_password, method="pbkdf2:sha256", salt_length=16
        )
        # 1) Create Mongo user
        ok, reason = create_user(
            username,
            password_hash,
            role="patient",
            must_change_password=True
        )
        if not ok:
            if reason == "duplicate":
                flash("Generated username already exists. Please try again.", "error")
            else:
                flash("User creation failed. Please check terminal logs.", "error")
            return redirect(url_for("admin_create_patient"))

        # 2) Insert SQLite record
        try:
            conn = get_db_connection()
            conn.execute("""
                INSERT INTO patient_records (
                    username, patient_id, age, sex,
                    blood_pressure, cholesterol_level,
                    fasting_blood_sugar_over_120mg_dl, resting_ecg,
                    exercise_induced_angina
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
            """, (
                username,
                int(patient_id),
                int(age),
                sex,
                int(blood_pressure),
                int(cholesterol_level),
                fasting,
                resting_ecg,
                angina,
            ))
            conn.commit()
            conn.close()
            log_audit(session["username"], f"create_patient:{username}")
        except Exception as e:
            print("SQLite insert error:", e)
            delete_user(username)
            flash("Patient record creation failed (SQLite). User rollback completed.", "error")
            return redirect(url_for("admin_create_patient"))
        # Show temp credentials once
        return render_template(
            "admin_create_patient_success.html",
            created_username=username,
            temp_password=temp_password,
        )

    return render_template("admin_create_patient.html")


@app.route("/admin/reset-password", methods=["GET", "POST"])
def admin_reset_password():
    # # Admin-only: generates a new temporary password for a user
    gate = require_login()
    if gate:
        return gate
    gate = require_admin()
    if gate:
        return gate

    if request.method == "POST":
        username = request.form.get("username", "").strip()

        if not username:
            flash("Username is required.", "error")
            return redirect(url_for("admin_reset_password"))

        user = find_user(username)
        if not user:
            flash("No such user exists.", "error")
            return redirect(url_for("admin_reset_password"))

        temp_password = generate_temp_password()
        new_hash = generate_password_hash(
            temp_password, method="pbkdf2:sha256", salt_length=16
        )

        ok = update_password_hash(username, new_hash)
        if not ok:
            flash("Password reset failed. Please check logs.", "error")
            return redirect(url_for("admin_reset_password"))

        set_must_change_password(username, True)
        log_audit(session["username"], f"reset_password_for:{username}")

        return render_template(
            "admin_reset_password_success.html",
            reset_username=username,
            temp_password=temp_password,
        )

    return render_template("admin_reset_password.html")


# -------------------------
# Health endpoint (Mongo)
# -------------------------
@app.route("/health/mongo")
def health_mongo():
    # # Health check for MongoDB connectivity
    ok, msg = ping_mongo()
    status = 200 if ok else 500
    return {"ok": ok, "message": msg}, status

# ===========================
# APPOINTMENTS (patient booking + viewing)
# ===========================

@app.route("/book-appointment", methods=["GET", "POST"])
def book_appointment():
    # Patient-only: create an appointment request
    gate = require_login()
    if gate:
        return gate

    if session.get("role") != "patient":
        flash("Only patient accounts can book appointments.", "warning")
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        # Basic input validation (healthcare data integrity)
        appointment_datetime = request.form.get("appointment_datetime", "").strip()
        reason = request.form.get("reason", "").strip()

        if not appointment_datetime or not reason:
            flash("Appointment date/time and reason are required.", "error")
            return redirect(url_for("book_appointment"))

        if len(reason) > 500:
            flash("Reason is too long (max 500 characters).", "error")
            return redirect(url_for("book_appointment"))

        conn = get_db_connection()
        conn.execute(
            """
            INSERT INTO appointments (patient_username, appointment_datetime, reason, status)
            VALUES (?, ?, ?, 'booked');
            """,
            (session["username"], appointment_datetime, reason),
        )
        conn.commit()
        conn.close()
        log_audit(session["username"], "book_appointment")

        flash("Appointment booked successfully.", "success")
        return redirect(url_for("my_appointments"))

    # GET: show booking form
    return render_template("book_appointment.html")


@app.route("/my-appointments")
def my_appointments():
    # Patient-only: view own appointments
    gate = require_login()
    if gate:
        return gate

    if session.get("role") != "patient":
        flash("Only patient accounts can view personal appointments.", "warning")
        return redirect(url_for("dashboard"))

    conn = get_db_connection()
    rows = conn.execute(
        """
        SELECT * FROM appointments
        WHERE patient_username = ?
        ORDER BY appointment_datetime DESC
        LIMIT 100;
        """,
        (session["username"],),
    ).fetchall()
    conn.close()

    return render_template("my_appointments.html", appointments=rows)


@app.route("/appointments")
def appointments():
    # Admin/Clinician: view all appointments (optional search)
    gate = require_login()
    if gate:
        return gate

    gate = require_admin_or_clinician()
    if gate:
        return gate

    q = request.args.get("q", "").strip()

    conn = get_db_connection()
    if q:
        like = f"%{q}%"
        rows = conn.execute(
            """
            SELECT * FROM appointments
            WHERE patient_username LIKE ?
               OR clinician_username LIKE ?
               OR status LIKE ?
               OR reason LIKE ?
            ORDER BY appointment_datetime DESC
            LIMIT 200;
            """,
            (like, like, like, like),
        ).fetchall()
    else:
        rows = conn.execute(
            """
            SELECT * FROM appointments
            ORDER BY appointment_datetime DESC
            LIMIT 200;
            """
        ).fetchall()
    conn.close()

    return render_template("appointments.html", appointments=rows, q=q)
@app.route("/patients/<int:patient_id>/edit", methods=["GET", "POST"])
def edit_patient_record(patient_id):
    gate = require_login()
    if gate:
        return gate

    gate = require_admin_or_clinician()
    if gate:
        return gate

    conn = get_db_connection()

    if request.method == "POST":
        age = request.form.get("age", "").strip()
        sex = request.form.get("sex", "").strip()
        blood_pressure = request.form.get("blood_pressure", "").strip()
        cholesterol_level = request.form.get("cholesterol_level", "").strip()
        fasting = request.form.get("fasting_blood_sugar_over_120mg_dl", "").strip()
        resting_ecg = request.form.get("resting_ecg", "").strip()
        angina = request.form.get("exercise_induced_angina", "").strip()

        if not age or not sex or not blood_pressure or not cholesterol_level or not fasting or not resting_ecg or not angina:
            conn.close()
            flash("All fields are required.", "error")
            return redirect(url_for("edit_patient_record", patient_id=patient_id))

        try:
            age = int(age)
            blood_pressure = int(blood_pressure)
            cholesterol_level = int(cholesterol_level)
        except ValueError:
            conn.close()
            flash("Age, blood pressure, and cholesterol must be numbers.", "error")
            return redirect(url_for("edit_patient_record", patient_id=patient_id))

        conn.execute("""
            UPDATE patient_records
            SET age = ?, sex = ?, blood_pressure = ?, cholesterol_level = ?,
                fasting_blood_sugar_over_120mg_dl = ?, resting_ecg = ?, exercise_induced_angina = ?
            WHERE patient_id = ?;
        """, (
            age,
            sex,
            blood_pressure,
            cholesterol_level,
            fasting,
            resting_ecg,
            angina,
            patient_id
        ))
        conn.commit()
        conn.close()

        log_audit(session["username"], "edit_patient_record")
        flash("Patient record updated successfully.", "success")
        return redirect(url_for("patients"))

    record = conn.execute("""
        SELECT * FROM patient_records
        WHERE patient_id = ?
        LIMIT 1;
    """, (patient_id,)).fetchone()

    conn.close()

    if record is None:
        flash("Patient record not found.", "error")
        return redirect(url_for("patients"))

    return render_template("edit_patient_record.html", record=record)
@app.route("/patients/<int:patient_id>/delete", methods=["GET", "POST"])
def delete_patient_record(patient_id):
    gate = require_login()
    if gate:
        return gate

    gate = require_admin()
    if gate:
        return gate

    conn = get_db_connection()

    record = conn.execute("""
        SELECT * FROM patient_records
        WHERE patient_id = ?
        LIMIT 1;
    """, (patient_id,)).fetchone()

    if record is None:
        conn.close()
        flash("Patient record not found.", "error")
        return redirect(url_for("patients"))

    if request.method == "POST":
        username = record["username"]

        conn.execute("""
            DELETE FROM patient_records
            WHERE patient_id = ?;
        """, (patient_id,))
        conn.commit()
        conn.close()

        if username:
            delete_user(username)

        log_audit(session["username"], "delete_patient_record")
        flash("Patient record deleted successfully.", "success")
        return redirect(url_for("patients"))

    conn.close()
    return render_template("delete_patient_record.html", record=record)
@app.route("/patients/<username>/deactivate", methods=["POST"])
def deactivate_patient_user(username):
    # Admin-only: deactivate patient account without deleting record
    gate = require_login()
    if gate:
        return gate

    gate = require_admin()
    if gate:
        return gate

    ok = deactivate_user(username)

    if ok:
        flash("Patient account deactivated successfully.", "success")
    else:
        flash("Failed to deactivate patient account.", "error")

    return redirect(url_for("patients"))
# -------------------------
# Dev server entry-point
# -------------------------
if __name__ == "__main__":
    # # Debug should be disabled in production
    app.run(debug=True)