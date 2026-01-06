import os
from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS
import psycopg
from datetime import datetime, timedelta
import hashlib

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'change-this-in-production')
CORS(app, resources={r"/api/*": {"origins": "*"}})

# ==================== DATABASE CONFIG ====================
def get_conn():
    """Veritabanı bağlantısı oluştur"""
    try:
        conn_string = os.getenv('DATABASE_URL')
        
        if not conn_string:
            raise Exception("DATABASE_URL ortam değişkeni ayarlanmamış!")
        
        conn = psycopg.connect(
            conn_string,
            sslmode="require",
            connect_timeout=20,
            keepalives=1,
            keepalives_idle=30
        )
        return conn
    except Exception as e:
        print(f"❌ Veritabanı bağlantı hatası: {str(e)}")
        raise

def hash_password(password):
    """Şifreyi hash'le"""
    return hashlib.sha256(password.encode()).hexdigest()

def calculate_duration(start_str, end_str):
    """Başlangıç ve bitiş saati arasındaki süreyi hesapla"""
    try:
        start = datetime.strptime(start_str, "%H:%M")
        end = datetime.strptime(end_str, "%H:%M")
        if end < start:
            end += timedelta(days=1)
        total_minutes = int((end - start).total_seconds() / 60)
        hours = total_minutes // 60
        minutes = total_minutes % 60
        return f"{hours}h {minutes}m"
    except:
        return "Hesaplanamadı"

# ==================== DATABASE INITIALIZATION ====================
def init_db():
    """Veritabanı tablolarını oluştur/kontrol et"""
    try:
        conn = get_conn()
        cur = conn.cursor()
        
        # Users tablosu
        cur.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                email VARCHAR(255) UNIQUE NOT NULL,
                password VARCHAR(255) NOT NULL,
                name VARCHAR(255) NOT NULL,
                employee_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Employees tablosu
        cur.execute('''
            CREATE TABLE IF NOT EXISTS employees (
                id SERIAL PRIMARY KEY,
                name VARCHAR(255) UNIQUE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Attendance tablosu
        cur.execute('''
            CREATE TABLE IF NOT EXISTS attendance (
                id SERIAL PRIMARY KEY,
                employee_id INTEGER NOT NULL,
                employee_name TEXT,
                date DATE,
                start_time TIME,
                end_time TIME,
                location TEXT,
                duration TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (employee_id) REFERENCES employees(id)
            )
        ''')
        
        conn.commit()
        cur.close()
        conn.close()
        print("✅ Tablolar başarıyla oluşturuldu/kontrol edildi.")
        return True
    except Exception as e:
        print(f"❌ Tablo oluşturma hatası: {str(e)}")
        return False

# ==================== LOGIN PAGE ====================
@app.route('/')
def index():
    return '''<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=5.0, user-scalable=yes">
    <title>🎯 PROSPANDO - Giriş</title>
    <style>
        * { 
            margin: 0; 
            padding: 0; 
            box-sizing: border-box; 
        }
        
        body {
            font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
            background: #0f172a;
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 20px;
            position: relative;
            overflow-x: hidden;
        }

        body::before {
            content: '';
            position: absolute;
            top: 0; left: 0; right: 0; bottom: 0;
            background: 
                radial-gradient(circle at 20% 80%, #7c3aed 0%, transparent 50%),
                radial-gradient(circle at 80% 20%, #ec4899 0%, transparent 50%),
                radial-gradient(circle at 50% 50%, #3b82f6 0%, transparent 40%);
            opacity: 0.5;
            z-index: -1;
            animation: pulse 18s ease infinite;
        }

        @keyframes pulse {
            0%, 100% { opacity: 0.5; }
            50% { opacity: 0.7; }
        }

        .container {
            background: rgba(15, 23, 42, 0.85);
            backdrop-filter: blur(20px);
            -webkit-backdrop-filter: blur(20px);
            border-radius: 32px;
            box-shadow: 
                0 0 50px rgba(124, 58, 237, 0.4),
                0 25px 80px rgba(0, 0, 0, 0.5),
                inset 0 0 30px rgba(255, 255, 255, 0.05);
            max-width: 500px;
            width: 100%;
            max-height: 90vh;          
            overflow-y: auto;        
            overflow-x: hidden;    
            border: 1px solid rgba(124, 58, 237, 0.3);
            position: relative;
        }

        .header {
            background: linear-gradient(135deg, #7c3aed, #ec4899);
            padding: 50px 30px;
            text-align: center;
            color: white;
            position: relative;
            overflow: hidden;
            border-radius: 32px 32px 0 0;
        }

        .header::before {
            content: '';
            position: absolute;
            inset: 0;
            background: linear-gradient(135deg, rgba(124,58,237,0.3), rgba(236,72,153,0.3));
            animation: neonShift 8s ease infinite;
        }

        @keyframes neonShift {
            0% { transform: translateX(-100%); }
            100% { transform: translateX(100%); }
        }

        .header h1 {
            font-size: 48px;
            font-weight: 900;
            margin-bottom: 8px;
            text-shadow: 
                0 0 20px rgba(255,255,255,0.8),
                0 0 40px rgba(124,58,237,0.8);
            letter-spacing: 3px;
            position: relative;
            z-index: 2;
            animation: neonGlow 2s ease-in-out infinite alternate;
            word-break: break-word;
        }

        @keyframes neonGlow {
            from { text-shadow: 0 0 20px rgba(255,255,255,0.8), 0 0 40px rgba(124,58,237,0.8); }
            to { text-shadow: 0 0 30px rgba(255,255,255,1), 0 0 60px rgba(236,72,153,0.9); }
        }

        .header p {
            font-size: 18px;
            opacity: 0.95;
            position: relative;
            z-index: 2;
            letter-spacing: 1px;
            text-shadow: 0 0 10px rgba(0,0,0,0.5);
            word-break: break-word;
        }

        .form-container {
            padding: 30px 30px;
            width: 100%;
        }

        h2 {
            text-align: center;
            margin-bottom: 35px;
            color: #e2e8f0;
            font-size: 26px;
            font-weight: 700;
            text-shadow: 0 0 15px rgba(124, 58, 237, 0.4);
        }

        .form-group {
            margin-bottom: 22px;
            width: 100%;
        }

        label {
            display: block;
            margin-bottom: 8px;
            color: #e2e8f0;
            font-weight: 600;
            font-size: 15px;
            text-shadow: 0 0 8px rgba(124, 58, 237, 0.3);
            word-break: break-word;
        }

        input {
            width: 100%;
            padding: 15px 18px;
            border: 3px solid #7c3aed;
            border-radius: 14px;
            font-size: 15px;
            background: rgba(30, 41, 59, 0.8);
            color: #e2e8f0;
            transition: all 0.4s ease;
            box-shadow: 
                0 0 20px rgba(124, 58, 237, 0.3),
                inset 0 0 15px rgba(0, 0, 0, 0.3);
        }

        input:focus {
            outline: none;
            border-color: #ec4899;
            background: rgba(51, 65, 85, 0.9);
            box-shadow: 
                0 0 40px rgba(236, 72, 153, 0.6),
                0 0 60px rgba(124, 58, 237, 0.4);
            transform: translateY(-2px);
        }

        input::placeholder {
            color: rgba(226, 232, 240, 0.5);
        }

        button {
            width: 100%;
            padding: 16px;
            background: linear-gradient(135deg, #7c3aed, #ec4899);
            color: white;
            border: none;
            border-radius: 14px;
            font-weight: 700;
            font-size: 16px;
            cursor: pointer;
            transition: all 0.5s ease;
            margin-bottom: 18px;
            box-shadow: 
                0 0 40px rgba(124, 58, 237, 0.6),
                0 10px 30px rgba(0, 0, 0, 0.4);
            letter-spacing: 1px;
            position: relative;
            overflow: hidden;
        }

        button::before {
            content: '';
            position: absolute;
            top: 0; left: -100%;
            width: 100%;
            height: 100%;
            background: linear-gradient(90deg, transparent, rgba(255,255,255,0.3), transparent);
            transition: 0.7s;
        }

        button:hover {
            transform: translateY(-4px);
            box-shadow: 
                0 0 80px rgba(236, 72, 153, 0.8),
                0 20px 50px rgba(124, 58, 237, 0.5);
        }

        button:hover::before {
            left: 100%;
        }

        button:active {
            transform: translateY(-1px);
        }

        .toggle-link {
            text-align: center;
            color: #94a3b8;
            font-size: 15px;
            margin-top: 8px;
            word-break: break-word;
        }

        .toggle-link a {
            color: #ec4899;
            cursor: pointer;
            text-decoration: none;
            font-weight: 700;
            text-shadow: 0 0 10px rgba(236, 72, 153, 0.4);
            transition: all 0.3s;
        }

        .toggle-link a:hover {
            color: #f472b6;
            text-shadow: 0 0 20px rgba(236, 72, 153, 0.7);
        }

        .error {
            color: #fca5a5;
            font-size: 14px;
            text-align: center;
            padding: 14px;
            background: rgba(239, 68, 68, 0.15);
            border-radius: 10px;
            border: 2px solid rgba(239, 68, 68, 0.4);
            box-shadow: 0 0 20px rgba(239, 68, 68, 0.3);
            backdrop-filter: blur(8px);
            margin-bottom: 15px;
            word-break: break-word;
        }

        .success {
            color: #86efac;
            font-size: 14px;
            text-align: center;
            padding: 14px;
            background: rgba(34, 197, 94, 0.15);
            border-radius: 10px;
            border: 2px solid rgba(34, 197, 94, 0.4);
            box-shadow: 0 0 20px rgba(34, 197, 94, 0.3);
            backdrop-filter: blur(8px);
            margin-bottom: 15px;
            word-break: break-word;
        }

        .hidden {
            display: none !important;
        }

        .form-section {
            display: none;
            opacity: 0;
            transition: opacity 0.4s ease;
        }

        .form-section.active {
            display: block;
            opacity: 1;
            animation: fadeIn 0.5s ease-in;
        }

        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(20px); }
            to { opacity: 1; transform: translateY(0); }
        }

        @media (max-width: 480px) {
            .header h1 { font-size: 32px; }
            .header p { font-size: 14px; }
            .form-container { padding: 25px 15px; }
            h2 { font-size: 20px; }
            input { padding: 12px 13px; font-size: 13px; }
            button { padding: 13px; font-size: 14px; }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎯 PROSPANDO</h1>
            <p>Personal-Anwesenheitssystem</p>
        </div>
        <div class="form-container">
            <!-- LOGIN FORMU -->
            <div id="login-section" class="form-section active">
                <h2>Anmelden</h2>
                <div id="login-error" class="error hidden"></div>
                <div id="login-success" class="success hidden"></div>
                <div class="form-group">
                    <label for="login-email">📧 E-Mail:</label>
                    <input type="email" id="login-email" placeholder="Ihre E-Mail-Adresse..." autocomplete="email">
                </div>
                <div class="form-group">
                    <label for="login-password">🔐 Passwort:</label>
                    <input type="password" id="login-password" placeholder="Ihr Passwort..." autocomplete="current-password">
                </div>
                <button type="button" onclick="handleLogin()">Anmelden</button>
                <div class="toggle-link">
                    Sie haben noch kein Konto? <a onclick="toggleForm()">Registrieren</a>
                </div>
            </div>

            <!-- SIGNUP FORMU -->
            <div id="signup-section" class="form-section">
                <h2>Registrieren</h2>
                <div id="signup-error" class="error hidden"></div>
                <div id="signup-success" class="success hidden"></div>
                <div class="form-group">
                    <label for="signup-name">👤 Vor- und Nachname:</label>
                    <input type="text" id="signup-name" placeholder="Ihr Vor- und Nachname..." autocomplete="name">
                </div>
                <div class="form-group">
                    <label for="signup-email">📧 E-Mail:</label>
                    <input type="email" id="signup-email" placeholder="Ihre E-Mail-Adresse..." autocomplete="email">
                </div>
                <div class="form-group">
                    <label for="signup-password">🔐 Passwort:</label>
                    <input type="password" id="signup-password" placeholder="Ihr Passwort..." autocomplete="new-password">
                </div>
                <div class="form-group">
                    <label for="signup-confirm">🔐 Passwort bestätigen:</label>
                    <input type="password" id="signup-confirm" placeholder="Passwort wiederholen..." autocomplete="new-password">
                </div>
                <button type="button" onclick="handleSignup()">Registrieren</button>
                <div class="toggle-link">
                    Sie haben bereits ein Konto? <a onclick="toggleForm()">Anmelden</a>
                </div>
            </div>
        </div>
    </div>

    <script>
        const BACKEND_URL = window.location.origin;

        function toggleForm() {
            const loginSection = document.getElementById('login-section');
            const signupSection = document.getElementById('signup-section');
            const loginError = document.getElementById('login-error');
            const signupError = document.getElementById('signup-error');
            
            loginSection.classList.toggle('active');
            signupSection.classList.toggle('active');
            loginError.classList.add('hidden');
            signupError.classList.add('hidden');
            
            if (loginSection.classList.contains('active')) {
                setTimeout(() => document.getElementById('login-email').focus(), 100);
            } else {
                setTimeout(() => document.getElementById('signup-name').focus(), 100);
            }
        }

        async function handleLogin() {
            const email = document.getElementById('login-email').value.trim();
            const password = document.getElementById('login-password').value;
            const errorDiv = document.getElementById('login-error');
            
            errorDiv.classList.add('hidden');
            
            if (!email || !password) {
                errorDiv.classList.remove('hidden');
                errorDiv.textContent = '❌ Bitte füllen Sie beide Felder aus!';
                return;
            }
            
            if (!email.includes('@')) {
                errorDiv.classList.remove('hidden');
                errorDiv.textContent = '❌ Bitte geben Sie eine gültige E-Mail ein!';
                return;
            }
            
            try {
                const response = await fetch(`${BACKEND_URL}/api/login`, {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({email, password})
                });
                
                const data = await response.json();
                
                if (data.success) {
                    localStorage.setItem('user_id', data.user_id);
                    localStorage.setItem('user_name', data.user_name);
                    localStorage.setItem('employee_id', data.employee_id);
                    window.location.href = `${BACKEND_URL}/dashboard`;
                } else {
                    errorDiv.classList.remove('hidden');
                    errorDiv.textContent = '❌ ' + (data.message || 'Anmeldung fehlgeschlagen!');
                }
            } catch (error) {
                errorDiv.classList.remove('hidden');
                errorDiv.textContent = '❌ Verbindungsfehler. Später versuchen!';
                console.error('Login Fehler:', error);
            }
        }

        async function handleSignup() {
            const name = document.getElementById('signup-name').value.trim();
            const email = document.getElementById('signup-email').value.trim();
            const password = document.getElementById('signup-password').value;
            const confirm = document.getElementById('signup-confirm').value;
            const errorDiv = document.getElementById('signup-error');
            
            errorDiv.classList.add('hidden');
            
            if (!name || !email || !password || !confirm) {
                errorDiv.classList.remove('hidden');
                errorDiv.textContent = '❌ Bitte füllen Sie alle Felder aus!';
                return;
            }
            
            if (!email.includes('@')) {
                errorDiv.classList.remove('hidden');
                errorDiv.textContent = '❌ Bitte geben Sie eine gültige E-Mail ein!';
                return;
            }
            
            if (password.length < 6) {
                errorDiv.classList.remove('hidden');
                errorDiv.textContent = '❌ Passwort muss mindestens 6 Zeichen sein!';
                return;
            }
            
            if (password !== confirm) {
                errorDiv.classList.remove('hidden');
                errorDiv.textContent = '❌ Passwörter stimmen nicht überein!';
                return;
            }
            
            try {
                const response = await fetch(`${BACKEND_URL}/api/signup`, {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({name, email, password})
                });
                
                const data = await response.json();
                
                if (data.success) {
                    localStorage.setItem('user_id', data.user_id);
                    localStorage.setItem('user_name', data.user_name);
                    localStorage.setItem('employee_id', data.employee_id);
                    window.location.href = `${BACKEND_URL}/dashboard`;
                } else {
                    errorDiv.classList.remove('hidden');
                    errorDiv.textContent = '❌ ' + (data.message || 'Registrierung fehlgeschlagen!');
                }
            } catch (error) {
                errorDiv.classList.remove('hidden');
                errorDiv.textContent = '❌ Verbindungsfehler. Später versuchen!';
                console.error('Signup Fehler:', error);
            }
        }

        document.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                const loginSection = document.getElementById('login-section');
                if (loginSection.classList.contains('active')) {
                    handleLogin();
                } else {
                    handleSignup();
                }
            }
        });

        window.addEventListener('load', () => {
            document.getElementById('login-email').focus();
        });
    </script>
</body>
</html>'''

# ==================== AUTH ROUTES ====================
@app.route('/api/signup', methods=['POST'])
def signup():
    try:
        data = request.json
        name = data.get('name', '').strip()
        email = data.get('email', '').strip()
        password = data.get('password', '')
        
        if not name or not email or not password:
            return jsonify({'success': False, 'message': 'Lütfen tüm alanları doldurunuz!'}), 400
        
        if len(password) < 6:
            return jsonify({'success': False, 'message': 'Şifre en az 6 karakter olmalı!'}), 400
        
        if '@' not in email:
            return jsonify({'success': False, 'message': 'Geçerli bir email girin!'}), 400
        
        conn = get_conn()
        cur = conn.cursor()
        
        cur.execute("SELECT id FROM users WHERE email = %s", (email,))
        if cur.fetchone():
            cur.close()
            conn.close()
            return jsonify({'success': False, 'message': 'Bu email zaten kayıtlı!'}), 400
        
        cur.execute("SELECT id FROM employees WHERE name = %s", (name,))
        existing_emp = cur.fetchone()
        
        if existing_emp:
            emp_id = existing_emp[0]
        else:
            cur.execute("INSERT INTO employees (name) VALUES (%s) RETURNING id", (name,))
            emp_id = cur.fetchone()[0]
        
        hashed_password = hash_password(password)
        cur.execute(
            "INSERT INTO users (email, password, name, employee_id) VALUES (%s, %s, %s, %s) RETURNING id",
            (email, hashed_password, name, emp_id)
        )
        user_id = cur.fetchone()[0]
        
        conn.commit()
        cur.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': 'Kayıt başarılı!',
            'user_id': user_id,
            'user_name': name,
            'employee_id': emp_id
        }), 201
        
    except Exception as e:
        print(f"❌ Signup hatası: {str(e)}")
        return jsonify({'success': False, 'message': f'Hata: {str(e)}'}), 500

@app.route('/api/login', methods=['POST'])
def login():
    try:
        data = request.json
        email = data.get('email', '').strip()
        password = data.get('password', '')
        
        if not email or not password:
            return jsonify({'success': False, 'message': 'Email ve şifre gerekli!'}), 400
        
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("SELECT id, name, password, employee_id FROM users WHERE email = %s", (email,))
        user = cur.fetchone()
        
        if not user:
            cur.close()
            conn.close()
            return jsonify({'success': False, 'message': 'Email veya şifre hatalı!'}), 401
        
        user_id, name, hashed_password, emp_id = user
        if hash_password(password) != hashed_password:
            cur.close()
            conn.close()
            return jsonify({'success': False, 'message': 'Email veya şifre hatalı!'}), 401
        
        if not emp_id:
            cur.execute("SELECT id FROM employees WHERE name = %s", (name,))
            emp_result = cur.fetchone()
            emp_id = emp_result[0] if emp_result else user_id
        
        cur.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': 'Giriş başarılı!',
            'user_id': user_id,
            'user_name': name,
            'employee_id': emp_id
        }), 200
    except Exception as e:
        print(f"❌ Login hatası: {str(e)}")
        return jsonify({'success': False, 'message': f'Hata: {str(e)}'}), 500

# ==================== DASHBOARD ====================
@app.route('/dashboard')
def dashboard():
    return '''<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🎯 PROSPANDO - Dashboard</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: #0f172a;
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            padding: 20px;
            padding-top: 100px;
            position: relative;
            overflow: hidden;
        }

        body::before {
            content: '';
            position: absolute;
            top: 0; left: 0; right: 0; bottom: 0;
            background: 
                radial-gradient(circle at 20% 80%, #7c3aed 0%, transparent 50%),
                radial-gradient(circle at 80% 20%, #ec4899 0%, transparent 50%),
                radial-gradient(circle at 50% 50%, #3b82f6 0%, transparent 40%);
            opacity: 0.4;
            z-index: -1;
            animation: pulse 15s ease infinite;
        }

        @keyframes pulse {
            0%, 100% { opacity: 0.4; }
            50% { opacity: 0.6; }
        }

        .navbar {
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            background: rgba(15, 23, 42, 0.95);
            backdrop-filter: blur(20px);
            color: white;
            padding: 20px 30px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            z-index: 1000;
            border-bottom: 2px solid rgba(124, 58, 237, 0.3);
        }
        
        .navbar h1 { 
            font-size: 28px; 
            font-weight: 900;
            text-shadow: 0 0 15px rgba(124, 58, 237, 0.6);
        }
        
        .navbar button {
            background: linear-gradient(135deg, #ef4444, #dc2626);
            color: white;
            border: none;
            padding: 12px 28px;
            border-radius: 10px;
            cursor: pointer;
            font-weight: 600;
            transition: all 0.3s;
            box-shadow: 0 0 20px rgba(239, 68, 68, 0.4);
        }
        
        .navbar button:hover { 
            transform: translateY(-3px);
            box-shadow: 0 0 40px rgba(239, 68, 68, 0.6);
        }

        .container {
            background: rgba(15, 23, 42, 0.85);
            backdrop-filter: blur(20px);
            border-radius: 32px;
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.5);
            max-width: 500px;
            width: 100%;
            padding: 40px 30px;
            border: 1px solid rgba(124, 58, 237, 0.3);
        }

        .welcome {
            background: rgba(124, 58, 237, 0.2);
            color: white;
            padding: 30px;
            border-radius: 20px;
            text-align: center;
            margin-bottom: 40px;
            font-size: 26px;
            font-weight: bold;
            border: 2px solid rgba(124, 58, 237, 0.4);
            box-shadow: 0 0 30px rgba(124, 58, 237, 0.3);
        }

        .title {
            color: white;
            text-align: center;
            font-size: 32px;
            font-weight: 900;
            margin-bottom: 40px;
            text-shadow: 0 0 20px rgba(124, 58, 237, 0.6);
            letter-spacing: 2px;
        }

        .form-group { margin-bottom: 30px; }
        
        label {
            color: white;
            font-size: 16px;
            font-weight: bold;
            display: block;
            margin-bottom: 10px;
            text-shadow: 0 0 10px rgba(124, 58, 237, 0.3);
        }

        select, input {
            width: 100%;
            padding: 16px;
            font-size: 16px;
            border: 3px solid #7c3aed;
            border-radius: 15px;
            background: rgba(30, 41, 59, 0.8);
            color: #e2e8f0;
            transition: all 0.3s;
        }

        select:focus, input:focus {
            outline: none;
            border-color: #ec4899;
            background: rgba(51, 65, 85, 0.9);
            box-shadow: 0 0 30px rgba(236, 72, 153, 0.5);
        }

        button.check-btn {
            width: 100%;
            padding: 28px;
            font-size: 28px;
            font-weight: bold;
            background: linear-gradient(135deg, #48bb78 0%, #38a169 100%);
            color: white;
            border: none;
            border-radius: 20px;
            cursor: pointer;
            margin-top: 20px;
            transition: all 0.5s ease;
            box-shadow: 0 0 40px rgba(72, 187, 120, 0.4);
            position: relative;
            overflow: hidden;
        }

        button.check-btn::before {
            content: '';
            position: absolute;
            top: 0; left: -100%;
            width: 100%;
            height: 100%;
            background: linear-gradient(90deg, transparent, rgba(255,255,255,0.3), transparent);
            transition: 0.7s;
        }

        button.check-btn:hover { 
            transform: translateY(-5px);
            box-shadow: 0 0 80px rgba(72, 187, 120, 0.6);
        }

        button.check-btn:hover::before {
            left: 100%;
        }

        .result {
            margin-top: 30px;
            padding: 30px;
            border-radius: 20px;
            text-align: center;
            font-size: 18px;
            font-weight: bold;
            color: white;
            display: none;
            border: 3px solid rgba(255, 255, 255, 0.3);
            white-space: pre-wrap;
            opacity: 0;
            transform: scale(0.9);
            transition: all 0.6s ease;
        }

        .result.show {
            opacity: 1;
            transform: scale(1);
            display: block;
        }

        .result.success { 
            background: linear-gradient(135deg, #48bb78 0%, #38a169 100%);
            border-color: #48bb78;
            box-shadow: 0 0 60px rgba(72, 187, 120, 0.7);
        }

        .result.error { 
            background: linear-gradient(135deg, #f56565 0%, #e53e3e 100%);
            border-color: #f56565;
            box-shadow: 0 0 60px rgba(245, 101, 101, 0.7);
        }

        .result.warning { 
            background: linear-gradient(135deg, #ed8936 0%, #dd6b20 100%);
            border-color: #ed8936;
            box-shadow: 0 0 60px rgba(237, 137, 54, 0.7);
        }

        @media (max-width: 480px) {
            .navbar { padding: 15px 20px; }
            .navbar h1 { font-size: 20px; }
            .container { padding: 25px 20px; }
            .welcome { font-size: 20px; padding: 20px; }
            .title { font-size: 24px; }
            button.check-btn { padding: 20px; font-size: 20px; }
        }
    </style>
</head>
<body>
    <div class="navbar">
        <div><h1>🎯 PROSPANDO</h1></div>
        <div><button onclick="logout()">Çıkış</button></div>
    </div>

    <div class="container">
        <div class="welcome">
            👋 Hoş geldiniz, <span id="user-name">Kullanıcı</span>!
        </div>
        
        <div class="title">Anwesenheitssystem</div>
        
        <div class="form-group">
            <label for="location">📍 Bereich wählen:</label>
            <select id="location">
                <option value="">Bereich auswählen...</option>
                <option value="Mitte">🏢 Mitte</option>
                <option value="Spandau">🏭 Spandau</option>
                <option value="Steglitz">🏪 Steglitz</option>
                <option value="Neukölln">🗽 Neukölln</option>
                <option value="Charlottenburg">🛖 Charlottenburg</option>
            </select>
        </div>

        <button class="check-btn" onclick="checkIn()">✅ EINGANG / AUSGANG</button>
        
        <div id="result" class="result"></div>
    </div>

    <script>
        const BACKEND_URL = window.location.origin;

        window.addEventListener('load', () => {
            const userName = localStorage.getItem('user_name');
            const userId = localStorage.getItem('user_id');
            const employeeId = localStorage.getItem('employee_id');
            
            if (!userId || !employeeId) {
                window.location.href = '/';
                return;
            }
            
            document.getElementById('user-name').textContent = userName || 'Kullanıcı';
            document.getElementById('location').focus();
        });

        async function checkIn() {
            const location = document.getElementById('location').value;
            const employeeId = localStorage.getItem('employee_id');
            
            if (!location) {
                showResult('❌ HATA!\nLütfen bir bereich seçin!', 'error');
                return;
            }
            
            try {
                const response = await fetch(`${BACKEND_URL}/api/checkin`, {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        employee_id: parseInt(employeeId),
                        location: location
                    })
                });
                
                const data = await response.json();
                showResult(data.message, data.type);
                
                if (data.success) {
                    document.getElementById('location').value = '';
                    document.getElementById('location').focus();
                }
            } catch (error) {
                showResult('❌ HATA!\nBağlantı hatası: ' + error.message, 'error');
                console.error('Fehler:', error);
            }
        }

        function showResult(message, type) {
            const resultDiv = document.getElementById('result');
            resultDiv.textContent = message;
            resultDiv.className = `result ${type} show`;
            setTimeout(() => { resultDiv.className = 'result'; }, 5000);
        }

        function logout() {
            localStorage.removeItem('user_id');
            localStorage.removeItem('user_name');
            localStorage.removeItem('employee_id');
            window.location.href = '/';
        }

        document.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                checkIn();
            }
        });
    </script>
</body>
</html>'''

# ==================== CHECK-IN ROUTE ====================
@app.route('/api/checkin', methods=['POST'])
def check_in():
    try:
        data = request.json
        emp_id_input = data.get('employee_id') or data.get('id')
        
        if not emp_id_input:
            return jsonify({
                'success': False,
                'message': '❌ HATA!\nPersonel ID gerekli!',
                'type': 'error'
            }), 400
        
        try:
            emp_id = int(emp_id_input)
        except (ValueError, TypeError):
            return jsonify({
                'success': False,
                'message': '❌ HATA!\nGeçersiz ID formatı!',
                'type': 'error'
            }), 400
        
        location = data.get('location', '').strip()
        
        if not location:
            return jsonify({
                'success': False,
                'message': '❌ HATA!\nBölge seçilmedi!',
                'type': 'error'
            }), 400
        
        conn = get_conn()
        cur = conn.cursor()
        
        cur.execute("SELECT id, name FROM employees WHERE id = %s", (emp_id,))
        employee = cur.fetchone()
        
        if not employee:
            cur.close()
            conn.close()
            return jsonify({
                'success': False,
                'message': f'❌ HATA!\nPersonel ID {emp_id} bulunamadı!',
                'type': 'error'
            }), 404
        
        emp_db_id, emp_name = employee
        today = datetime.now().strftime("%Y-%m-%d")
        now_time = datetime.now().strftime("%H:%M")
        
        cur.execute("""
            SELECT id, start_time FROM attendance
            WHERE employee_id = %s AND date = %s AND location = %s AND end_time IS NULL
        """, (emp_db_id, today, location))
        open_record = cur.fetchone()
        
        if open_record:
            # Çıkış
            att_id, start_time = open_record
            start_str = str(start_time)[:5] if len(str(start_time)) > 5 else str(start_time)
            duration = calculate_duration(start_str, now_time)
            
            cur.execute("""
                UPDATE attendance 
                SET end_time = %s, duration = %s 
                WHERE id = %s
            """, (now_time, duration, att_id))
            
            message = f'👋 BİS SPÄTER!\n{emp_name}\n🕐 Ausgang: {now_time}\n⏱️ Dauer: {duration}\n📍 {location}'
            response_type = 'success'
        else:
            cur.execute("""
                SELECT location FROM attendance
                WHERE employee_id = %s AND date = %s AND end_time IS NULL
            """, (emp_db_id, today))
            elsewhere = cur.fetchone()
            
            if elsewhere:
                cur.close()
                conn.close()
                return jsonify({
                    'success': False,
                    'message': f'⚠️ ACHTUNG!\n{emp_name}\nSie haben einen offenen Eintrag im Bereich {elsewhere[0]}!\nBitte melden Sie sich zuerst ab!',
                    'type': 'warning'
                }), 409
            
            # Giriş
            cur.execute("""
                INSERT INTO attendance 
                (employee_id, employee_name, date, start_time, location)
                VALUES (%s, %s, %s, %s, %s)
            """, (emp_db_id, emp_name, today, now_time, location))
            
            message = f'✅ WILLKOMMEN!\n{emp_name}\n🕐 Eingang: {now_time}\n📍 {location}'
            response_type = 'success'
        
        conn.commit()
        cur.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': message,
            'type': response_type
        }), 200
        
    except Exception as e:
        print(f"❌ Check-in hatası: {str(e)}")
        return jsonify({
            'success': False,
            'message': '❌ HATA!\nSunucu hatası. Lütfen tekrar deneyiniz!',
            'type': 'error'
        }), 500

# ==================== HEALTH & ERROR HANDLERS ====================
@app.route('/health', methods=['GET'])
def health():
    try:
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("SELECT 1")
        cur.close()
        conn.close()
        return jsonify({'status': 'healthy', 'database': 'connected'}), 200
    except Exception as e:
        return jsonify({'status': 'unhealthy', 'error': str(e)}), 500

@app.route('/favicon.ico')
def favicon():
    return '', 204

@app.errorhandler(404)
def not_found(e):
    return jsonify({'success': False, 'message': 'Sayfa bulunamadı'}), 404

@app.errorhandler(500)
def server_error(e):
    return jsonify({'success': False, 'message': 'Sunucu hatası'}), 500

# ==================== MAIN ====================
if __name__ == '__main__':
    print("🚀 Uygulama başlatılıyor...")
    if init_db():
        print("✅ Veritabanı hazır!")
    else:
        print("⚠️ Veritabanı bağlantı sorunu olabilir!")
    
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('FLASK_ENV', 'production') == 'development'
    app.run(host='0.0.0.0', port=port, debug=debug)
