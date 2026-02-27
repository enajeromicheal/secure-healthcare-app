import sqlite3

def get_db_connection():
    conn = sqlite3.connect("healthcare.db")
    conn.row_factory = sqlite3.Row
    return conn
from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "change-this-to-a-long-random-string"  # we will improve this later


@app.route("/")
def home():
    return render_template("home.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        role = request.form.get("role", "patient")

        # Basic validation (improve later)
        if not username or not password:
            flash("Username and password are required.")
            return redirect(url_for("register"))

        password_hash = generate_password_hash(password)

        # For now: just show it works (we'll save to database next step)
        flash(f"Registered {username} as {role}. (DB saving comes next)")
        return redirect(url_for("login"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        # For now: temporary demo user check (we'll replace with DB next step)
        demo_user = "admin"
        demo_hash = generate_password_hash("Admin123!")  # temporary

        if username == demo_user and check_password_hash(demo_hash, password):
            session["username"] = username
            session["role"] = "admin"
            flash("Login successful.")
            return redirect(url_for("dashboard"))
        else:
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