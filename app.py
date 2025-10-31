from flask import Flask, render_template, jsonify, request, session, redirect, url_for
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
from functools import wraps
import requests
import atexit
from config import Config
from bot import get_bot_instance

app = Flask(__name__)
app.config['SECRET_KEY'] = Config.SECRET_KEY

server_status = {
    'status': 'unknown',
    'server_address': '',
    'logs_access_token': '',
    'last_check': None,
    'auto_start_count': 0,
    'auto_check_enabled': True
}

bot_status = {
    'status': 'offline',
    'username': Config.BOT_USERNAME,
    'auto_join': Config.BOT_AUTO_JOIN
}

bot = None

logs = []
MAX_LOGS = 100

def add_log(message, level='info'):
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

def init_bot():
    global bot, bot_status
    try:
        bot = get_bot_instance(
            username=Config.BOT_USERNAME,
            auto_join=Config.BOT_AUTO_JOIN,
            log_callback=add_log
        )
        bot_status['username'] = Config.BOT_USERNAME
        bot_status['auto_join'] = Config.BOT_AUTO_JOIN
        add_log(f"机器人已初始化: {Config.BOT_USERNAME}", 'info')
    except Exception as e:
        add_log(f"机器人初始化失败: {str(e)}", 'error')

def update_bot_status():
    global bot_status
    if bot:
        status_info = bot.get_status()
        bot_status['status'] = status_info['status']
        bot_status['reconnect_attempt'] = status_info.get('reconnect_attempt', 0)

def check_server_status():
    if not server_status['auto_check_enabled']:
        add_log("自动检查已暂停", 'info')
        return
    
    previous_status = server_status['status']
    
    try:
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
            
            if isinstance(data, list):
                add_log(f"API 返回列表类型数据，长度: {len(data)}", 'warning')
                if len(data) > 0 and isinstance(data[0], dict):
                    data = data[0]  # 使用列表的第一个元素
                else:
                    add_log("API 返回的列表数据格式异常", 'error')
                    server_status['status'] = 'error'
                    return
            elif not isinstance(data, dict):
                add_log(f"API 返回未知数据类型: {type(data)}", 'error')
                server_status['status'] = 'error'
                return
            
            server_status['status'] = data.get('status', 'unknown')
            server_status['server_address'] = data.get('server_address', '')
            server_status['logs_access_token'] = data.get('logs_access_token', '')
            server_status['last_check'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            add_log(f"服务器状态: {server_status['status']}", 'info')
            
            if server_status['status'] == 'stopped':
                add_log("检测到服务器已停止，尝试启动...", 'warning')
                start_result = start_server()
                if start_result:
                    server_status['auto_start_count'] += 1
                    add_log(f"服务器启动请求已发送（自动启动次数: {server_status['auto_start_count']}）", 'success')
                else:
                    add_log("服务器启动失败", 'error')
                    
                if bot and bot_status['status'] != 'offline':
                    add_log("服务器已停止，断开机器人连接", 'info')
                    bot.leave()
                    
            elif server_status['status'] == 'running' and previous_status != 'running':
                if bot and bot_status['auto_join'] and server_status['server_address']:
                    add_log("检测到服务器已启动，机器人准备加入...", 'info')
                    import threading
                    def delayed_join():
                        import time
                        time.sleep(10)
                        if server_status['status'] == 'running':
                            bot.join(server_status['server_address'])
                    threading.Thread(target=delayed_join, daemon=True).start()
        else:
            add_log(f"状态检查失败: HTTP {response.status_code}", 'error')
            server_status['status'] = 'error'
            
    except Exception as e:
        add_log(f"状态检查异常: {str(e)}", 'error')
        server_status['status'] = 'error'
    
    update_bot_status()

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

def renew_server():
    """续期服务器"""
    if not Config.MINEHOST_COOKIE:
        add_log("错误: MINEHOST_COOKIE 未配置，无法续期", 'error')
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
        
        response = requests.get(Config.RENEW_URL, headers=headers, timeout=10)
        
        if response.status_code in [200, 302]:
            add_log("服务器续期成功", 'success')
            return True
        else:
            add_log(f"续期请求失败: HTTP {response.status_code}", 'error')
            return False
            
    except Exception as e:
        add_log(f"续期请求异常: {str(e)}", 'error')
        return False

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
@login_required
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
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
    session.pop('logged_in', None)
    add_log("用户已登出", 'info')
    return redirect(url_for('login'))

@app.route('/play')
def play():
    return render_template('play.html')

@app.route('/api/status')
@login_required
def api_status():
    update_bot_status()
    return jsonify({
        'status': server_status['status'],
        'server_address': server_status['server_address'],
        'last_check': server_status['last_check'],
        'auto_start_count': server_status['auto_start_count'],
        'auto_check_enabled': server_status['auto_check_enabled'],
        'bot_status': bot_status['status'],
        'bot_username': bot_status['username'],
        'bot_auto_join': bot_status['auto_join'],
        'logs': logs[:50]
    })

@app.route('/api/play-status')
def api_play_status():
    return jsonify({
        'status': server_status['status'],
        'server_address': server_status['server_address'],
        'last_check': server_status['last_check']
    })

@app.route('/api/start', methods=['POST'])
@login_required
def api_start():
    add_log("手动启动服务器请求", 'info')
    result = start_server()
    if result:
        add_log("手动启动成功", 'success')
        check_server_status()
        return jsonify({'success': True, 'message': '启动请求已发送'})
    else:
        return jsonify({'success': False, 'message': '启动请求失败'}), 500

@app.route('/api/toggle-auto', methods=['POST'])
@login_required
def api_toggle_auto():
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
    add_log("手动触发状态检查", 'info')
    check_server_status()
    return jsonify({'success': True, 'message': '状态检查已完成'})

@app.route('/api/console-info')
@login_required
def api_console_info():
    if server_status['status'] != 'running':
        return jsonify({
            'success': False,
            'message': '服务器未运行'
        }), 400
    
    if not server_status['server_address'] or not server_status['logs_access_token']:
        return jsonify({
            'success': False,
            'message': '缺少连接信息'
        }), 400
    
    ws_url = f"wss://logs.minehost.io/?target={server_status['server_address']}&token={server_status['logs_access_token']}"
    
    return jsonify({
        'success': True,
        'ws_url': ws_url,
        'server_address': server_status['server_address'],
        'token': server_status['logs_access_token']
    })

@app.route('/api/console-command', methods=['POST'])
@login_required
def api_console_command():
    if not Config.MINEHOST_COOKIE:
        return jsonify({
            'success': False,
            'message': 'MINEHOST_COOKIE 未配置'
        }), 500
    
    command = request.json.get('command', '')
    if not command:
        return jsonify({
            'success': False,
            'message': '命令不能为空'
        }), 400
    
    try:
        headers = {
            'sec-ch-ua-platform': '"Windows"',
            'X-Requested-With': 'XMLHttpRequest',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36 Edg/142.0.0.0',
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'sec-ch-ua': '"Chromium";v="142", "Microsoft Edge";v="142", "Not_A Brand";v="99"',
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'sec-ch-ua-mobile': '?0',
            'Sec-Fetch-Site': 'same-origin',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Dest': 'empty',
            'host': 'www.minehost.io',
            'Cookie': Config.MINEHOST_COOKIE
        }
        
        form_data = {
            '_drupal_ajax': '1',
            '_triggering_element_name': 'op',
            '_triggering_element_value': 'Send',
            'ajax_page_state[libraries]': 'eJxtTlt2AiEM3RAMS_LE4ZZGgbRJGJ3dF9vxQ09_8rivhHJ2ob4nOoblQ6V7oGzohnT0ZTULqyhS1vFFdaHVeUOs3K-v-IXufwB3h_YJXb4HdOaKtoC7PyxP9bGGIlIqTjTlu_Nq6R0IjTs-xfw0OJUqZ6rRfJ_m8kIZdIPGKsXixrhB_6PNyYfFNuPLVBg7bpznuQr1-Th7sN0cLZ3JEB5Bln7r0iSPih8-z3kw',
            'ajax_page_state[theme]': 'minehost_ui',
            'ajax_page_state[theme_token]': '',
            'command': command,
            'form_build_id': 'form-wAu9OZekYK120Q8pbxPEg9cPqvcniO2JF8LlsxxTP24',
            'form_id': 'server_console_form',
            'form_token': 'f1u4EKkmK_6sK7ag1BF2ClF8BgW70I79nAxTahn0Ww8',
            'server_custom_domain': ''
        }
        
        console_url = f'https://www.minehost.io/server/{Config.MINEHOST_SERVER_ID}/console?ajax_form=1&_wrapper_format=drupal_ajax'
        
        response = requests.post(console_url, headers=headers, data=form_data, timeout=10)
        
        if response.status_code == 200:
            add_log(f"控制台命令已发送: {command}", 'info')
            return jsonify({
                'success': True,
                'message': '命令已发送'
            })
        else:
            add_log(f"控制台命令发送失败: HTTP {response.status_code}", 'error')
            return jsonify({
                'success': False,
                'message': f'命令发送失败: HTTP {response.status_code}'
            }), 500
            
    except Exception as e:
        add_log(f"控制台命令发送异常: {str(e)}", 'error')
        return jsonify({
            'success': False,
            'message': f'命令发送异常: {str(e)}'
        }), 500

@app.route('/api/bot-join', methods=['POST'])
@login_required
def api_bot_join():
    if not bot:
        return jsonify({
            'success': False,
            'message': '机器人未初始化'
        }), 500
    
    if server_status['status'] != 'running':
        return jsonify({
            'success': False,
            'message': '服务器未运行'
        }), 400
    
    if not server_status['server_address']:
        return jsonify({
            'success': False,
            'message': '服务器地址未知'
        }), 400
    
    try:
        add_log(f"手动让机器人加入服务器: {server_status['server_address']}", 'info')
        bot.join(server_status['server_address'])
        return jsonify({
            'success': True,
            'message': '机器人正在加入服务器'
        })
    except Exception as e:
        add_log(f"机器人加入失败: {str(e)}", 'error')
        return jsonify({
            'success': False,
            'message': f'加入失败: {str(e)}'
        }), 500

@app.route('/api/bot-leave', methods=['POST'])
@login_required
def api_bot_leave():
    """让机器人离开服务器"""
    if not bot:
        return jsonify({
            'success': False,
            'message': '机器人未初始化'
        }), 500
    
    try:
        add_log("手动让机器人离开服务器", 'info')
        bot.leave()
        return jsonify({
            'success': True,
            'message': '机器人已离开服务器'
        })
    except Exception as e:
        add_log(f"机器人离开失败: {str(e)}", 'error')
        return jsonify({
            'success': False,
            'message': f'离开失败: {str(e)}'
        }), 500

@app.route('/api/bot-toggle-auto', methods=['POST'])
@login_required
def api_bot_toggle_auto():
    """切换机器人自动加入"""
    global bot_status
    bot_status['auto_join'] = not bot_status['auto_join']
    if bot:
        bot.auto_join = bot_status['auto_join']
    
    status = "已启用" if bot_status['auto_join'] else "已禁用"
    add_log(f"机器人自动加入{status}", 'info')
    
    return jsonify({
        'success': True,
        'auto_join': bot_status['auto_join']
    })

scheduler = BackgroundScheduler()
scheduler.add_job(
    func=check_server_status,
    trigger="interval",
    seconds=Config.CHECK_INTERVAL,
    id='check_status',
    name='检查服务器状态',
    replace_existing=True
)
scheduler.add_job(
    func=renew_server,
    trigger="interval",
    seconds=600,
    id='renew_server',
    name='续期服务器',
    replace_existing=True
)
scheduler.start()

add_log("MineHost 监控服务已启动", 'success')
add_log(f"服务器 ID: {Config.MINEHOST_SERVER_ID}", 'info')
add_log(f"检查间隔: {Config.CHECK_INTERVAL} 秒", 'info')
add_log("自动续期已启用，每10分钟执行一次", 'info')
Config.validate()

init_bot()

check_server_status()

def cleanup():
    scheduler.shutdown()
    if bot:
        bot.shutdown()
        
atexit.register(cleanup)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=7860, debug=False)
