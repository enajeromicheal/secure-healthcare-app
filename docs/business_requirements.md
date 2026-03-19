# Business Requirements and Stakeholders

This system supports secure healthcare record management.

## Administrator

Responsibilities:
- Create patient accounts
- Reset passwords
- Deactivate users
- View and edit patient records

Security Needs:
- Strong authentication
- Restricted access to admin routes
- Audit logging

## Clinician

Responsibilities:
- View patient records
- Create prescriptions
- View appointments

Security Needs:
- Cannot perform admin tasks
- Access limited to authorised data
- All actions traceable

## Patient

Responsibilities:
- View personal record
- Book appointments
- View prescriptions
- Change password

Security Needs:
- Cannot access other records
- Session security
- Data confidentiality

## System Logic

The system enforces Role-Based Access Control (RBAC).  
Permissions are assigned based on user role to protect healthcare data.