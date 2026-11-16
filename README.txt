SHOPEASE - US-001 USER REGISTRATION DEMO
========================================

WHAT THIS IS
------------
A small browser application for practising functional testing of US-001: Register a new customer account.
It includes registration fields, field-level validation, case-insensitive duplicate email checking, duplicate mobile checking, simulated OTP verification and a success confirmation.

HOW TO RUN (RECOMMENDED)
------------------------
1. Extract the ZIP file to a folder on your computer.
2. Make sure Python 3 is installed.
3. Open Command Prompt (Windows) or Terminal (Mac/Linux).
4. Change directory to the extracted shopease_us001 folder. Example on Windows:
      cd Downloads\shopease_us001
5. Start a local web server:
      py -m http.server 8000
   If that command does not work, try:
      python -m http.server 8000
6. Open Chrome and visit:
      http://localhost:8000
7. You should see the ShopEase registration page.
8. To stop the server, return to the command window and press Ctrl+C.

DEMO TEST DATA
--------------
Valid sample:
First name: Asha
Last name: Sharma
Date of birth: 1995-04-15
Email: asha.demo@example.com
Mobile: 9876543210
Password: Test@1234
Confirm password: Test@1234
Terms: checked
Demo OTP: 123456

Other examples from the business requirements:
Duplicate email: asha.demo@example.com (after successfully registering it once)
Invalid email: asha.demo@ or asha.example.com
Invalid mobile: 987654321 or 98AB543210
Invalid password: test1234 or TEST@1234
Invalid OTP: 000000

IMPORTANT IMPLEMENTATION NOTES
------------------------------
1. The business requirements specify the fixed demo OTP 123456 but do not define an expiry duration. This build uses a 5-minute OTP expiry as an explicit practice assumption. The expiry is shown on the OTP screen.
2. OTP delivery is simulated. No real SMS is sent.
3. Accounts are stored in this browser's localStorage. They do not sync to another browser or computer. Use the same browser profile for repeat tests.
4. The password is not stored in plain text. This demo stores a salted SHA-256 hash to support the registration exercise. This is NOT production-grade password storage. A real application must use a secure server-side password hashing method such as Argon2id, bcrypt or scrypt, with suitable rate limiting and account protections.
5. This is a front-end practice build, not a production service. Personal information should not be entered; use only fictional test data.
6. The app implements US-001 only. Sign-in, profile, address book, shopping and other user stories are not included in this first build.

RESETTING TEST DATA
-------------------
Use the "Reset all local demo accounts" link in the right-hand information panel. Confirm the browser prompt to remove all registered demo accounts from this browser. You can then repeat the registration scenarios from a clean state.

SCOPE NOTE
----------
The application follows the US-001 business requirements in the ShopEase requirements pack. Where a rule was not specified (OTP expiry), the assumption is documented above so that it can be reviewed rather than treated as an original business requirement.
