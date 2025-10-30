// 全局状态
let autoCheckEnabled = true;

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
        
        // 更新日志
        updateLogs(data.logs || []);
        
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
