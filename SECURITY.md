# Security Policy

Project RISING is a pilot decision-support prototype and does not accept
patient-level or other sensitive personal data. Report vulnerabilities
privately to the repository owner; do not include secrets or real health data
in an issue.

Production pilots must use HTTPS, API-key protection, explicit CORS and trusted
hosts, managed secrets, least-privilege database credentials, encrypted
backups, centralized logs, dependency scanning, and a documented key-rotation
procedure. The single shared API key is suitable only for a small controlled
pilot. Multi-user identity, roles, audit-grade access records, regulatory
review, and independent penetration testing are required before broader use.
