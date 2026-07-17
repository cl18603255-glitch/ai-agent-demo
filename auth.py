"""
MailPilot Pro v3.0 - User System Module
用户系统：注册/登录/积分/充值/用量统计
"""
import sqlite3
import os
import hashlib
import secrets
from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify, g

DATABASE = os.path.join(os.path.dirname(__file__), 'mailpilot.db')


def get_db():
    """获取数据库连接"""
    if 'db' not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
        g.db.execute('PRAGMA journal_mode=WAL')
    return g.db


def close_db(e=None):
    """关闭数据库连接"""
    db = g.pop('db', None)
    if db is not None:
        db.close()


def init_db():
    """初始化数据库表"""
    db = get_db()
    db.executescript('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE,
            password_hash TEXT NOT NULL,
            phone TEXT,
            balance REAL DEFAULT 100.0,
            total_spent REAL DEFAULT 0.0,
            is_premium INTEGER DEFAULT 0,
            premium_expires DATETIME,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            last_login DATETIME
        );

        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            token TEXT UNIQUE NOT NULL,
            expires_at DATETIME NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            amount REAL NOT NULL,
            balance_added REAL NOT NULL,
            payment_method TEXT DEFAULT 'wechat',
            status TEXT DEFAULT 'pending',
            transaction_id TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            paid_at DATETIME,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS usage_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            endpoint TEXT NOT NULL,
            credits_used REAL DEFAULT 1.0,
            response_size INTEGER DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        );

        CREATE INDEX IF NOT EXISTS idx_sessions_token ON sessions(token);
        CREATE INDEX IF NOT EXISTS idx_orders_user ON orders(user_id);
        CREATE INDEX IF NOT EXISTS idx_usage_user ON usage_logs(user_id);
    ''')
    db.commit()


def hash_password(password, salt=None):
    """密码哈希加密"""
    if salt is None:
        salt = secrets.token_hex(16)
    hashed = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt.encode('utf-8'), 100000)
    return salt + hashed.hex()


def verify_password(password, password_hash):
    """验证密码"""
    salt = password_hash[:32]
    stored_hash = password_hash[32:]
    hashed = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt.encode('utf-8'), 100000)
    return stored_hash == hashed.hex()


def generate_token(user_id, expires_hours=24):
    """生成 JWT-like 会话令牌"""
    token = secrets.token_hex(32)
    expires_at = datetime.utcnow() + timedelta(hours=expires_hours)
    db = get_db()
    db.execute(
        'INSERT INTO sessions (user_id, token, expires_at) VALUES (?, ?, ?)',
        (user_id, token, expires_at.isoformat())
    )
    db.commit()
    return token


def require_auth(f):
    """认证装饰器 - 需要登录才能访问"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization', '')
        if auth_header.startswith('Bearer '):
            token = auth_header[7:]
        else:
            token = request.args.get('token', '')

        if not token:
            return jsonify({'error': '未登录，请先登录'}), 401

        db = get_db()
        session = db.execute(
            'SELECT s.*, u.id as user_id, u.username, u.email, u.balance, u.total_spent, u.is_premium FROM sessions s JOIN users u ON s.user_id = u.id WHERE s.token = ? AND s.expires_at > ?',
            (token, datetime.utcnow().isoformat())
        ).fetchone()

        if not session:
            return jsonify({'error': '登录已过期，请重新登录'}), 401

        g.current_user = dict(session)
        return f(*args, **kwargs)
    return decorated_function


def get_current_user():
    """获取当前登录用户"""
    return getattr(g, 'current_user', None)
