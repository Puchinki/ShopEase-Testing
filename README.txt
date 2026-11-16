SHOPEASE US-001 BACKEND (LOCAL PRACTICE)

Requirements: Python 3.9+

1) Open a terminal in this folder.
2) (Recommended) Create and activate a virtual environment:
   Windows: py -m venv .venv
            .venv\Scripts\activate
   macOS/Linux: python3 -m venv .venv
                source .venv/bin/activate
3) Install dependencies:
   py -m pip install -r requirements.txt
4) Start the API:
   py app.py
5) Keep the terminal open. API base URL: http://127.0.0.1:5000
6) Check in browser: http://127.0.0.1:5000/api/health

POSTMAN ENDPOINTS
GET  http://127.0.0.1:5000/api/health
POST http://127.0.0.1:5000/api/register
POST http://127.0.0.1:5000/api/verify-otp
GET  http://127.0.0.1:5000/api/users/1
POST http://127.0.0.1:5000/api/test/reset

REGISTER request: Body > raw > JSON
{
  "firstName": "Asha",
  "lastName": "Sharma",
  "dob": "1995-04-15",
  "email": "asha.demo@example.com",
  "mobile": "9876543210",
  "password": "Test@1234",
  "confirmPassword": "Test@1234",
  "termsAccepted": true
}

A successful registration returns HTTP 201 and a userId. Account status remains PENDING until OTP verification.
VERIFY request: Body > raw > JSON
{ "userId": 1, "otp": "123456" }
Successful verification returns HTTP 200 and ACTIVE status.

IMPORTANT DEMO LIMITATIONS
- OTP is fixed to 123456 and included in the registration response for practice. No real SMS/email is sent.
- SQLite database file shopease.db is created automatically beside app.py.
- Passwords are hashed for this demo, but use a production password-hashing algorithm (Argon2/bcrypt/scrypt) and proper secret/OTP handling in a real system.
- /api/users/<id> and /api/test/reset are test-only helpers. Never expose these as-is in production.
- This backend is a separate API from the existing static HTML page. Postman calls the API directly. The current HTML file has not yet been wired to call this backend.
- For repeat tests, use a new email and mobile number, or call POST /api/test/reset to clear demo data.
