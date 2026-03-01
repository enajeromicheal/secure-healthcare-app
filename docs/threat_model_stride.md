# STRIDE Threat Model

This document presents a STRIDE-based threat model for the Secure Healthcare Record System.  
The system includes user registration, authentication (MongoDB), patient record storage (SQLite), and role-based access control.

Trust boundaries exist between:
- Browser ↔ Flask application
- Flask ↔ MongoDB
- Flask ↔ SQLite
- Role boundary (patient vs admin)

Each threat is analysed with implemented mitigations and proposed future improvements.

| STRIDE Category        | Threat Example             | Impact             | Mitigation Implemented    | Additional Mitigation (Future) |
| ---------------------- | -------------------------- | ------------------ | ------------------------- | ------------------------------ |
| Spoofing               | Fake identity creation     | Fraudulent account | Password hashing (PBKDF2) | Email/identity verification    |
| Tampering              | Modify form inputs         | Data corruption    | Input validation + CSRF   | Server-side schema validation  |
| Repudiation            | User denies registration   | Audit gap          | Flash logging             | Add audit log table            |
| Information Disclosure | Password leaked in transit | Credential theft   | Hashing before storage    | Enforce HTTPS in production    |
| DoS                    | Mass registrations         | DB overload        | Basic validation          | Rate limiting / CAPTCHA        |
| Elevation of Privilege | Register as admin          | Full system access | Role default = patient    | Restrict admin creation        |

## 2️⃣ Login

| STRIDE Category | Threat | Impact | Mitigation Implemented | Additional Mitigation (Future) |
|----------------|--------|--------|------------------------|--------------------------------|
| Spoofing | Credential stuffing | Account takeover | Secure password hashing | Rate limiting |
| Tampering | Modify session cookie | Session hijacking | Server-side session validation | Signed cookies |
| Repudiation | User denies login | Accountability gap | Flash messaging | Login audit logs |
| Information Disclosure | Timing attacks | Username discovery | Generic error messages | Constant-time comparisons |
| DoS | Repeated login attempts | System overload | Basic validation | Account lockout mechanism |
| Elevation of Privilege | Session reuse | Role bypass | Session role validation | Regenerate session ID on login |

## 3️⃣ Dashboard Session

| STRIDE Category | Threat | Impact | Mitigation Implemented | Additional Mitigation (Future) |
|----------------|--------|--------|------------------------|--------------------------------|
| Spoofing | Access without authentication | Unauthorised access | Session check before rendering | Token-based authentication |
| Tampering | Manipulate session role | Admin privilege bypass | Role verified server-side | Signed session cookies |
| Repudiation | User denies viewing records | Legal risk | None | Activity logging |
| Information Disclosure | Session cookie theft | Session hijacking | HttpOnly cookies | Enforce HTTPS |
| DoS | Excessive session creation | Memory exhaustion | None | Session expiry timeout |
| Elevation of Privilege | Direct route access | Data breach | RBAC validation | Centralised permission decorators |

## 4️⃣ Admin Patients Page

| STRIDE Category | Threat | Impact | Mitigation Implemented | Additional Mitigation (Future) |
|----------------|--------|--------|------------------------|--------------------------------|
| Spoofing | Non-admin impersonates admin | Data exposure | Role-based access control | Multi-factor authentication |
| Tampering | Modify patient records | Clinical integrity risk | Admin-only restriction | Record integrity verification |
| Repudiation | Admin denies modification | Legal liability | None | Audit trail logging |
| Information Disclosure | Patient views all records | Privacy breach | Admin-only route protection | Row-level filtering |
| DoS | Large query requests | Performance degradation | Query LIMIT clause | Pagination + indexing |
| Elevation of Privilege | Direct URL access | Privilege escalation | Session + role checks | Permission decorator abstraction |

## 5️⃣ MongoDB (Authentication Database)

| STRIDE Category | Threat | Impact | Mitigation Implemented | Additional Mitigation (Future) |
|----------------|--------|--------|------------------------|--------------------------------|
| Spoofing | DB access without authentication | User database breach | MongoDB authenticated URI | IP restriction |
| Tampering | Modify password hash | Account takeover | Unique username index | Encryption at rest |
| Repudiation | User deletion without trace | Audit failure | None | Change logging |
| Information Disclosure | Password database leak | Catastrophic breach | Hashed passwords | DB-level encryption |
| DoS | Connection flooding | Service outage | Controlled access via app | Connection pooling |
| Elevation of Privilege | Direct DB manipulation | Full system control | Authenticated connection string | Role-based DB permissions |

## 6️⃣ SQLite (Patient Records Database)

| STRIDE Category | Threat | Impact | Mitigation Implemented | Additional Mitigation (Future) |
|----------------|--------|--------|------------------------|--------------------------------|
| Spoofing | Direct DB file access | Patient data exposure | Server-side access only | File permission hardening |
| Tampering | SQL injection | Data corruption | Parameterised queries | ORM enforcement |
| Repudiation | Record modification denial | Legal accountability issue | None | Timestamp + editor tracking |
| Information Disclosure | DB file theft | Privacy breach | Local dev isolation | Encryption at rest |
| DoS | Large unfiltered queries | Performance issues | LIMIT clause | Indexing strategy |
| Elevation of Privilege | Admin bypass | Data compromise | RBAC checks | Attribute-based access control |