import sqlite3
from flask import Flask, request, jsonify
import uuid
import random
import datetime
from datetime import datetime as dt
import logging
from werkzeug.security import generate_password_hash, check_password_hash
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'fallback-secret-key')
DATABASE = 'pvtxc.db'

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def init_db():
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (user_id TEXT PRIMARY KEY, 
                  username TEXT UNIQUE, 
                  password TEXT,
                  balance REAL DEFAULT 0,
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  last_mine TIMESTAMP)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS transactions
                 (transaction_id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_id TEXT,
                  target_id TEXT,
                  type TEXT,
                  amount REAL,
                  timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS problems
                 (problem_id TEXT PRIMARY KEY,
                  user_id TEXT,
                  problem TEXT,
                  answer REAL,
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    
    conn.commit()
    conn.close()

init_db()

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def parse_datetime(datetime_str: str) -> dt:
    if not datetime_str:
        return dt.now()
    formats = [
        "%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M:%S.%f",
        "%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M:%S.%f"
    ]
    for fmt in formats:
        try:
            return dt.strptime(datetime_str, fmt)
        except ValueError:
            continue
    raise ValueError(f"Unparseable datetime: {datetime_str}")

@app.route('/register', methods=['POST'])
def register():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    
    if not username or len(username) > 20:
        return jsonify({"error": "Invalid username"}), 400
    if not password or len(password) < 6:
        return jsonify({"error": "Password must be at least 6 characters"}), 400
    
    hashed_pw = generate_password_hash(password)
    user_id = str(uuid.uuid4())
    
    conn = get_db()
    try:
        conn.execute('INSERT INTO users (user_id, username, password) VALUES (?, ?, ?)',
                    (user_id, username, hashed_pw))
        conn.commit()
        return jsonify({
            "message": "Registration successful",
            "user_id": user_id
        }), 201
    except sqlite3.IntegrityError:
        return jsonify({"error": "Username already exists"}), 409
    finally:
        conn.close()

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    
    conn = get_db()
    user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
    conn.close()
    
    if not user or not check_password_hash(user['password'], password):
        return jsonify({"error": "Invalid credentials"}), 401
    
    return jsonify({
        "user_id": user['user_id'],
        "username": user['username'],
        "balance": user['balance']
    }), 200

@app.route('/mine', methods=['POST'])
def mine():
    data = request.json
    user_id = data.get('user_id')
    password = data.get('password')
    problem_id = data.get('problem_id')
    answer = data.get('answer')
    
    conn = get_db()
    try:
        user = conn.execute('SELECT * FROM users WHERE user_id = ?', (user_id,)).fetchone()
        if not user or not check_password_hash(user['password'], password):
            return jsonify({"error": "Unauthorized"}), 401

        problem = conn.execute('SELECT * FROM problems WHERE problem_id = ? AND user_id = ?',
                             (problem_id, user_id)).fetchone()
        if not problem:
            return jsonify({"error": "Invalid problem"}), 404

        current_time = dt.now()
        try:
            created_at = parse_datetime(problem['created_at'])
            solve_time = (current_time - created_at).total_seconds()
            reward = max(0.1, 2.0 - (1.9 * (solve_time / 120)))
            reward = round(min(reward, 2.0), 4)
        except:
            reward = 0.1

        conn.execute('UPDATE users SET balance = balance + ?, last_mine = ? WHERE user_id = ?',
                   (reward, current_time.isoformat(), user_id))
        conn.execute('INSERT INTO transactions (user_id, type, amount) VALUES (?, "mine", ?)',
                   (user_id, reward))
        conn.execute('DELETE FROM problems WHERE problem_id = ?', (problem_id,))
        conn.commit()

        new_balance = conn.execute('SELECT balance FROM users WHERE user_id = ?', 
                                 (user_id,)).fetchone()['balance']
        return jsonify({
            "reward": reward,
            "balance": round(new_balance, 4)
        }), 200
    except Exception as e:
        conn.rollback()
        logger.error(f"Mining error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500
    finally:
        conn.close()

@app.route('/transfer', methods=['POST'])
def transfer():
    data = request.json
    user_id = data.get('user_id')
    password = data.get('password')
    receiver = data.get('receiver')
    amount = data.get('amount')
    
    try:
        amount = float(amount)
        if amount <= 0:
            raise ValueError
    except:
        return jsonify({"error": "Invalid amount"}), 400
    
    conn = get_db()
    try:
        sender = conn.execute('SELECT * FROM users WHERE user_id = ?', (user_id,)).fetchone()
        if not sender or not check_password_hash(sender['password'], password):
            return jsonify({"error": "Unauthorized"}), 401
            
        if sender['balance'] < amount:
            return jsonify({"error": "Insufficient funds"}), 400
            
        receiver = conn.execute('SELECT * FROM users WHERE username = ?', (receiver,)).fetchone()
        if not receiver:
            return jsonify({"error": "Receiver not found"}), 404
            
        if sender['user_id'] == receiver['user_id']:
            return jsonify({"error": "Cannot send to yourself"}), 400
            
        conn.execute('UPDATE users SET balance = balance - ? WHERE user_id = ?',
                   (amount, user_id))
        conn.execute('UPDATE users SET balance = balance + ? WHERE user_id = ?',
                   (amount, receiver['user_id']))
                   
        conn.execute('''INSERT INTO transactions 
                     (user_id, target_id, type, amount)
                     VALUES (?, ?, 'transfer', ?)''',
                  (user_id, receiver['user_id'], -amount))
        conn.execute('''INSERT INTO transactions 
                     (user_id, target_id, type, amount)
                     VALUES (?, ?, 'transfer', ?)''',
                  (receiver['user_id'], user_id, amount))
        
        conn.commit()
        return jsonify({"message": "Transfer successful"}), 200
    except Exception as e:
        conn.rollback()
        logger.error(f"Transfer error: {str(e)}")
        return jsonify({"error": "Transfer failed"}), 500
    finally:
        conn.close()

@app.route('/transactions', methods=['POST'])
def transactions():
    data = request.json
    user_id = data.get('user_id')
    password = data.get('password')
    
    conn = get_db()
    user = conn.execute('SELECT * FROM users WHERE user_id = ?', (user_id,)).fetchone()
    if not user or not check_password_hash(user['password'], password):
        return jsonify({"error": "Unauthorized"}), 401
    
    txns = conn.execute('''SELECT * FROM transactions 
                        WHERE user_id = ? 
                        ORDER BY timestamp DESC LIMIT 50''',
                     (user_id,)).fetchall()
    return jsonify([dict(txn) for txn in txns]), 200

@app.route('/problem', methods=['POST'])
def problem():
    data = request.json
    user_id = data.get('user_id')
    password = data.get('password')
    
    conn = get_db()
    user = conn.execute('SELECT * FROM users WHERE user_id = ?', (user_id,)).fetchone()
    if not user or not check_password_hash(user['password'], password):
        return jsonify({"error": "Unauthorized"}), 401
    
    a, b = random.randint(100, 999), random.randint(10, 99)
    op = random.choice(['+', '-', '*'])
    problem_str = f"{a}{op}{b}"
    answer = eval(problem_str)
    problem_id = str(uuid.uuid4())
    
    conn.execute('INSERT INTO problems (problem_id, user_id, problem, answer) VALUES (?, ?, ?, ?)',
               (problem_id, user_id, problem_str, answer))
    conn.commit()
    return jsonify({"problem_id": problem_id, "problem": problem_str}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5057, threaded=True)
