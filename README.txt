SHOPEASE US-001 + US-002 BACKEND (LOCAL PRACTICE)
==================================================

Requirements: Python 3.9+

1) Open a terminal in this folder.
2) (Recommended) Create and activate a virtual environment:
   Windows:     py -m venv .venv
                .venv\Scripts\activate
   macOS/Linux: python3 -m venv .venv
                source .venv/bin/activate
3) Install dependencies:
   py -m pip install -r requirements.txt
4) Start the API:
   py app.py
5) Keep the terminal open. API base URL: http://127.0.0.1:5000
6) Check in browser: http://127.0.0.1:5000/api/health


FRONTEND PAGES (open in browser)
--------------------------------
Registration  : index.html
Sign-In       : signin.html    (US-002, new)
Dashboard     : dashboard.html (US-002, new — protected)

You can either:
  a) Open these HTML files via VS Code Live Server (usually http://127.0.0.1:5500), OR
  b) Open http://127.0.0.1:5000/signin.html and /dashboard.html directly from Flask.

CORS in app.py already allows both http://127.0.0.1:5500 and http://localhost:5500.
If your Live Server uses a different port, add it to the origins=[...] list in app.py.


POSTMAN ENDPOINTS
-----------------
US-001:
GET  http://127.0.0.1:5000/api/health
POST http://127.0.0.1:5000/api/register
POST http://127.0.0.1:5000/api/verify-otp
GET  http://127.0.0.1:5000/api/users/1
POST http://127.0.0.1:5000/api/test/reset

US-002 (new):
POST http://127.0.0.1:5000/api/signin
GET  http://127.0.0.1:5000/api/me           (session cookie required)
POST http://127.0.0.1:5000/api/signout


US-001 — REGISTER request (Body > raw > JSON)
---------------------------------------------
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
Returns HTTP 201 + userId. Account status is PENDING until OTP verification.

US-001 — VERIFY request (Body > raw > JSON)
-------------------------------------------
{ "userId": 1, "otp": "123456" }
Returns HTTP 200 and ACTIVE status.

US-002 — SIGN-IN request (Body > raw > JSON)
--------------------------------------------
{ "email": "asha.demo@example.com", "password": "Test@1234" }
Returns HTTP 200 with session cookie on success.

US-002 rules:
- Email is case-insensitive; password is case-sensitive.
- Wrong email AND wrong password both return "Invalid email or password."
  (no field-existence disclosure).
- 5 consecutive wrong passwords → account locked for 15 minutes (HTTP 423).
- Lockout is per-account (registrations.failed_attempts + lockout_until).
- Successful sign-in resets the counter and starts a 30-minute session cookie.
- Account must be ACTIVE (OTP-verified) to sign in. PENDING accounts get the
  same generic message.


MANUAL TEST FLOW
----------------
1. Open index.html → click "Reset all demo accounts" (optional, clears DB)
2. Register Asha (asha.demo@example.com / Test@1234) → verify OTP 123456
3. Open signin.html → sign in with the same credentials
4. Land on dashboard.html → click Sign Out → back to signin.html

Tricky cases:
- 5 × wrong password → 6th attempt (even with correct password) returns 423.
- Wait 15 min OR click "Reset all demo accounts" → account unlocks.
- Unverified (PENDING) account → generic "Invalid email or password."
- Email in UPPERCASE (ASHA.DEMO@EXAMPLE.COM) → still succeeds.
- Password in different case (test@1234) → fails (case-sensitive).


IMPORTANT DEMO LIMITATIONS
--------------------------
- OTP is fixed to 123456 and returned in the registration response. No SMS.
- Passwords use SHA-256 (demo only). Use Argon2/bcrypt/scrypt in production.
- Flask signed-cookie sessions (no Redis). Fine for local practice only.
- /api/users/<id> and /api/test/reset are test helpers — never expose in prod.
- Do not commit the SECRET_KEY or DB password; use environment variables.
- CORS origins list in app.py must match your frontend port exactly.