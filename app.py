import os
      # HEMEN ALTINDA – psycopg import edilmeden önce!

from flask import Flask, request, jsonify
from flask_cors import CORS
import psycopg                 # bu satırdan SONRA gelmeli
from datetime import datetime, timedelta
import hashlib

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'change-this-in-production')
CORS(app)


# ==================== DATABASE CONFIG ====================
def get_conn():
    """Veritabanı bağlantısı oluştur"""
    try:
        # Render'da tanımladığımız DATABASE_URL ortam değişkenini al
        conn_string = os.getenv('DATABASE_URL')
        
        if not conn_string:
            raise Exception("DATABASE_URL ortam değişkeni tanımlı değil! Render Environment'ta eklediğinden emin ol.")
        
        conn = psycopg.connect(
            conn_string,                # Tüm bilgiler (host, user, password, dbname, port) burada
            sslmode="require",
            connect_timeout=20,
            keepalives=1,
            keepalives_idle=30
        )
        return conn
    except Exception as e:
        print(f"❌ Database connection error: {str(e)}")
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
                employee_id INTEGER UNIQUE,
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
        print("✅ Tablolar başarıyla oluşturuldu/kontrol edildi")
        return True
    except Exception as e:
        print(f"❌ Tablo oluşturma hatası: {str(e)}")
        return False

# ==================== AUTH ROUTES ====================

@app.route('/')
def index():
    return """<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🎯 PROSPANDO - Giriş</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 20px;
        }
        .container {
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
            max-width: 400px;
            width: 100%;
            overflow: hidden;
        }
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 40px 20px;
            text-align: center;
            color: white;
        }
        .header h1 { font-size: 48px; margin-bottom: 10px; }
        .header p { font-size: 16px; opacity: 0.9; }
        .form-container { padding: 40px; }
        .form-group { margin-bottom: 20px; }
        label {
            display: block;
            margin-bottom: 8px;
            color: #2d3748;
            font-weight: 600;
            font-size: 14px;
        }
        input {
            width: 100%;
            padding: 12px 15px;
            border: 2px solid #e2e8f0;
            border-radius: 8px;
            font-size: 14px;
            transition: all 0.3s;
        }
        input:focus {
            outline: none;
            border-color: #667eea;
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
        }
        button {
            width: 100%;
            padding: 12px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 8px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s;
            margin-bottom: 10px;
        }
        button:hover { transform: translateY(-2px); box-shadow: 0 5px 20px rgba(102, 126, 234, 0.4); }
        .toggle-link { text-align: center; color: #666; font-size: 14px; }
        .toggle-link a { color: #667eea; cursor: pointer; text-decoration: none; font-weight: 600; }
        .form-section { display: none; }
        .form-section.active { display: block; }
        .error {
            color: #f56565;
            font-size: 13px;
            margin-top: 10px;
            padding: 10px;
            background: #fff5f5;
            border-radius: 6px;
            border-left: 3px solid #f56565;
        }
        .hidden { display: none; }
        h2 { text-align: center; margin-bottom: 30px; color: #2d3748; font-size: 20px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎯 PROSPANDO</h1>
            <p>Personel Yoklama Sistemi</p>
        </div>
        <div class="form-container">
            <div id="login-section" class="form-section active">
                <h2>Giriş Yap</h2>
                <div class="form-group">
                    <label for="login-email">📧 Email:</label>
                    <input type="email" id="login-email" placeholder="Email adresiniz...">
                </div>
                <div class="form-group">
                    <label for="login-password">🔐 Şifre:</label>
                    <input type="password" id="login-password" placeholder="Şifreniz...">
                </div>
                <button onclick="handleLogin()">Giriş Yap</button>
                <div id="login-error" class="error hidden"></div>
                <div class="toggle-link">
                    Hesabınız yok mu? <a onclick="toggleForm()">Kayıt Ol</a>
                </div>
            </div>
            <div id="signup-section" class="form-section">
                <h2>Kayıt Ol</h2>
                <div class="form-group">
                    <label for="signup-name">👤 Ad Soyad:</label>
                    <input type="text" id="signup-name" placeholder="Ad Soyadınız...">
                </div>
                <div class="form-group">
                    <label for="signup-email">📧 Email:</label>
                    <input type="email" id="signup-email" placeholder="Email adresiniz...">
                </div>
                <div class="form-group">
                    <label for="signup-password">🔐 Şifre:</label>
                    <input type="password" id="signup-password" placeholder="Şifreniz...">
                </div>
                <div class="form-group">
                    <label for="signup-confirm">🔐 Şifreyi Onayla:</label>
                    <input type="password" id="signup-confirm" placeholder="Şifreyi tekrar giriniz...">
                </div>
                <div class="form-group">
                    <label for="signup-id">🆔 Kimlik No:</label>
                    <input type="number" id="signup-id" placeholder="Personel kimlik numaranız...">
                </div>
                <button onclick="handleSignup()">Kayıt Ol</button>
                <div id="signup-error" class="error hidden"></div>
                <div class="toggle-link">
                    Zaten hesabınız var mı? <a onclick="toggleForm()">Giriş Yap</a>
                </div>
            </div>
        </div>
    </div>
    <script>
        function toggleForm() {
            document.getElementById('login-section').classList.toggle('active');
            document.getElementById('signup-section').classList.toggle('active');
            document.getElementById('login-error').classList.add('hidden');
            document.getElementById('signup-error').classList.add('hidden');
        }
        async function handleLogin() {
            const email = document.getElementById('login-email').value.trim();
            const password = document.getElementById('login-password').value;
            const errorDiv = document.getElementById('login-error');
            if (!email || !password) {
                errorDiv.classList.remove('hidden');
                errorDiv.textContent = '❌ Lütfen tüm alanları doldurunuz!';
                return;
            }
            try {
                const response = await fetch('/api/login', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({email, password})
                });
                const data = await response.json();
                if (data.success) {
                    localStorage.setItem('user_id', data.user_id);
                    localStorage.setItem('user_name', data.user_name);
                    localStorage.setItem('employee_id', data.employee_id);
                    window.location.href = '/dashboard';
                } else {
                    errorDiv.classList.remove('hidden');
                    errorDiv.textContent = '❌ ' + data.message;
                }
            } catch (error) {
                errorDiv.classList.remove('hidden');
                errorDiv.textContent = '❌ Bağlantı hatası!';
            }
        }
        async function handleSignup() {
            const name = document.getElementById('signup-name').value.trim();
            const email = document.getElementById('signup-email').value.trim();
            const password = document.getElementById('signup-password').value;
            const confirm = document.getElementById('signup-confirm').value;
            const employee_id = document.getElementById('signup-id').value.trim();
            const errorDiv = document.getElementById('signup-error');
            if (!name || !email || !password || !confirm || !employee_id) {
                errorDiv.classList.remove('hidden');
                errorDiv.textContent = '❌ Lütfen tüm alanları doldurunuz!';
                return;
            }
            if (password !== confirm) {
                errorDiv.classList.remove('hidden');
                errorDiv.textContent = '❌ Şifreler eşleşmiyor!';
                return;
            }
            if (password.length < 6) {
                errorDiv.classList.remove('hidden');
                errorDiv.textContent = '❌ Şifre en az 6 karakter olmalıdır!';
                return;
            }
            try {
                const response = await fetch('/api/signup', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({name, email, password, employee_id: parseInt(employee_id)})
                });
                const data = await response.json();
                if (data.success) {
                    localStorage.setItem('user_id', data.user_id);
                    localStorage.setItem('user_name', data.user_name);
                    localStorage.setItem('employee_id', data.employee_id);
                    window.location.href = '/dashboard';
                } else {
                    errorDiv.classList.remove('hidden');
                    errorDiv.textContent = '❌ ' + data.message;
                }
            } catch (error) {
                errorDiv.classList.remove('hidden');
                errorDiv.textContent = '❌ Bağlantı hatası!';
            }
        }
        document.getElementById('login-password').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') handleLogin();
        });
        document.getElementById('signup-confirm').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') handleSignup();
        });
    </script>
</body>
</html>"""

@app.route('/api/signup', methods=['POST'])
def signup():
    try:
        data = request.json
        name = data.get('name', '').strip()
        email = data.get('email', '').strip()
        password = data.get('password', '')
        # employee_id'yi kaldırdık, artık kullanmıyoruz
        
        if not name or not email or not password:
            return jsonify({'success': False, 'message': 'Lütfen tüm alanları doldurunuz!'}), 400
        
        conn = get_conn()
        cur = conn.cursor()
        
        # Email kontrol
        cur.execute("SELECT id FROM users WHERE email = %s", (email,))
        if cur.fetchone():
            cur.close()
            conn.close()
            return jsonify({'success': False, 'message': 'Bu email zaten kayıtlı!'}), 400
        
        # Doğrudan users tablosuna ekle (employee_id yok)
        hashed_password = hash_password(password)
        cur.execute(
            "INSERT INTO users (email, password, name) VALUES (%s, %s, %s) RETURNING id",
            (email, hashed_password, name)
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
            'employee_id': user_id  # geçici olarak user_id'yi gönderiyoruz, frontend uyumlu olsun
        })
    except Exception as e:
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
        cur.execute("SELECT id, name, password FROM users WHERE email = %s", (email,))
        user = cur.fetchone()
        if not user:
            cur.close()
            conn.close()
            return jsonify({'success': False, 'message': 'Email veya şifre yanlış!'}), 401
        
        user_id, name, hashed_password = user
        if hash_password(password) != hashed_password:
            cur.close()
            conn.close()
            return jsonify({'success': False, 'message': 'Email veya şifre yanlış!'}), 401
        
        cur.close()
        conn.close()
        return jsonify({
            'success': True,
            'message': 'Giriş başarılı!',
            'user_id': user_id,
            'user_name': name,
            'employee_id': user_id  # frontend'in beklediği alan, user_id ile doldur
        })
    except Exception as e:
        print(f"❌ Login error: {str(e)}")
        return jsonify({'success': False, 'message': f'Hata: {str(e)}'}), 500

# ==================== DASHBOARD PAGE ====================

@app.route('/dashboard')
def dashboard():
    return """<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🎯 PROSPANDO YOKLAMA</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            padding: 20px;
            padding-top: 100px;
        }
        .navbar {
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            background: rgba(0, 0, 0, 0.3);
            color: white;
            padding: 15px 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            z-index: 1000;
        }
        .navbar h1 { font-size: 24px; }
        .navbar button {
            background: #f56565;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 8px;
            cursor: pointer;
            font-weight: 600;
        }
        .navbar button:hover { background: #e53e3e; }
        .container {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border-radius: 25px;
            padding: 60px 80px;
            max-width: 900px;
            width: 100%;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
        }
        .welcome {
            background: rgba(255, 255, 255, 0.2);
            color: white;
            padding: 20px;
            border-radius: 15px;
            text-align: center;
            margin-bottom: 40px;
            font-size: 32px;
            font-weight: bold;
        }
        .title {
            color: white;
            text-align: center;
            font-size: 28px;
            font-weight: bold;
            margin-bottom: 40px;
        }
        .form-group { margin-bottom: 30px; }
        label {
            color: white;
            font-size: 24px;
            font-weight: bold;
            display: flex;
            align-items: center;
            margin-bottom: 15px;
            background: rgba(255, 255, 255, 0.25);
            padding: 18px 25px;
            border-radius: 15px;
            border: 3px solid rgba(255, 255, 255, 0.4);
            width: fit-content;
            min-width: 200px;
        }
        select, input {
            width: 100%;
            padding: 20px;
            font-size: 20px;
            border: 3px solid #4299e1;
            border-radius: 15px;
            background: white;
            color: #2d3748;
        }
        select:focus, input:focus {
            outline: none;
            border-color: #3182ce;
            background: #ebf8ff;
        }
        .input-row {
            display: flex;
            gap: 25px;
            align-items: flex-start;
        }
        .input-row label { margin-bottom: 0; flex-shrink: 0; }
        .input-row input, .input-row select { flex: 1; }
        button.check-btn {
            width: 100%;
            padding: 35px;
            font-size: 36px;
            font-weight: bold;
            background: linear-gradient(135deg, #48bb78 0%, #38a169 100%);
            color: white;
            border: none;
            border-radius: 20px;
            cursor: pointer;
            margin-top: 20px;
        }
        button.check-btn:hover { background: linear-gradient(135deg, #38a169 0%, #2f855a 100%); }
        .result {
            margin-top: 30px;
            padding: 35px;
            border-radius: 20px;
            text-align: center;
            font-size: 26px;
            font-weight: bold;
            color: white;
            min-height: 130px;
            display: none;
            align-items: center;
            justify-content: center;
            border: 4px solid rgba(255, 255, 255, 0.3);
            white-space: pre-wrap;
        }
        .result.success { background: linear-gradient(135deg, #48bb78 0%, #38a169 100%); display: flex; }
        .result.error { background: linear-gradient(135deg, #f56565 0%, #e53e3e 100%); display: flex; }
        .result.warning { background: linear-gradient(135deg, #ed8936 0%, #dd6b20 100%); display: flex; }
        @media (max-width: 768px) {
            .container { padding: 30px 20px; }
            .welcome { font-size: 24px; }
            button.check-btn { padding: 20px; font-size: 24px; }
            .input-row { flex-direction: column; }
            label { font-size: 18px; width: 100%; }
            select, input { font-size: 16px; padding: 15px; }
        }
    </style>
</head>
<body>
    <div class="navbar">
        <div><h1>🎯 PROSPANDO</h1></div>
        <div><button onclick="logout()">Çıkış Yap</button></div>
    </div>
    <div class="container">
        <div class="welcome">
            👋 Hoş geldiniz, <span id="user-name"></span>!
        </div>
        <div class="title">PERSONEL YOKLAMA SİSTEMİ</div>
        <div class="form-group input-row">
            <label for="location">📍 BÖLGE:</label>
            <select id="location">
                <option value="">Bölge seçiniz...</option>
                <option value="Mitte">🏢 Mitte</option>
                <option value="Spandau">🏭 Spandau</option>
                <option value="Steglitz">🏪 Steglitz</option>
                <option value="Neukölln">🗽️ Neukölln</option>
                <option value="Charlottenburg">🛖️ Charlottenburg</option>
            </select>
        </div>
        <button class="check-btn" onclick="checkIn()">▶ GİRİŞ / ÇIKIŞ</button>
        <div id="result" class="result"></div>
    </div>
    <script>
        window.addEventListener('load', () => {
            const userName = localStorage.getItem('user_name');
            const userId = localStorage.getItem('user_id');
            const employeeId = localStorage.getItem('employee_id');
            if (!userName || !userId || !employeeId) {
                window.location.href = '/';
                return;
            }
            document.getElementById('user-name').textContent = userName;
            document.getElementById('location').focus();
        });
        async function checkIn() {
            const location = document.getElementById('location').value;
            const employeeId = localStorage.getItem('employee_id');
            if (!location) {
                showResult('❌ HATA!\\nLütfen bölge seçiniz.', 'error');
                return;
            }
            try {
                const response = await fetch('/api/checkin', {
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
                showResult('❌ HATA!\\nBağlantı hatası: ' + error.message, 'error');
            }
        }
        function showResult(message, type) {
            const resultDiv = document.getElementById('result');
            resultDiv.textContent = message;
            resultDiv.className = `result ${type}`;
            setTimeout(() => { resultDiv.className = 'result'; }, 6000);
        }
        function logout() {
            localStorage.removeItem('user_id');
            localStorage.removeItem('user_name');
            localStorage.removeItem('employee_id');
            window.location.href = '/';
        }
    </script>
</body>
</html>"""

@app.route('/api/checkin', methods=['POST'])
def check_in():
    try:
        data = request.json
        emp_id = int(data.get('id'))          # Frontend'den gelen ID (1001, 1002 vs.)
        location = data.get('location', '')
        
        if not location:
            return jsonify({
                'success': False,
                'message': '❌ HATA!\nLütfen bölge seçiniz.',
                'type': 'error'
            })
        
        conn = get_conn()
        cur = conn.cursor()
        
        # employees tablosundan isim al (id ile)
        cur.execute("SELECT name FROM employees WHERE id = %s", (emp_id,))
        employee = cur.fetchone()
        
        if not employee:
            cur.close()
            conn.close()
            return jsonify({
                'success': False,
                'message': f'❌ HATA!\nID {emp_id} numaralı personel bulunamadı!',
                'type': 'error'
            })
        
        emp_name = employee[0]
        today = datetime.now().strftime("%Y-%m-%d")
        now_time = datetime.now().strftime("%H:%M")
        
        # Bugün aynı bölgede açık giriş var mı?
        cur.execute("""
            SELECT id, start_time FROM attendance
            WHERE employee_id = %s AND date = %s AND location = %s AND end_time IS NULL
        """, (emp_id, today, location))
        open_record = cur.fetchone()
        
        if open_record:
            # ÇIKIŞ YAP
            att_id, start_time = open_record
            start_str = str(start_time)[:5] if len(str(start_time)) > 5 else str(start_time)
            duration = calculate_duration(start_str, now_time)
            
            cur.execute("""
                UPDATE attendance 
                SET end_time = %s, duration = %s 
                WHERE id = %s
            """, (now_time, duration, att_id))
            
            message = f'👋 GÖRÜŞÜRÜZ!\n{emp_name}\n🕐 Çıkış: {now_time}\n⏱️ Çalışma Süresi: {duration}\n📍 {location}'
            type_ = 'success'
        else:
            # GİRİŞ YAP
            # Başka bölgede açık kayıt varsa uyarı ver
            cur.execute("""
                SELECT location FROM attendance
                WHERE employee_id = %s AND date = %s AND end_time IS NULL
            """, (emp_id, today))
            elsewhere = cur.fetchone()
            
            if elsewhere:
                cur.close()
                conn.close()
                return jsonify({
                    'success': False,
                    'message': f'⚠️ DİKKAT!\n{emp_name}\n{elsewhere[0]} bölgesinde açık girişiniz var!\nÖnce oradan çıkış yapınız.',
                    'type': 'warning'
                })
            
            cur.execute("""
                INSERT INTO attendance 
                (employee_id, employee_name, date, start_time, location)
                VALUES (%s, %s, %s, %s, %s)
            """, (emp_id, emp_name, today, now_time, location))
            
            message = f'✅ HOŞ GELDİN!\n{emp_name}\n🕐 Giriş: {now_time}\n📍 {location}'
            type_ = 'success'
        
        conn.commit()
        cur.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': message,
            'type': type_
        })
        
    except ValueError:
        return jsonify({
            'success': False,
            'message': '❌ HATA!\nGeçersiz ID formatı.',
            'type': 'error'
        })
  except Exception as e:
    print(f"❌ Check-in error: {str(e)} | Data: {data}")  # Detaylı log için
    return jsonify({
        'success': False,
        'message': f'❌ Hata!\n{str(e)}',  # Test için detay göster, sonra kaldır
        'type': 'error'
    })

# ==================== HEALTH CHECK ====================

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
        return jsonify({'status': 'unhealthy', 'database': 'disconnected', 'error': str(e)}), 500

# ==================== ERROR HANDLERS ====================

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
        print("✅ Veritabanı hazır")
    else:
        print("⚠️  Veritabanı bağlantısında sorun olabilir")
    
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('FLASK_ENV', 'production') == 'development'
    app.run(host='0.0.0.0', port=port, debug=debug)










