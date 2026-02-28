import os
import re
import sqlite3
from dotenv import load_dotenv
from flask_talisman import Talisman
from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from flask_wtf.csrf import CSRFProtect

load_dotenv()

def get_db_connection():
    conn = sqlite3.connect("healthcare.db")
    conn.row_factory = sqlite3.Row
    return conn

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-only-change-me")
csp = {
    "default-src": ["'self'"],
    "style-src": ["'self'"],
    "img-src": ["'self'"],
    "script-src": ["'self'"],
}

Talisman(
    app,
    content_security_policy=csp,
    frame_options="DENY",
    strict_transport_security=True,
    strict_transport_security_preload=True,
    strict_transport_security_include_subdomains=True,
)
csrf = CSRFProtect(app)
@app.route("/")
def home():
    return render_template("home.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        role = request.form.get("role", "patient")

        if not username or not password:
            flash("Username and password are required.")
            return redirect(url_for("register"))
        # Password strength check
        if len(password) < 8 or not re.search(r"\d", password):
            flash("Password must be at least 8 characters and contain at least one number.")
            return redirect(url_for("register"))

        # IMPORTANT: force PBKDF2 (fixes hashlib.scrypt error)
        password_hash = generate_password_hash(
            password,
            method="pbkdf2:sha256",
            salt_length=16
        )

        conn = get_db_connection()
        cur = conn.cursor()

        try:
            cur.execute(
                "INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)",
                (username, password_hash, role)
            )
            conn.commit()
            flash("Registration successful. Please log in.")
            return redirect(url_for("login"))

        except sqlite3.IntegrityError:
            flash("Username already exists.")
            return redirect(url_for("register"))

        finally:
            conn.close()

    return render_template("register.html")
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            "SELECT username, password_hash, role FROM users WHERE username = ?",
            (username,)
        )
        user = cur.fetchone()
        conn.close()

        if user and check_password_hash(user["password_hash"], password):
            session.clear()
            session["username"] = user["username"]
            session["role"] = user["role"]
            flash("Login successful.")
            return redirect(url_for("dashboard"))

        flash("Invalid login details.")
        return redirect(url_for("login"))

    return render_template("login.html")


@app.route("/dashboard")
def dashboard():
    if "username" not in session:
        flash("Please log in first.")
        return redirect(url_for("login"))

    return render_template("dashboard.html", username=session["username"], role=session["role"])

@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.")
    return redirect(url_for("home"))


@app.route("/patients")
def patients():
    if "username" not in session:
        flash("Please log in first.")
        return redirect(url_for("login"))

    if session.get("role") != "admin":
        flash("Access denied. Admins only.")
        return redirect(url_for("dashboard"))

    conn = get_db_connection()
    patients = conn.execute(
        "SELECT * FROM patient_records LIMIT 50;"
    ).fetchall()
    conn.close()

    return render_template("patients.html", patients=patients)

if __name__ == "__main__":
    app.run(debug=True)