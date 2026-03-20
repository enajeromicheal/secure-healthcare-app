## Security Evaluation and Residual Risk

This system was evaluated against common web security threats and healthcare data protection requirements. Several important security controls have been successfully implemented to reduce risk.

### Implemented Security Controls

**Authentication Security**
- Passwords are securely hashed using PBKDF2 via Werkzeug.
- Unique username enforcement prevents duplicate accounts.
- Login rate limiting is implemented to reduce brute-force attacks.
- Temporary passwords can be issued for newly created patient accounts.

**Session Security**
- Session-based authentication protects sensitive routes.
- Session timeout is enforced using permanent session lifetime settings.
- Session data is cleared during logout to prevent session reuse.

**Access Control**
- Role-Based Access Control (RBAC) is implemented.
- Only administrators can access the patient management page.
- Unauthorized users are redirected to an Access Denied page.

**Audit Logging**
- Critical system actions such as viewing, editing, and deleting patient records are logged in the `audit_logs` table.
- Each log entry records the username, action performed, and timestamp.
- This improves accountability and supports forensic investigation.

**Web Security Protections**
- CSRF protection is enabled using Flask-WTF.
- Secure HTTP headers (CSP, HSTS, X-Frame-Options) are enforced using Flask-Talisman.
- Environment variables are used to protect sensitive configuration such as the secret key.

### Residual Security Risks

Despite the implemented protections, some risks remain:

- Login rate limiting is stored in application memory and resets if the server restarts.
- Account lockout after repeated failed login attempts is not yet implemented.
- Password complexity rules are limited and could be strengthened.
- SQLite database encryption at rest is not enabled.
- No distributed session storage is used (e.g., Redis).
- Advanced monitoring and alerting mechanisms are not implemented.

### Recommended Future Improvements

- Implement persistent rate limiting using Redis or database storage.
- Add account lockout functionality after multiple failed login attempts.
- Enforce stronger password complexity policies.
- Use encrypted databases such as SQLCipher for sensitive healthcare data.
- Introduce structured logging and security monitoring tools.
- Apply pagination and query optimisation for large patient datasets.

Overall, the system demonstrates a secure foundation suitable for a prototype healthcare application, with clear opportunities for further enhancement in a production environment.