from flask import Flask, render_template, jsonify, request, session, redirect, url_for
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
from functools import wraps
import requests
import atexit
from config import Config

app = Flask(__name__)
app.config['SECRET_KEY'] = Config.SECRET_KEY

# 全局状态
server_status = {
    'status': 'unknown',
    'server_address': '',
    'last_check': None,
    'auto_start_count': 0,
    'auto_check_enabled': True
}

# 日志列表（保存最近 100 条）
logs = []
MAX_LOGS = 100

def add_log(message, level='info'):
    """添加日志"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    log_entry = {
        'timestamp': timestamp,
        'message': message,
        'level': level
    }
    logs.insert(0, log_entry)
    if len(logs) > MAX_LOGS:
        logs.pop()
    print(f"[{timestamp}] [{level.upper()}] {message}")

def check_server_status():
    """检查服务器状态并自动启动"""
    if not server_status['auto_check_enabled']:
        add_log("自动检查已暂停", 'info')
        return
    
    try:
        # 检查状态 API
        headers = {
            'sec-ch-ua-platform': '"Windows"',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36 Edg/142.0.0.0',
            'sec-ch-ua': '"Chromium";v="142", "Microsoft Edge";v="142", "Not_A Brand";v="99"',
            'Content-Type': 'application/json',
            'sec-ch-ua-mobile': '?0',
            'Accept': '*/*',
            'Sec-Fetch-Site': 'same-origin',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Dest': 'empty',
            'host': 'www.minehost.io'
        }
        
        response = requests.get(Config.STATUS_API_URL, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            server_status['status'] = data.get('status', 'unknown')
            server_status['server_address'] = data.get('server_address', '')
            server_status['last_check'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            add_log(f"服务器状态: {server_status['status']}", 'info')
            
            # 如果服务器已停止，尝试启动
            if server_status['status'] == 'stopped':
                add_log("检测到服务器已停止，尝试启动...", 'warning')
                start_result = start_server()
                if start_result:
                    server_status['auto_start_count'] += 1
                    add_log(f"服务器启动请求已发送（自动启动次数: {server_status['auto_start_count']}）", 'success')
                else:
                    add_log("服务器启动失败", 'error')
        else:
            add_log(f"状态检查失败: HTTP {response.status_code}", 'error')
            server_status['status'] = 'error'
            
    except Exception as e:
        add_log(f"状态检查异常: {str(e)}", 'error')
        server_status['status'] = 'error'

def start_server():
    """启动服务器"""
    if not Config.MINEHOST_COOKIE:
        add_log("错误: MINEHOST_COOKIE 未配置", 'error')
        return False
    
    try:
        headers = {
            'sec-ch-ua': '"Chromium";v="142", "Microsoft Edge";v="142", "Not_A Brand";v="99"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'Upgrade-Insecure-Requests': '1',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36 Edg/142.0.0.0',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Sec-Fetch-Site': 'same-origin',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-User': '?1',
            'Sec-Fetch-Dest': 'document',
            'host': 'www.minehost.io',
            'Cookie': Config.MINEHOST_COOKIE
        }
        
        response = requests.get(Config.START_URL, headers=headers, timeout=10)
        
        if response.status_code in [200, 302]:
            return True
        else:
            add_log(f"启动请求失败: HTTP {response.status_code}", 'error')
            return False
            
    except Exception as e:
        add_log(f"启动请求异常: {str(e)}", 'error')
        return False

# 密码认证装饰器
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# 路由
@app.route('/')
@login_required
def index():
    """主页"""
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """登录页面"""
    if request.method == 'POST':
        password = request.form.get('password', '')
        if password == Config.WEB_PASSWORD:
            session['logged_in'] = True
            add_log("用户登录成功", 'info')
            return redirect(url_for('index'))
        else:
            add_log("登录失败: 密码错误", 'warning')
            return render_template('login.html', error="密码错误")
    return render_template('login.html')

@app.route('/logout')
def logout():
    """登出"""
    session.pop('logged_in', None)
    add_log("用户已登出", 'info')
    return redirect(url_for('login'))

@app.route('/api/status')
@login_required
def api_status():
    """获取当前状态和日志"""
    return jsonify({
        'status': server_status['status'],
        'server_address': server_status['server_address'],
        'last_check': server_status['last_check'],
        'auto_start_count': server_status['auto_start_count'],
        'auto_check_enabled': server_status['auto_check_enabled'],
        'logs': logs[:50]  # 只返回最近 50 条日志
    })

@app.route('/api/start', methods=['POST'])
@login_required
def api_start():
    """手动启动服务器"""
    add_log("手动启动服务器请求", 'info')
    result = start_server()
    if result:
        add_log("手动启动成功", 'success')
        # 立即检查状态
        check_server_status()
        return jsonify({'success': True, 'message': '启动请求已发送'})
    else:
        return jsonify({'success': False, 'message': '启动请求失败'}), 500

@app.route('/api/toggle-auto', methods=['POST'])
@login_required
def api_toggle_auto():
    """暂停/恢复自动检查"""
    server_status['auto_check_enabled'] = not server_status['auto_check_enabled']
    status = "已恢复" if server_status['auto_check_enabled'] else "已暂停"
    add_log(f"自动检查{status}", 'info')
    return jsonify({
        'success': True,
        'auto_check_enabled': server_status['auto_check_enabled']
    })

@app.route('/api/check-now', methods=['POST'])
@login_required
def api_check_now():
    """立即检查状态"""
    add_log("手动触发状态检查", 'info')
    check_server_status()
    return jsonify({'success': True, 'message': '状态检查已完成'})

# 初始化调度器
scheduler = BackgroundScheduler()
scheduler.add_job(
    func=check_server_status,
    trigger="interval",
    seconds=Config.CHECK_INTERVAL,
    id='check_status',
    name='检查服务器状态',
    replace_existing=True
)
scheduler.start()

# 应用启动时的初始化
add_log("MineHost 监控服务已启动", 'success')
add_log(f"服务器 ID: {Config.MINEHOST_SERVER_ID}", 'info')
add_log(f"检查间隔: {Config.CHECK_INTERVAL} 秒", 'info')
Config.validate()

# 启动时立即检查一次
check_server_status()

# 确保应用退出时关闭调度器
atexit.register(lambda: scheduler.shutdown())

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=7860, debug=False)
