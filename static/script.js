// 全局状态
let autoCheckEnabled = true;
let consoleWebSocket = null;
let lastServerStatus = 'unknown';
let reconnectTimer = null;

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', function() {
    // 立即加载一次状态
    updateStatus();
    
    // 每 5 秒自动刷新状态
    setInterval(updateStatus, 5000);
});

// 更新服务器状态
async function updateStatus() {
    try {
        const response = await fetch('/api/status');
        if (!response.ok) {
            throw new Error('获取状态失败');
        }
        
        const data = await response.json();
        
        // 更新状态显示
        const statusIndicator = document.getElementById('statusIndicator');
        const statusText = document.getElementById('statusText');
        const serverAddress = document.getElementById('serverAddress');
        
        // 移除所有状态类
        statusIndicator.className = 'status-indicator';
        
        // 根据状态设置样式和文本
        switch(data.status) {
            case 'running':
                statusIndicator.classList.add('running');
                statusText.textContent = '运行中';
                break;
            case 'stopped':
                statusIndicator.classList.add('stopped');
                statusText.textContent = '已停止';
                break;
            case 'unknown':
                statusText.textContent = '未知';
                break;
            case 'error':
                statusIndicator.classList.add('error');
                statusText.textContent = '错误';
                break;
            default:
                statusText.textContent = data.status;
        }
        
        // 更新服务器地址
        if (data.server_address) {
            serverAddress.textContent = `服务器地址: ${data.server_address}`;
        } else {
            serverAddress.textContent = '';
        }
        
        // 更新统计信息
        document.getElementById('autoStartCount').textContent = data.auto_start_count || 0;
        document.getElementById('lastCheck').textContent = data.last_check || '--';
        
        // 更新自动检查按钮
        autoCheckEnabled = data.auto_check_enabled;
        const btnToggleAuto = document.getElementById('btnToggleAuto');
        if (autoCheckEnabled) {
            btnToggleAuto.textContent = '⏸️ 暂停自动检查';
            btnToggleAuto.classList.remove('btn-primary');
            btnToggleAuto.classList.add('btn-secondary');
        } else {
            btnToggleAuto.textContent = '▶️ 恢复自动检查';
            btnToggleAuto.classList.remove('btn-secondary');
            btnToggleAuto.classList.add('btn-primary');
        }
        
        // 更新机器人状态
        updateBotStatus(data);
        
        // 更新日志
        updateLogs(data.logs || []);
        
        // 管理控制台连接
        manageConsoleConnection(data.status);
        
    } catch (error) {
        console.error('更新状态失败:', error);
    }
}

// 更新日志显示
function updateLogs(logs) {
    const logsContainer = document.getElementById('logsContainer');
    
    if (logs.length === 0) {
        logsContainer.innerHTML = '<div class="log-item info"><span class="log-time">--:--:--</span><span class="log-message">暂无日志</span></div>';
        return;
    }
    
    logsContainer.innerHTML = logs.map(log => {
        const time = log.timestamp.split(' ')[1]; // 只显示时间部分
        return `
            <div class="log-item ${log.level}">
                <span class="log-time">${time}</span>
                <span class="log-message">${escapeHtml(log.message)}</span>
            </div>
        `;
    }).join('');
}

// HTML 转义
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// 手动启动服务器
async function startServer() {
    const btn = document.getElementById('btnStart');
    btn.disabled = true;
    btn.textContent = '🚀 启动中...';
    
    try {
        const response = await fetch('/api/start', {
            method: 'POST'
        });
        
        const data = await response.json();
        
        if (data.success) {
            showNotification('服务器启动请求已发送', 'success');
            // 立即刷新状态
            setTimeout(updateStatus, 1000);
        } else {
            showNotification(data.message || '启动失败', 'error');
        }
    } catch (error) {
        showNotification('请求失败: ' + error.message, 'error');
    } finally {
        btn.disabled = false;
        btn.textContent = '🚀 手动启动服务器';
    }
}

// 切换自动检查
async function toggleAuto() {
    const btn = document.getElementById('btnToggleAuto');
    btn.disabled = true;
    
    try {
        const response = await fetch('/api/toggle-auto', {
            method: 'POST'
        });
        
        const data = await response.json();
        
        if (data.success) {
            const status = data.auto_check_enabled ? '已恢复' : '已暂停';
            showNotification(`自动检查${status}`, 'success');
            updateStatus();
        }
    } catch (error) {
        showNotification('操作失败: ' + error.message, 'error');
    } finally {
        btn.disabled = false;
    }
}

// 立即检查状态
async function checkNow() {
    const btn = document.getElementById('btnCheckNow');
    btn.disabled = true;
    btn.textContent = '🔄 检查中...';
    
    try {
        const response = await fetch('/api/check-now', {
            method: 'POST'
        });
        
        const data = await response.json();
        
        if (data.success) {
            showNotification('状态检查完成', 'success');
            // 立即刷新状态
            setTimeout(updateStatus, 500);
        }
    } catch (error) {
        showNotification('检查失败: ' + error.message, 'error');
    } finally {
        btn.disabled = false;
        btn.textContent = '🔄 立即检查状态';
    }
}

// 显示通知（简单实现）
function showNotification(message, type) {
    // 这里可以使用更复杂的通知系统
    console.log(`[${type.toUpperCase()}] ${message}`);
    
    // 创建临时通知元素
    const notification = document.createElement('div');
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 16px 24px;
        background: ${type === 'success' ? '#4caf50' : '#f44336'};
        color: white;
        border-radius: 8px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.3);
        z-index: 9999;
        animation: slideIn 0.3s ease-out;
    `;
    notification.textContent = message;
    
    document.body.appendChild(notification);
    
    // 3 秒后移除
    setTimeout(() => {
        notification.style.animation = 'slideOut 0.3s ease-in';
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}

// 添加动画样式
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from {
            transform: translateX(400px);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }
    
    @keyframes slideOut {
        from {
            transform: translateX(0);
            opacity: 1;
        }
        to {
            transform: translateX(400px);
            opacity: 0;
        }
    }
`;
document.head.appendChild(style);

function manageConsoleConnection(serverStatus) {
    if (serverStatus === 'running' && lastServerStatus !== 'running') {
        // 服务器刚启动，连接控制台
        connectConsole();
    } else if (serverStatus !== 'running' && lastServerStatus === 'running') {
        // 服务器停止，断开控制台
        disconnectConsole();
    }
    lastServerStatus = serverStatus;
}

// 连接控制台
async function connectConsole() {
    try {
        updateConsoleStatus('connecting', '连接中...');
        
        const response = await fetch('/api/console-info');
        if (!response.ok) {
            throw new Error('获取连接信息失败');
        }
        
        const data = await response.json();
        
        if (!data.success) {
            addConsoleMessage(data.message, 'error');
            updateConsoleStatus('disconnected', '未连接');
            return;
        }
        
        // 创建 WebSocket 连接
        consoleWebSocket = new WebSocket(data.ws_url);
        
        consoleWebSocket.onopen = () => {
            updateConsoleStatus('connected', '已连接');
            addConsoleMessage('控制台已连接', 'system');
            enableConsoleInput();
        };
        
        consoleWebSocket.onmessage = (event) => {
            // 接收控制台消息
            try {
                // 尝试解析 JSON 格式
                const message = JSON.parse(event.data);
                if (message.content) {
                    // 按行分割并显示
                    const lines = message.content.split('\n');
                    lines.forEach(line => {
                        if (line.trim()) {
                            addConsoleMessage(line, 'log');
                        }
                    });
                }
            } catch (e) {
                // 如果不是 JSON，直接显示
                addConsoleMessage(event.data, 'log');
            }
        };
        
        consoleWebSocket.onerror = (error) => {
            console.error('WebSocket 错误:', error);
            addConsoleMessage('连接错误', 'error');
        };
        
        consoleWebSocket.onclose = () => {
            updateConsoleStatus('disconnected', '未连接');
            addConsoleMessage('控制台已断开', 'system');
            disableConsoleInput();
            
            // 如果服务器仍在运行，尝试重连
            if (lastServerStatus === 'running') {
                scheduleReconnect();
            }
        };
        
    } catch (error) {
        console.error('连接控制台失败:', error);
        addConsoleMessage('连接失败: ' + error.message, 'error');
        updateConsoleStatus('disconnected', '未连接');
    }
}

// 断开控制台
function disconnectConsole() {
    if (consoleWebSocket) {
        consoleWebSocket.close();
        consoleWebSocket = null;
    }
    
    if (reconnectTimer) {
        clearTimeout(reconnectTimer);
        reconnectTimer = null;
    }
    
    updateConsoleStatus('disconnected', '未连接');
    disableConsoleInput();
    addConsoleMessage('服务器已停止', 'system');
}

// 计划重连
function scheduleReconnect() {
    if (reconnectTimer) {
        clearTimeout(reconnectTimer);
    }
    
    reconnectTimer = setTimeout(() => {
        if (lastServerStatus === 'running') {
            addConsoleMessage('正在重新连接...', 'system');
            connectConsole();
        }
    }, 5000);
}

// 更新控制台状态显示
function updateConsoleStatus(status, text) {
    const statusElement = document.getElementById('consoleStatus');
    statusElement.className = 'console-status';
    
    if (status === 'connected') {
        statusElement.classList.add('connected');
    } else if (status === 'connecting') {
        statusElement.classList.add('connecting');
    }
    
    statusElement.textContent = text;
}

function stripAnsiCodes(text) {
    if (!text) return '';
    return text
        .replace(/[\u001B\u009B][[\]()#;?]*(?:[0-9]{1,4}(?:;[0-9]{0,4})*)?[0-9A-ORZcf-nqry=><]/g, '')
        .replace(/[\u0000-\u0008\u000B-\u000C\u000E-\u001F\u007F-\u009F]/g, '');
}

function addConsoleMessage(message, type = 'log') {
    const output = document.getElementById('consoleOutput');
    const line = document.createElement('div');
    line.className = `console-line ${type}`;
    
    const cleanMessage = stripAnsiCodes(message);
    
    const timestamp = new Date().toLocaleTimeString('zh-CN', { hour12: false });
    
    if (type === 'command') {
        line.textContent = `> ${cleanMessage}`;
    } else if (type === 'system' || type === 'error') {
        line.textContent = `[${timestamp}] ${cleanMessage}`;
    } else {
        line.textContent = cleanMessage;
    }
    
    output.appendChild(line);
    
    output.scrollTop = output.scrollHeight;
    
    while (output.children.length > 500) {
        output.removeChild(output.firstChild);
    }
}

// 启用控制台输入
function enableConsoleInput() {
    const input = document.getElementById('consoleInput');
    const button = document.getElementById('btnConsoleSend');
    
    input.disabled = false;
    button.disabled = false;
    
    input.onkeypress = (e) => {
        if (e.key === 'Enter') {
            sendConsoleCommand();
        }
    };
}

// 禁用控制台输入
function disableConsoleInput() {
    const input = document.getElementById('consoleInput');
    const button = document.getElementById('btnConsoleSend');
    
    input.disabled = true;
    button.disabled = true;
    input.onkeypress = null;
}

// 发送控制台命令
async function sendConsoleCommand() {
    const input = document.getElementById('consoleInput');
    const command = input.value.trim();
    
    if (!command) {
        return;
    }
    
    // 显示命令
    addConsoleMessage(command, 'command');
    
    // 清空输入框
    input.value = '';
    
    try {
        const response = await fetch('/api/console-command', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ command })
        });
        
        const data = await response.json();
        
        if (!data.success) {
            addConsoleMessage(`命令发送失败: ${data.message}`, 'error');
        }
        
    } catch (error) {
        addConsoleMessage(`命令发送异常: ${error.message}`, 'error');
    }
}

function updateBotStatus(data) {
    const statusIndicator = document.getElementById('botStatusIndicator');
    const statusText = document.getElementById('botStatusText');
    const username = document.getElementById('botUsername');
    const btnJoin = document.getElementById('btnBotJoin');
    const btnLeave = document.getElementById('btnBotLeave');
    const btnToggleBotAuto = document.getElementById('btnToggleBotAuto');
    
    if (data.bot_username) {
        username.textContent = data.bot_username;
    }
    
    statusIndicator.className = 'bot-status-indicator';
    
    switch(data.bot_status) {
        case 'online':
            statusIndicator.classList.add('online');
            statusText.textContent = '在线';
            btnJoin.disabled = true;
            btnLeave.disabled = false;
            break;
        case 'connecting':
            statusIndicator.classList.add('connecting');
            statusText.textContent = '连接中...';
            btnJoin.disabled = true;
            btnLeave.disabled = false;
            break;
        case 'offline':
            statusIndicator.classList.add('offline');
            statusText.textContent = '离线';
            btnJoin.disabled = false;
            btnLeave.disabled = true;
            break;
        case 'error':
            statusIndicator.classList.add('error');
            statusText.textContent = '错误';
            btnJoin.disabled = false;
            btnLeave.disabled = false;
            break;
        default:
            statusText.textContent = data.bot_status;
    }
    
    // 更新自动加入按钮
    if (data.bot_auto_join) {
        btnToggleBotAuto.textContent = '🔄 自动加入: 开';
        btnToggleBotAuto.classList.remove('btn-secondary');
        btnToggleBotAuto.classList.add('btn-success');
    } else {
        btnToggleBotAuto.textContent = '🔄 自动加入: 关';
        btnToggleBotAuto.classList.remove('btn-success');
        btnToggleBotAuto.classList.add('btn-secondary');
    }
}

// 让机器人加入服务器
async function joinBot() {
    const btn = document.getElementById('btnBotJoin');
    btn.disabled = true;
    
    try {
        const response = await fetch('/api/bot-join', {
            method: 'POST'
        });
        
        const data = await response.json();
        
        if (data.success) {
            showNotification('机器人正在加入服务器', 'success');
            setTimeout(updateStatus, 1000);
        } else {
            showNotification(data.message || '加入失败', 'error');
            btn.disabled = false;
        }
    } catch (error) {
        showNotification('请求失败: ' + error.message, 'error');
        btn.disabled = false;
    }
}

// 让机器人离开服务器
async function leaveBot() {
    const btn = document.getElementById('btnBotLeave');
    btn.disabled = true;
    
    try {
        const response = await fetch('/api/bot-leave', {
            method: 'POST'
        });
        
        const data = await response.json();
        
        if (data.success) {
            showNotification('机器人已离开服务器', 'success');
            setTimeout(updateStatus, 1000);
        } else {
            showNotification(data.message || '离开失败', 'error');
        }
    } catch (error) {
        showNotification('请求失败: ' + error.message, 'error');
    } finally {
        btn.disabled = false;
    }
}

// 切换机器人自动加入
async function toggleBotAuto() {
    const btn = document.getElementById('btnToggleBotAuto');
    btn.disabled = true;
    
    try {
        const response = await fetch('/api/bot-toggle-auto', {
            method: 'POST'
        });
        
        const data = await response.json();
        
        if (data.success) {
            const status = data.auto_join ? '已启用' : '已禁用';
            showNotification(`机器人自动加入${status}`, 'success');
            updateStatus();
        }
    } catch (error) {
        showNotification('操作失败: ' + error.message, 'error');
    } finally {
        btn.disabled = false;
    }
}
