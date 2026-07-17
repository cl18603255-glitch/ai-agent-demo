"""
MailPilot Pro v3.0 - User API Routes
用户相关API：注册/登录/充值/订单/用量
"""
import os
import time
import hashlib
from datetime import datetime
from flask import Blueprint, request, jsonify, current_app
from auth import get_db, init_db, close_db, hash_password, verify_password, generate_token, require_auth, get_current_user

user_bp = Blueprint('user', __name__, url_prefix='/api/user')


# ==================== 注册 ====================
@user_bp.route('/register', methods=['POST'])
def register():
    """用户注册"""
    data = request.get_json(silent=True)
    if not data:
        return jsonify({'error': '无效请求'}), 400

    username = (data.get('username') or '').strip()
    email = (data.get('email') or '').strip()
    password = data.get('password', '')
    phone = (data.get('phone') or '').strip()

    # 验证
    if not username or not password:
        return jsonify({'error': '用户名和密码不能为空'}), 400
    if len(username) < 2 or len(username) > 30:
        return jsonify({'error': '用户名2-30个字符'}), 400
    if len(password) < 6:
        return jsonify({'error': '密码至少6位'}), 400
    if email and '@' not in email:
        return jsonify({'error': '邮箱格式不正确'}), 400

    db = get_db()
    # 检查用户名是否已存在
    existing = db.execute('SELECT id FROM users WHERE username = ? OR email = ?', (username, email)).fetchone()
    if existing:
        return jsonify({'error': '用户名或邮箱已被注册'}), 409

    password_hash = hash_password(password)
    cursor = db.execute(
        'INSERT INTO users (username, email, password_hash, phone, balance) VALUES (?, ?, ?, ?, 100.0)',
        (username, email or None, password_hash, phone or None)
    )
    db.commit()
    user_id = cursor.lastrowid

    # 生成登录令牌
    token = generate_token(user_id)

    return jsonify({
        'message': '注册成功！赠送100元体验金',
        'user': {
            'id': user_id,
            'username': username,
            'email': email,
            'balance': 100.0,
            'token': token
        }
    }), 201


# ==================== 登录 ====================
@user_bp.route('/login', methods=['POST'])
def login():
    """用户登录"""
    data = request.get_json(silent=True)
    if not data:
        return jsonify({'error': '无效请求'}), 400

    username = (data.get('username') or '').strip()
    password = data.get('password', '')

    if not username or not password:
        return jsonify({'error': '请输入用户名和密码'}), 400

    db = get_db()
    user = db.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
    if not user or not verify_password(password, user['password_hash']):
        return jsonify({'error': '用户名或密码错误'}), 401

    # 更新最后登录时间
    db.execute('UPDATE users SET last_login = ? WHERE id = ?', (datetime.utcnow().isoformat(), user['id']))
    db.commit()

    # 生成新令牌
    token = generate_token(user['id'])

    return jsonify({
        'message': '登录成功',
        'user': {
            'id': user['id'],
            'username': user['username'],
            'email': user['email'],
            'phone': user['phone'],
            'balance': float(user['balance']),
            'total_spent': float(user['total_spent']),
            'is_premium': bool(user['is_premium']),
            'premium_expires': user['premium_expires'],
            'token': token
        }
    })


# ==================== 用户信息 ====================
@user_bp.route('/profile', methods=['GET'])
@require_auth
def profile():
    """获取当前用户信息"""
    user = get_current_user()
    return jsonify({
        'id': user['user_id'],
        'username': user['username'],
        'email': user['email'],
        'phone': user.get('phone'),
        'balance': float(user['balance']),
        'total_spent': float(user['total_spent']),
        'is_premium': bool(user['is_premium']),
        'premium_expires': user.get('premium_expires'),
        'created_at': user.get('created_at'),
        'last_login': user.get('last_login')
    })


@user_bp.route('/profile', methods=['PUT'])
@require_auth
def update_profile():
    """更新用户资料"""
    user = get_current_user()
    data = request.get_json(silent=True) or {}

    email = data.get('email', '').strip()
    phone = data.get('phone', '').strip()

    db = get_db()
    if email:
        existing = db.execute('SELECT id FROM users WHERE email = ? AND id != ?', (email, user['user_id'])).fetchone()
        if existing:
            return jsonify({'error': '邮箱已被使用'}), 409
        db.execute('UPDATE users SET email = ?, updated_at = ? WHERE id = ?', (email, datetime.utcnow().isoformat(), user['user_id']))

    if phone:
        db.execute('UPDATE users SET phone = ?, updated_at = ? WHERE id = ?', (phone, datetime.utcnow().isoformat(), user['user_id']))

    db.commit()
    return jsonify({'message': '资料已更新'})


# ==================== 修改密码 ====================
@user_bp.route('/change-password', methods=['POST'])
@require_auth
def change_password():
    """修改密码"""
    user = get_current_user()
    data = request.get_json(silent=True) or {}
    old_password = data.get('old_password', '')
    new_password = data.get('new_password', '')

    if not old_password or not new_password:
        return jsonify({'error': '请输入旧密码和新密码'}), 400
    if len(new_password) < 6:
        return jsonify({'error': '新密码至少6位'}), 400

    db = get_db()
    db_user = db.execute('SELECT password_hash FROM users WHERE id = ?', (user['user_id'],)).fetchone()
    if not verify_password(old_password, db_user['password_hash']):
        return jsonify({'error': '旧密码不正确'}), 400

    new_hash = hash_password(new_password)
    db.execute('UPDATE users SET password_hash = ?, updated_at = ? WHERE id = ?',
               (new_hash, datetime.utcnow().isoformat(), user['user_id']))
    db.commit()
    return jsonify({'message': '密码已修改'})


# ==================== 充值套餐 ====================
@user_bp.route('/plans', methods=['GET'])
def plans():
    """获取充值套餐列表"""
    return jsonify({
        'plans': [
            {'id': 'basic', 'name': '体验包', 'amount': 50, 'balance': 55, 'desc': '充50送5元', 'popular': False},
            {'id': 'standard', 'name': '标准包', 'amount': 100, 'balance': 115, 'desc': '充100送15元', 'popular': True},
            {'id': 'pro', 'name': '专业包', 'amount': 300, 'balance': 360, 'desc': '充300送60元', 'popular': False},
            {'id': 'enterprise', 'name': '企业包', 'amount': 1000, 'balance': 1300, 'desc': '充1000送300元', 'popular': False},
        ]
    })


# ==================== 创建订单 ====================
@user_bp.route('/order/create', methods=['POST'])
@require_auth
def create_order():
    """创建充值订单"""
    user = get_current_user()
    data = request.get_json(silent=True) or {}
    plan_id = data.get('plan_id', '')
    payment_method = data.get('payment_method', 'wechat')

    if not plan_id:
        return jsonify({'error': '请选择充值套餐'}), 400

    db = get_db()
    plan_row = db.execute('SELECT * FROM plans WHERE id = ?', (plan_id,)).fetchone()
    if not plan_row:
        # 兼容旧版：手动映射
        plan_map = {
            'basic': {'amount': 50, 'balance': 55},
            'standard': {'amount': 100, 'balance': 115},
            'pro': {'amount': 300, 'balance': 360},
            'enterprise': {'amount': 1000, 'balance': 1300},
        }
        pm = plan_map.get(plan_id)
        if not pm:
            return jsonify({'error': '无效的套餐ID'}), 400
        amount = pm['amount']
        balance = pm['balance']
    else:
        amount = float(plan_row['amount'])
        balance = float(plan_row['balance'])

    # 生成订单号
    order_no = 'MP' + datetime.utcnow().strftime('%Y%m%d%H%M%S') + secrets.token_hex(3)[:6]
    transaction_id = hashlib.md5(f"{order_no}{user['user_id']}{time.time()}".encode()).hexdigest()[:16]

    # 创建待支付订单
    cursor = db.execute(
        'INSERT INTO orders (user_id, amount, balance_added, payment_method, status, transaction_id) VALUES (?, ?, ?, ?, ?, ?)',
        (user['user_id'], amount, balance, payment_method, 'pending', transaction_id)
    )
    db.commit()

    # 生成微信支付二维码数据（模拟）
    qrcode_data = generate_wechat_qr_data(order_no, amount, transaction_id)

    return jsonify({
        'order_no': order_no,
        'transaction_id': transaction_id,
        'amount': amount,
        'balance': balance,
        'qrcode_url': qrcode_data['qrcode_url'],
        'qrcode_data': qrcode_data['data'],
        'expire_at': qrcode_data['expire_at'],
        'message': '请使用微信扫描二维码支付'
    })


# ==================== 查询订单状态 ====================
@user_bp.route('/order/status/<transaction_id>', methods=['GET'])
@require_auth
def order_status(transaction_id):
    """查询订单支付状态"""
    user = get_current_user()
    db = get_db()
    order = db.execute(
        'SELECT * FROM orders WHERE transaction_id = ? AND user_id = ?',
        (transaction_id, user['user_id'])
    ).fetchone()

    if not order:
        return jsonify({'error': '订单不存在'}), 404

    if order['status'] == 'paid':
        return jsonify({
            'order_no': order['order_no'],
            'status': 'paid',
            'amount': float(order['amount']),
            'balance_added': float(order['balance_added']),
            'paid_at': order['paid_at']
        })
    else:
        return jsonify({
            'order_no': order['order_no'],
            'status': order['status'],
            'amount': float(order['amount'])
        })


# ==================== 支付回调（模拟） ====================
@user_bp.route('/order/callback', methods=['POST'])
def payment_callback():
    """
    微信支付回调（实际环境中由微信服务器调用）
    这里用于模拟支付成功后的回调
    """
    data = request.get_json(silent=True) or {}
    transaction_id = data.get('transaction_id', '')
    pay_type = data.get('pay_type', '')  # wechat_notify 或 simulate

    if not transaction_id:
        return jsonify({'error': '缺少交易ID'}), 400

    db = get_db()
    order = db.execute('SELECT * FROM orders WHERE transaction_id = ?', (transaction_id,)).fetchone()
    if not order:
        return jsonify({'error': '订单不存在'}), 404

    if order['status'] == 'paid':
        return jsonify({'status': 'already_paid'})

    # 更新订单状态
    now = datetime.utcnow().isoformat()
    db.execute(
        'UPDATE orders SET status = ?, paid_at = ? WHERE transaction_id = ?',
        ('paid', now, transaction_id)
    )

    # 更新用户余额
    db.execute(
        'UPDATE users SET balance = balance + ?, total_spent = total_spent + ?, updated_at = ? WHERE id = ?',
        (float(order['balance_added']), float(order['amount']), now, order['user_id'])
    )
    db.commit()

    return jsonify({'status': 'success', 'message': '支付成功'})


# ==================== 用量统计 ====================
@user_bp.route('/usage', methods=['GET'])
@require_auth
def usage_stats():
    """获取用户使用统计"""
    user = get_current_user()
    db = get_db()

    today = datetime.utcnow().strftime('%Y-%m-%d')
    this_month = today[:7]

    stats = db.execute('''
        SELECT
            COUNT(*) as total_requests,
            COALESCE(SUM(credits_used), 0) as total_credits,
            SUM(CASE WHEN created_at >= ? THEN 1 ELSE 0 END) as today_requests,
            SUM(CASE WHEN substr(created_at, 1, 10) = ? THEN 1 ELSE 0 END) as month_requests
        FROM usage_logs WHERE user_id = ?
    ''', (today, this_month, user['user_id'])).fetchone()

    recent = db.execute(
        'SELECT endpoint, credits_used, created_at FROM usage_logs WHERE user_id = ? ORDER BY created_at DESC LIMIT 20',
        (user['user_id'],)
    ).fetchall()

    return jsonify({
        'total_requests': stats['total_requests'] or 0,
        'total_credits': float(stats['total_credits'] or 0),
        'today_requests': stats['today_requests'] or 0,
        'month_requests': stats['month_requests'] or 0,
        'recent_usage': [dict(r) for r in recent]
    })


# ==================== 扣费（供其他API调用） ====================
def deduct_credits(user_id, endpoint, credits=1.0, response_size=0):
    """
    从用户账户扣费
    返回 (success, message, remaining_balance)
    """
    db = get_db()
    user = db.execute('SELECT balance FROM users WHERE id = ?', (user_id,)).fetchone()
    if not user:
        return False, '用户不存在', 0

    if user['balance'] < credits:
        return False, f'余额不足，需要{credits}元，当前余额{user["balance"]:.2f}元', float(user['balance'])

    # 扣费
    now = datetime.utcnow().isoformat()
    db.execute(
        'UPDATE users SET balance = balance - ?, updated_at = ? WHERE id = ?',
        (credits, now, user_id)
    )

    # 记录用量
    db.execute(
        'INSERT INTO usage_logs (user_id, endpoint, credits_used, response_size) VALUES (?, ?, ?, ?)',
        (user_id, endpoint, credits, response_size)
    )
    db.commit()

    new_balance = user['balance'] - credits
    return True, '扣费成功', new_balance


# ==================== 辅助函数 ====================

def generate_wechat_qr_data(order_no, amount, transaction_id):
    """生成模拟微信支付二维码数据"""
    expire_minutes = 5
    expire_at = (datetime.utcnow() + timedelta(minutes=expire_minutes)).isoformat()

    # 模拟二维码URL（实际应调用微信支付API生成）
    qrcode_url = f"https://mp.weixin.qq.com/pay/qr?order={order_no}&amount={amount}&tid={transaction_id}"

    return {
        'qrcode_url': qrcode_url,
        'data': {
            'order_no': order_no,
            'amount': amount,
            'transaction_id': transaction_id,
            'expire_at': expire_at
        },
        'expire_at': expire_at
    }


# 注册数据库清理钩子
def register_db_cleanup(app):
    """在Flask应用中注册数据库清理和初始化"""
    app.teardown_appcontext(close_db)
    with app.app_context():
        init_db()
