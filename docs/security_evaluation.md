# Security Evaluation and Residual Risk Analysis  
Secure Healthcare Record System

## 1. Evaluation of Implemented Security Controls

The Secure Healthcare Record System applies several secure programming techniques based on threats identified during the STRIDE threat modelling process.  
These controls aim to protect sensitive healthcare data, user credentials, and system functionality.

---

### Authentication Security

User passwords are securely hashed using the PBKDF2 algorithm provided by Werkzeug before being stored in MongoDB.  
This ensures that passwords are never stored in plaintext and reduces the risk of credential exposure if the authentication database is compromised.

Additionally, a unique index is enforced on usernames to prevent duplicate account creation and identity confusion.

**Strengths**

- Protects against credential disclosure
- Reduces risk of account takeover following database breach
- Supports secure user identity management

**Limitations**

- Multi-Factor Authentication is not implemented
- Advanced account lockout policies are limited
- Identity verification (such as email confirmation) is not present

---

### Session Management and Access Control

The system uses server-side session validation to ensure that only authenticated users can access protected routes such as `/dashboard` and `/patients`.  
Role-Based Access Control (RBAC) is implemented to ensure that only authorised administrators can view or manage patient records.

Sessions are cleared during logout, reducing the risk of session reuse attacks.

**Strengths**

- Prevents unauthorised access to sensitive healthcare data
- Enforces separation of privileges between user roles
- Protects against direct URL access attempts

**Limitations**

- Session timeout duration is basic and can be improved
- Token-based authentication is not implemented
- Advanced session monitoring mechanisms are not present

---

### Input Validation and Injection Protection

All SQLite database queries use parameterised statements to prevent SQL injection attacks.  
CSRF protection is enabled to prevent attackers from performing unauthorised actions using forged requests.

These controls align with OWASP secure coding recommendations.

**Strengths**

- Protects against common database injection attacks
- Ensures safer handling of user input
- Improves overall application integrity

**Limitations**

- No centralised validation framework across all routes
- Limited input sanitisation beyond required form fields

---

### Secure Headers and Client-Side Protection

Flask-Talisman is used to enforce important HTTP security headers, including:

- Content Security Policy (CSP)
- HTTP Strict Transport Security (HSTS)
- Clickjacking protection using frame restrictions

These headers help reduce the risk of browser-based attacks such as cross-site scripting and man-in-the-middle attacks.

**Strengths**

- Improves browser-side security posture
- Encourages secure HTTPS communication
- Protects against UI redressing attacks

**Limitations**

- Full HTTPS enforcement depends on production deployment configuration
- Some policies may require tuning for real-world environments

---

### Audit Logging and Security Monitoring

The system records important user actions such as login attempts and sensitive operations within an audit logging mechanism.  
This supports accountability and security incident investigation.

**Strengths**

- Provides traceability of user activities
- Supports repudiation mitigation
- Enhances system transparency

**Limitations**

- No real-time monitoring dashboard
- Logs are not yet protected against tampering

---

## 2. Residual Risks

Despite the implemented controls, some residual risks remain due to the prototype nature of the system:

1. Limited protection against highly distributed brute force attacks  
2. No encryption at rest for the SQLite patient database  
3. Absence of Multi-Factor Authentication for privileged users  
4. Lack of intrusion detection and automated threat monitoring  
5. Basic session management compared to enterprise healthcare systems  
6. No disaster recovery or database backup strategy  
7. Limited defence-in-depth architecture

These risks are considered acceptable within an academic prototype but would require mitigation before deployment in a real clinical environment.

---

## 3. Security Maturity Assessment

Overall, the system demonstrates a structured and threat-driven security design approach.

The following maturity characteristics are present:

- STRIDE-based threat modelling
- Role-Based Access Control implementation
- Secure password storage practices
- Input validation and CSRF protection
- Secure HTTP headers enforcement
- Automated security testing
- Audit logging for accountability
- Clear trust boundary identification

However, the system would require further hardening to reach production-level healthcare security standards.  
Future improvements should include advanced authentication mechanisms, continuous monitoring, encryption strategies, and stronger operational security controls.

---

## Conclusion

The Secure Healthcare Record System achieves a strong security foundation suitable for academic demonstration.  
While residual risks remain, the implemented safeguards significantly reduce common web application threats and demonstrate an understanding of secure software engineering principles.