from flask import Flask, request, jsonify
from flask_cors import CORS
import mysql.connector
import re, os, hashlib
from datetime import date, datetime

app = Flask(__name__)
CORS(app)
DEMO_OTP = '123456'

# --- MySQL configuration (adjust to your environment) ---
DB_CONFIG = {
    'host':     os.getenv('DB_HOST', '127.0.0.1'),
    'port':     int(os.getenv('DB_PORT', 3306)),
    'user':     os.getenv('DB_USER', 'root'),
    'password': os.getenv('DB_PASSWORD', 'Root@123'),
    'database': os.getenv('DB_NAME', 'shopease'),
    'autocommit': False,
}


def db():
    """Return a MySQL connection with dictionary-style rows."""
    return mysql.connector.connect(**DB_CONFIG)


def init_db():
    con = db()
    try:
        cur = con.cursor()
        cur.execute('''
            CREATE TABLE IF NOT EXISTS registrations (
                id            INT AUTO_INCREMENT PRIMARY KEY,
                first_name    VARCHAR(50)  NOT NULL,
                last_name     VARCHAR(50)  NOT NULL,
                dob           DATE         NOT NULL,
                email         VARCHAR(100) NOT NULL,
                mobile        VARCHAR(10)  NOT NULL,
                password_hash CHAR(64)     NOT NULL,
                status        VARCHAR(20)  NOT NULL DEFAULT 'PENDING',
                created_at    DATETIME     NOT NULL,
                UNIQUE KEY uq_email  (email),
                UNIQUE KEY uq_mobile (mobile)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        ''')
        con.commit()
    finally:
        con.close()


def error(message, status=400, field=None):
    body = {'success': False, 'message': message}
    if field:
        body['field'] = field
    return jsonify(body), status


def validate(payload):
    required = ['firstName', 'lastName', 'dob', 'email', 'mobile',
                'password', 'confirmPassword']
    for key in required:
        if not isinstance(payload.get(key), str) or not payload[key].strip():
            return (f'{key} is required', key)

    first, last = payload['firstName'].strip(), payload['lastName'].strip()
    if not 2 <= len(first) <= 50:
        return ('First name must be 2 to 50 characters', 'firstName')
    if not re.fullmatch(r"[A-Za-z][A-Za-z '\-]*", first):
        return ('First name contains invalid characters', 'firstName')
    if not 2 <= len(last) <= 50:
        return ('Last name must be 2 to 50 characters', 'lastName')
    if not re.fullmatch(r"[A-Za-z][A-Za-z '\-]*", last):
        return ('Last name contains invalid characters', 'lastName')

    try:
        dob = date.fromisoformat(payload['dob'].strip())
        today = date.today()
        age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
        if dob >= today or age < 18:
            return ('Customer must be at least 18 years old', 'dob')
    except ValueError:
        return ('DOB must use YYYY-MM-DD format', 'dob')

    email = payload['email'].strip()
    if len(email) > 100 or not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", email):
        return ('Enter a valid email address (maximum 100 characters)', 'email')

    if not re.fullmatch(r'\d{10}', payload['mobile'].strip()):
        return ('Mobile must contain exactly 10 digits', 'mobile')

    pw = payload['password']
    if (len(pw) < 8 or not re.search(r'[A-Z]', pw) or
            not re.search(r'[a-z]', pw) or not re.search(r'\d', pw) or
            not re.search(r'[^A-Za-z0-9]', pw)):
        return ('Password must be at least 8 characters and include uppercase, '
                'lowercase, number and special character', 'password')
    if pw != payload['confirmPassword']:
        return ('Password and confirmPassword do not match', 'confirmPassword')
    if payload.get('termsAccepted') is not True:
        return ('Terms and conditions must be accepted', 'termsAccepted')
    return None


@app.get('/api/health')
def health():
    return jsonify({
        'success': True,
        'service': 'ShopEase US-001 API',
        'database': 'MySQL',
        'status': 'running',
    })


@app.post('/api/register')
def register():
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return error('Request body must be valid JSON')
    invalid = validate(payload)
    if invalid:
        return error(invalid[0], 400, invalid[1])

    email, mobile = payload['email'].strip().lower(), payload['mobile'].strip()
    pw_hash = hashlib.sha256(payload['password'].encode()).hexdigest()

    con = db()
    try:
        cur = con.cursor(dictionary=True)
        cur.execute('SELECT 1 FROM registrations WHERE email=%s', (email,))
        if cur.fetchone():
            return error('Email is already registered', 409, 'email')

        cur.execute('SELECT 1 FROM registrations WHERE mobile=%s', (mobile,))
        if cur.fetchone():
            return error('Mobile number is already registered', 409, 'mobile')

        cur = con.cursor()
        cur.execute('''
            INSERT INTO registrations
                (first_name, last_name, dob, email, mobile,
                 password_hash, status, created_at)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
        ''', (
            payload['firstName'].strip(),
            payload['lastName'].strip(),
            payload['dob'].strip(),
            email,
            mobile,
            pw_hash,
            'PENDING',
            datetime.utcnow(),
        ))
        user_id = cur.lastrowid
        con.commit()
    except mysql.connector.IntegrityError as e:
        con.rollback()
        # Safety net if a race condition hits a unique constraint
        if 'uq_email' in str(e) or 'email' in str(e).lower():
            return error('Email is already registered', 409, 'email')
        if 'uq_mobile' in str(e) or 'mobile' in str(e).lower():
            return error('Mobile number is already registered', 409, 'mobile')
        return error('Database constraint error', 409)
    finally:
        con.close()

    return jsonify({
        'success': True,
        'message': ('Registration details accepted. Verify the demo OTP '
                    'to activate the account.'),
        'userId': user_id,
        'status': 'PENDING_VERIFICATION',
        'demoOtp': DEMO_OTP,
    }), 201


@app.post('/api/verify-otp')
def verify_otp():
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return error('Request body must be valid JSON')

    user_id, otp = payload.get('userId'), payload.get('otp')
    if not user_id:
        return error('userId is required', field='userId')
    if not isinstance(otp, str) or not re.fullmatch(r'\d{6}', otp):
        return error('OTP must be exactly 6 digits', field='otp')

    con = db()
    try:
        cur = con.cursor(dictionary=True)
        cur.execute('SELECT id, status FROM registrations WHERE id=%s', (user_id,))
        row = cur.fetchone()
        if not row:
            return error('Registration not found', 404, 'userId')
        if row['status'] == 'ACTIVE':
            return error('Account is already verified', 409)
        if otp != DEMO_OTP:
            return error('Invalid OTP', 400, 'otp')

        cur = con.cursor()
        cur.execute("UPDATE registrations SET status='ACTIVE' WHERE id=%s", (user_id,))
        con.commit()
    finally:
        con.close()

    return jsonify({
        'success': True,
        'message': 'Account verified successfully',
        'userId': user_id,
        'status': 'ACTIVE',
    }), 200


@app.get('/api/users/<int:user_id>')
def get_user(user_id):
    con = db()
    try:
        cur = con.cursor(dictionary=True)
        cur.execute('''
            SELECT id, first_name, last_name, dob, email, mobile,
                   status, created_at
            FROM registrations
            WHERE id=%s
        ''', (user_id,))
        row = cur.fetchone()
    finally:
        con.close()

    if not row:
        return error('User not found', 404)

    # Convert non-JSON-serializable types
    if isinstance(row.get('dob'), date):
        row['dob'] = row['dob'].isoformat()
    if isinstance(row.get('created_at'), datetime):
        row['created_at'] = row['created_at'].isoformat()

    return jsonify({'success': True, 'user': row})


@app.post('/api/test/reset')
def reset_demo_data():
    con = db()
    try:
        cur = con.cursor()
        cur.execute('DELETE FROM registrations')
        con.commit()
    finally:
        con.close()
    return jsonify({'success': True, 'message': 'Demo registration data cleared'})


if __name__ == '__main__':
    init_db()
    app.run(host='127.0.0.1', port=5000, debug=True)