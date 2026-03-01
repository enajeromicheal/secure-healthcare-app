# Trust Boundary Diagram – Secure Healthcare Record System

## System Components

1. Browser (User Client)
2. Flask Application Server
3. MongoDB (Authentication Database)
4. SQLite (Patient Records Database)

---

## Trust Boundaries

The system contains four primary trust boundaries:

### 1. HTTP Boundary (Browser ↔ Flask)

Sensitive data crossing this boundary:
- Login credentials
- Registration details
- Session cookies
- Patient data requests

Security Controls:
- Password hashing
- CSRF protection
- Secure headers (CSP, HSTS)
- Role-based access checks

---

### 2. Authentication Database Boundary (Flask ↔ MongoDB)

Data crossing:
- Username
- Password hash
- User role

Security Controls:
- Authenticated MongoDB URI
- Unique username index
- Hashed password storage

---

### 3. Patient Records Database Boundary (Flask ↔ SQLite)

Data crossing:
- Patient medical records
- Query results

Security Controls:
- Parameterised SQL queries
- Admin-only access enforcement
- Query LIMIT protection

---

### 4. Role Boundary (Patient vs Admin)

Sensitive operations:
- Access to /patients route
- Viewing all patient records

Security Controls:
- Role validation in session
- Access denied redirects

## Visual Representation

[ Browser ]
      |
      |  HTTP (Credentials, Cookies)
      v
[ Flask Application ]
      |                 |
      | MongoDB Auth    | SQLite Queries
      v                 v
[ MongoDB ]        [ SQLite ]
 (Auth DB)         (Patient Records)