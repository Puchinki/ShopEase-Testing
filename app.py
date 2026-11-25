from flask import Flask, request, jsonify, session, send_from_directory
from flask_cors import CORS
import mysql.connector
import re, os, hashlib
from datetime import date, datetime, timedelta

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'shopease-us002-dev-secret')
app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Lax',
    SESSION_COOKIE_SECURE=False,
    PERMANENT_SESSION_LIFETIME=timedelta(minutes=30),
)
CORS(app, supports_credentials=True,
     origins=['http://127.0.0.1:5500', 'http://localhost:5500',
              'http://127.0.0.1:5000', 'http://localhost:5000'])
DEMO_OTP = '123456'

# US-002 constants
MAX_ATTEMPTS = 5
LOCKOUT_MINUTES = 15
GENERIC_ERROR = 'Invalid email or password.'
LOCKOUT_ERROR = ('Too many failed attempts. Sign-in is temporarily blocked. '
                 'Please try again after 15 minutes.')

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
                id              INT AUTO_INCREMENT PRIMARY KEY,
                first_name      VARCHAR(50)  NOT NULL,
                last_name       VARCHAR(50)  NOT NULL,
                dob             DATE         NOT NULL,
                email           VARCHAR(100) NOT NULL,
                mobile          VARCHAR(10)  NOT NULL,
                password_hash   CHAR(64)     NOT NULL,
                status          VARCHAR(20)  NOT NULL DEFAULT 'PENDING',
                created_at      DATETIME     NOT NULL,
                failed_attempts INT          NOT NULL DEFAULT 0,
                lockout_until   DATETIME     NULL,
                UNIQUE KEY uq_email  (email),
                UNIQUE KEY uq_mobile (mobile)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        ''')
        con.commit()

        # Safe migration for existing DBs created before US-002
        cur.execute("""
            SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'registrations'
        """)
        cols = {r[0] for r in cur.fetchall()}
        if 'failed_attempts' not in cols:
            cur.execute("ALTER TABLE registrations ADD COLUMN failed_attempts INT NOT NULL DEFAULT 0")
        if 'lockout_until' not in cols:
            cur.execute("ALTER TABLE registrations ADD COLUMN lockout_until DATETIME NULL")
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


# ══════════════════════════════════════════════════════════════════
# US-001 — Registration, OTP verification, user lookup
# ══════════════════════════════════════════════════════════════════

@app.get('/api/health')
def health():
    return jsonify({
        'success': True,
        'service': 'ShopEase US-001 + US-002 API',
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
                 password_hash, status, created_at,
                 failed_attempts, lockout_until)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        ''', (
            payload['firstName'].strip(),
            payload['lastName'].strip(),
            payload['dob'].strip(),
            email,
            mobile,
            pw_hash,
            'PENDING',
            datetime.utcnow(),
            0,
            None,
        ))
        user_id = cur.lastrowid
        con.commit()
    except mysql.connector.IntegrityError as e:
        con.rollback()
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


# ══════════════════════════════════════════════════════════════════
# US-002 — Sign in to an existing account
# ══════════════════════════════════════════════════════════════════

@app.post('/api/signin')
def signin():
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return error('Request body must be valid JSON')

    email = (payload.get('email') or '').strip()
    password = payload.get('password') or ''

    errors = {}
    if not email:
        errors['email'] = 'Email is required.'
    elif not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", email):
        errors['email'] = 'Enter a valid email address.'
    if not password:
        errors['password'] = 'Password is required.'
    if errors:
        return jsonify({'success': False,
                        'message': 'Please fix the highlighted fields.',
                        'errors': errors}), 400

    email = email.lower()
    pw_hash = hashlib.sha256(password.encode()).hexdigest()

    con = db()
    try:
        cur = con.cursor(dictionary=True)
        cur.execute('''
            SELECT id, email, password_hash, status,
                   COALESCE(failed_attempts, 0) AS failed_attempts,
                   lockout_until
            FROM registrations
            WHERE email=%s
        ''', (email,))
        user = cur.fetchone()

        # No email-existence disclosure: unknown OR non-ACTIVE → same message
        if not user or user['status'] != 'ACTIVE':
            return error(GENERIC_ERROR, 401)

        now = datetime.utcnow()

        # Lockout still active?
        if user['lockout_until'] and now < user['lockout_until']:
            remaining = int((user['lockout_until'] - now).total_seconds())
            return jsonify({'success': False,
                            'message': LOCKOUT_ERROR,
                            'remainingSeconds': remaining}), 423

        # Lockout expired → reset counters
        if user['lockout_until'] and now >= user['lockout_until']:
            cur = con.cursor()
            cur.execute('UPDATE registrations SET failed_attempts=0, '
                        'lockout_until=NULL WHERE id=%s', (user['id'],))
            con.commit()
            user['failed_attempts'] = 0
            user['lockout_until'] = None

        # Case-sensitive password compare (SHA-256 is exact)
        if pw_hash != user['password_hash']:
            attempts = user['failed_attempts'] + 1
            if attempts >= MAX_ATTEMPTS:
                lock_until = now + timedelta(minutes=LOCKOUT_MINUTES)
                cur = con.cursor()
                cur.execute('UPDATE registrations SET failed_attempts=%s, '
                            'lockout_until=%s WHERE id=%s',
                            (attempts, lock_until, user['id']))
                con.commit()
                return jsonify({'success': False,
                                'message': LOCKOUT_ERROR,
                                'remainingSeconds': LOCKOUT_MINUTES * 60}), 423

            cur = con.cursor()
            cur.execute('UPDATE registrations SET failed_attempts=%s WHERE id=%s',
                        (attempts, user['id']))
            con.commit()
            return jsonify({
                'success': False,
                'message': GENERIC_ERROR,
                'attemptsLeft': MAX_ATTEMPTS - attempts,
            }), 401

        # ✅ Success — reset counter
        cur = con.cursor()
        cur.execute('UPDATE registrations SET failed_attempts=0, '
                    'lockout_until=NULL WHERE id=%s', (user['id'],))
        con.commit()
    finally:
        con.close()

    session.permanent = True
    session['user'] = {'id': user['id'], 'email': user['email']}

    return jsonify({
        'success': True,
        'message': 'Signed in successfully.',
        'redirectTo': 'dashboard.html',
        'user': {'id': user['id'], 'email': user['email']},
    }), 200


@app.get('/api/me')
def me():
    if 'user' not in session:
        return error('Not authenticated.', 401)
    return jsonify({'success': True, 'user': session['user']})


@app.post('/api/signout')
def signout():
    session.clear()
    return jsonify({'success': True, 'message': 'Signed out.'})


# ══════════════════════════════════════════════════════════════════
# Static HTML pages served from Flask
# ══════════════════════════════════════════════════════════════════

@app.get('/')
@app.get('/index.html')
def serve_index():
    return send_from_directory(os.path.dirname(os.path.abspath(__file__)), 'index.html')


@app.get('/signin.html')
def serve_signin():
    return send_from_directory(os.path.dirname(os.path.abspath(__file__)), 'signin.html')


@app.get('/dashboard.html')
def serve_dashboard():
    return send_from_directory(os.path.dirname(os.path.abspath(__file__)), 'dashboard.html')


if __name__ == '__main__':
    init_db()
    app.run(host='127.0.0.1', port=5000, debug=True)