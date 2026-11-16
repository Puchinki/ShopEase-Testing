from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3, re, os, hashlib, secrets
from datetime import date, datetime, timedelta

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'shopease.db')
app = Flask(__name__)
CORS(app)
DEMO_OTP = '123456'  # Local practice only; never expose OTPs this way in production.


def db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with db() as con:
        con.execute('''CREATE TABLE IF NOT EXISTS registrations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            first_name TEXT NOT NULL, last_name TEXT NOT NULL, dob TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE COLLATE NOCASE,
            mobile TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'PENDING',
            created_at TEXT NOT NULL
        )''')


def error(message, status=400, field=None):
    body = {'success': False, 'message': message}
    if field: body['field'] = field
    return jsonify(body), status


def validate(payload):
    required = ['firstName', 'lastName', 'dob', 'email', 'mobile', 'password', 'confirmPassword']
    for key in required:
        if not isinstance(payload.get(key), str) or not payload[key].strip():
            return (f'{key} is required', key)
    first, last = payload['firstName'].strip(), payload['lastName'].strip()
    if not 2 <= len(first) <= 50: return ('First name must be 2 to 50 characters', 'firstName')
    if not re.fullmatch(r"[A-Za-z][A-Za-z '\-]*", first): return ('First name contains invalid characters', 'firstName')
    if not 2 <= len(last) <= 50: return ('Last name must be 2 to 50 characters', 'lastName')
    if not re.fullmatch(r"[A-Za-z][A-Za-z '\-]*", last): return ('Last name contains invalid characters', 'lastName')
    try:
        dob = date.fromisoformat(payload['dob'].strip())
        today = date.today()
        age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
        if dob >= today or age < 18: return ('Customer must be at least 18 years old', 'dob')
    except ValueError:
        return ('DOB must use YYYY-MM-DD format', 'dob')
    email = payload['email'].strip()
    if len(email) > 100 or not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", email):
        return ('Enter a valid email address (maximum 100 characters)', 'email')
    if not re.fullmatch(r'\d{10}', payload['mobile'].strip()): return ('Mobile must contain exactly 10 digits', 'mobile')
    pw = payload['password']
    if len(pw) < 8 or not re.search(r'[A-Z]', pw) or not re.search(r'[a-z]', pw) or not re.search(r'\d', pw) or not re.search(r'[^A-Za-z0-9]', pw):
        return ('Password must be at least 8 characters and include uppercase, lowercase, number and special character', 'password')
    if pw != payload['confirmPassword']: return ('Password and confirmPassword do not match', 'confirmPassword')
    if payload.get('termsAccepted') is not True: return ('Terms and conditions must be accepted', 'termsAccepted')
    return None


@app.get('/api/health')
def health():
    return jsonify({'success': True, 'service': 'ShopEase US-001 API', 'database': 'SQLite', 'status': 'running'})


@app.post('/api/register')
def register():
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict): return error('Request body must be valid JSON')
    invalid = validate(payload)
    if invalid: return error(invalid[0], 400, invalid[1])
    email, mobile = payload['email'].strip().lower(), payload['mobile'].strip()
    with db() as con:
        if con.execute('SELECT 1 FROM registrations WHERE email=?', (email,)).fetchone():
            return error('Email is already registered', 409, 'email')
        if con.execute('SELECT 1 FROM registrations WHERE mobile=?', (mobile,)).fetchone():
            return error('Mobile number is already registered', 409, 'mobile')
        pw_hash = hashlib.sha256(payload['password'].encode()).hexdigest()
        cur = con.execute('''INSERT INTO registrations
            (first_name,last_name,dob,email,mobile,password_hash,status,created_at)
            VALUES (?,?,?,?,?,?,?,?)''',
            (payload['firstName'].strip(), payload['lastName'].strip(), payload['dob'].strip(), email, mobile, pw_hash, 'PENDING', datetime.utcnow().isoformat()))
        user_id = cur.lastrowid
    return jsonify({'success': True, 'message': 'Registration details accepted. Verify the demo OTP to activate the account.',
                    'userId': user_id, 'status': 'PENDING_VERIFICATION', 'demoOtp': DEMO_OTP}), 201


@app.post('/api/verify-otp')
def verify_otp():
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict): return error('Request body must be valid JSON')
    user_id, otp = payload.get('userId'), payload.get('otp')
    if not user_id: return error('userId is required', field='userId')
    if not isinstance(otp, str) or not re.fullmatch(r'\d{6}', otp): return error('OTP must be exactly 6 digits', field='otp')
    with db() as con:
        row = con.execute('SELECT id,status FROM registrations WHERE id=?', (user_id,)).fetchone()
        if not row: return error('Registration not found', 404, 'userId')
        if row['status'] == 'ACTIVE': return error('Account is already verified', 409)
        if otp != DEMO_OTP: return error('Invalid OTP', 400, 'otp')
        con.execute("UPDATE registrations SET status='ACTIVE' WHERE id=?", (user_id,))
    return jsonify({'success': True, 'message': 'Account verified successfully', 'userId': user_id, 'status': 'ACTIVE'}), 200


@app.get('/api/users/<int:user_id>')
def get_user(user_id):
    # Practice-only inspection endpoint; does not return password data.
    with db() as con:
        row = con.execute('SELECT id,first_name,last_name,dob,email,mobile,status,created_at FROM registrations WHERE id=?', (user_id,)).fetchone()
    if not row: return error('User not found', 404)
    return jsonify({'success': True, 'user': dict(row)})


@app.post('/api/test/reset')
def reset_demo_data():
    # Local practice helper. Do not expose an endpoint like this in production.
    with db() as con: con.execute('DELETE FROM registrations')
    return jsonify({'success': True, 'message': 'Demo registration data cleared'})


if __name__ == '__main__':
    init_db()
    app.run(host='127.0.0.1', port=5000, debug=True)
