# Security Evaluation & Residual Risk Analysis

## 1. Evaluation of Implemented Security Controls

This system applies multiple secure programming techniques aligned with identified threats in the STRIDE model.

### Authentication Security

Passwords are hashed using PBKDF2 via Werkzeug before being stored in MongoDB. This prevents plaintext credential exposure in the event of database compromise. A unique index on usernames prevents duplicate account creation.

Strength:
- Mitigates credential disclosure
- Reduces risk of account takeover via database leak

Limitation:
- No rate limiting against brute force attacks
- No multi-factor authentication

---

### Session Management

The system validates session presence before granting access to protected routes such as `/dashboard` and `/patients`. Role-based access control (RBAC) ensures only administrators can access sensitive patient records.

Strength:
- Prevents unauthenticated access
- Enforces separation of privileges

Limitation:
- Session IDs are not rotated on login
- No session timeout implemented

---

### Input Validation & Injection Protection

SQLite queries use parameterised statements to prevent SQL injection. CSRF protection is enabled to prevent cross-site request forgery.

Strength:
- Protects against common web injection attacks
- Aligns with OWASP secure coding principles

Limitation:
- No centralised input validation schema
- Limited sanitisation beyond required fields

---

### Secure Headers

Flask-Talisman is used to enforce:
- Content Security Policy (CSP)
- HTTP Strict Transport Security (HSTS)
- Clickjacking protection

Strength:
- Protects against client-side attack vectors
- Improves transport security posture

Limitation:
- HTTPS enforcement depends on deployment environment

---

## 2. Residual Risks

Despite implemented controls, residual risks remain:

1. Brute force login attempts (no rate limiting)
2. Lack of audit logging for user actions
3. No encryption at rest for SQLite database
4. No multi-factor authentication for admin users
5. No monitoring or intrusion detection mechanisms

These risks are acceptable within a coursework prototype but would require mitigation in a production healthcare environment.

---

## 3. Security Maturity Assessment

The system demonstrates:

- Authentication hardening
- Role-based access control
- Threat-driven design (STRIDE)
- Secure coding practices
- Clear trust boundary definition

However, it does not yet implement:

- Defence-in-depth layering
- Operational monitoring
- Advanced identity assurance mechanisms

Overall, the security posture aligns with a secure prototype suitable for academic demonstration but would require further hardening for clinical deployment.