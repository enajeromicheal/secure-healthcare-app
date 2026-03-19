# STRIDE Threat Model – Secure Healthcare Record System

## System Overview

The Secure Healthcare Record System is a web application developed using Flask.

The system provides:

- User registration and authentication using MongoDB
- Patient medical record storage using SQLite
- Role-Based Access Control (RBAC) for Admin, Clinician and Patient users
- Secure session management
- Security monitoring through audit logging
- Protection against common web attacks such as CSRF and brute force login attempts

The system contains important trust boundaries where sensitive data moves between components.

---

## Trust Boundaries

The main trust boundaries in the system are:

1. Browser ↔ Flask Web Application  
2. Flask Application ↔ MongoDB Authentication Database  
3. Flask Application ↔ SQLite Patient Records Database  
4. Role Boundary (Administrator vs Clinician vs Patient)

Security controls are implemented at each boundary to reduce security risks.

---

## 1. Registration Process

| STRIDE Category | Threat | Impact | Implemented Mitigation | Future Improvement |
|-----------------|--------|--------|------------------------|-------------------|
| Spoofing | Fake identity registration | Unauthorised account creation | Password hashing using PBKDF2 | Email verification |
| Tampering | Manipulated form inputs | Incorrect data stored | Input validation and CSRF protection | Central validation schema |
| Repudiation | User denies creating account | Lack of accountability | Audit logging implemented | Log monitoring dashboard |
| Information Disclosure | Credentials intercepted | Account takeover | Secure headers and password hashing | Enforce HTTPS |
| DoS | Mass registration requests | Database overload | Rate limiting implemented | CAPTCHA protection |
| Elevation of Privilege | User registers as admin | Full system compromise | Default role enforcement | Admin approval workflow |

---

## 2. Login Process

| STRIDE Category | Threat | Impact | Implemented Mitigation | Future Improvement |
|-----------------|--------|--------|------------------------|-------------------|
| Spoofing | Credential stuffing attack | Account compromise | Secure password hashing and rate limiting | Account lockout mechanism |
| Tampering | Session cookie manipulation | Session hijacking | Server-side session validation | Signed cookies |
| Repudiation | User denies login activity | Investigation difficulty | Login audit logging | Centralised log storage |
| Information Disclosure | Username discovery attack | Targeted brute force attack | Generic error messages | Constant-time comparison |
| DoS | Repeated login attempts | System slowdown | Rate limiting protection | Web Application Firewall |
| Elevation of Privilege | Session fixation | Role bypass | Session regeneration after login | Multi-Factor Authentication |

---

## 3. Authenticated Session and Dashboard

| STRIDE Category | Threat | Impact | Implemented Mitigation | Future Improvement |
|-----------------|--------|--------|------------------------|-------------------|
| Spoofing | Access without login | Unauthorised data access | Login required decorator | Token-based authentication |
| Tampering | Session role manipulation | Privilege escalation | Role verification on each request | Signed session tokens |
| Repudiation | User denies viewing records | Legal compliance issue | Activity audit logging | Immutable log storage |
| Information Disclosure | Session cookie theft | Account takeover | HttpOnly cookies | Secure cookies + HTTPS |
| DoS | Excessive session creation | Memory exhaustion | Session timeout implemented | Distributed session store |
| Elevation of Privilege | Direct URL access | Data breach | RBAC enforcement | Attribute-Based Access Control |

---

## 4. Admin Patient Management

| STRIDE Category | Threat | Impact | Implemented Mitigation | Future Improvement |
|-----------------|--------|--------|------------------------|-------------------|
| Spoofing | Non-admin impersonation | Patient data exposure | Role-based access control | Multi-Factor Authentication |
| Tampering | Patient record modification | Clinical safety risk | Admin-only routes | Record integrity hashing |
| Repudiation | Admin denies data changes | Legal liability | Audit log tracking | Digital signatures |
| Information Disclosure | Viewing all patient records | Privacy breach | Route protection and query limits | Row-level filtering |
| DoS | Large database queries | Performance degradation | LIMIT clause in SQL queries | Pagination and indexing |
| Elevation of Privilege | URL bypass attempts | System compromise | Permission decorators | Policy-based access engine |

---

## 5. MongoDB Authentication Database

| STRIDE Category | Threat | Impact | Implemented Mitigation | Future Improvement |
|-----------------|--------|--------|------------------------|-------------------|
| Spoofing | Unauthorised database access | User database breach | Authenticated MongoDB connection string | IP whitelisting |
| Tampering | Password hash modification | Account takeover | Unique username index | Database encryption |
| Repudiation | Account deletion without trace | Audit failure | Application audit logs | Database change logging |
| Information Disclosure | Database leak | Credential exposure | Strong password hashing | Encryption at rest |
| DoS | Connection flooding | Service outage | Controlled access via application | Connection pooling |
| Elevation of Privilege | Direct database manipulation | Full system compromise | Least-privilege database account | Role-based DB permissions |

---

## 6. SQLite Patient Records Database

| STRIDE Category | Threat | Impact | Implemented Mitigation | Future Improvement |
|-----------------|--------|--------|------------------------|-------------------|
| Spoofing | Direct database file access | Patient data exposure | Server-side database access only | File permission hardening |
| Tampering | SQL injection | Data corruption | Parameterised SQL queries | ORM migration |
| Repudiation | Record modification denial | Accountability issue | Audit logging implemented | Editor tracking metadata |
| Information Disclosure | Database file theft | Privacy breach | Local development isolation | Encryption at rest |
| DoS | Large unfiltered queries | System slowdown | Query LIMIT protection | Index optimisation |
| Elevation of Privilege | Admin bypass attempts | Data compromise | RBAC checks | Fine-grained access policies |

---

## Security Testing Validation

The STRIDE mitigations were validated using automated security tests including:

- Route access testing
- Role-based access testing
- Authentication testing
- Session logout validation
- Rate-limiting behaviour testing

These tests demonstrate that implemented controls reduce identified risks and improve system security posture.
