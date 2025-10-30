import threading
import time
from datetime import datetime
from quarry.net.client import ClientFactory, ClientProtocol
from twisted.internet import reactor, defer
from twisted.internet.error import ConnectionRefusedError, TimeoutError as TwistedTimeoutError
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MinecraftBot(ClientProtocol):
    
    def __init__(self, factory, addr):
        super().__init__(factory, addr)
        self.display_name = factory.display_name
        
    def packet_position_look(self, buff):
        buff.unpack('dddff?')
        
    def packet_keep_alive(self, buff):
        identifier = buff.unpack('Q')
        self.send_packet('keep_alive', self.buff_type.pack('Q', identifier))
        
    def packet_disconnect(self, buff):
        reason = buff.unpack_chat()
        logger.info(f"机器人 {self.display_name} 被断开: {reason}")
        if self.factory.bot_manager:
            self.factory.bot_manager.on_disconnected(reason)


class BotFactory(ClientFactory):
    protocol = MinecraftBot
    
    def __init__(self, username, bot_manager=None):
        super().__init__()
        self.display_name = username
        self.bot_manager = bot_manager
        self.online_mode = False
        self.profile = type('Profile', (), {
            'name': username,
            'display_name': username,
            'uuid': None
        })()
        
    def buildProtocol(self, addr):
        """构建协议实例"""
        protocol = self.protocol(self, addr)
        protocol.display_name = self.display_name
        return protocol


class BotManager:
    
    def __init__(self, username="WakeUpBot", auto_join=True, log_callback=None):
        self.username = username
        self.auto_join = auto_join
        self.log_callback = log_callback
        
        # 状态
        self.status = 'offline'  # offline, connecting, online, error
        self.host = None
        self.port = None
        self.factory = None
        self.connector = None
        
        self.max_reconnect_attempts = 3
        self.reconnect_delay = 5
        self.current_reconnect_attempt = 0
        
        self.lock = threading.Lock()
        
        self.reactor_thread = None
        self.reactor_running = False
        
    def add_log(self, message, level='info'):
        logger.info(f"[Bot] {message}")
        if self.log_callback:
            self.log_callback(message, level)
    
    def set_status(self, status):
        with self.lock:
            self.status = status
            self.add_log(f"机器人状态: {status}", 'info')
    
    def get_status(self):
        with self.lock:
            return {
                'status': self.status,
                'username': self.username,
                'host': self.host,
                'port': self.port,
                'reconnect_attempt': self.current_reconnect_attempt
            }
    
    def start_reactor(self):
        if not self.reactor_running:
            self.reactor_thread = threading.Thread(target=self._run_reactor, daemon=True)
            self.reactor_thread.start()
            time.sleep(1)  # 等待 reactor 启动
            
    def _run_reactor(self):
        try:
            self.reactor_running = True
            self.add_log("Twisted reactor 已启动", 'info')
            reactor.run(installSignalHandlers=False)
        except Exception as e:
            self.add_log(f"Reactor 错误: {str(e)}", 'error')
        finally:
            self.reactor_running = False
    
    def parse_server_address(self, server_address):
        if ':' in server_address:
            parts = server_address.split(':')
            host = parts[0]
            try:
                port = int(parts[1])
            except (ValueError, IndexError):
                port = 25565
        else:
            host = server_address
            port = 25565
            
        return host, port
    
    def join(self, server_address):
        if not server_address:
            self.add_log("错误: 服务器地址为空", 'error')
            self.set_status('error')
            return False
            
        # 解析地址
        self.host, self.port = self.parse_server_address(server_address)
        self.add_log(f"正在连接到 {self.host}:{self.port}...", 'info')
        self.set_status('connecting')
        
        # 启动 reactor（如果尚未运行）
        if not self.reactor_running:
            self.start_reactor()
        
        # 创建工厂并连接
        try:
            self.factory = BotFactory(self.username, bot_manager=self)
            
            # 在 reactor 线程中执行连接
            def connect():
                try:
                    self.connector = reactor.connectTCP(self.host, self.port, self.factory)
                    self.add_log(f"机器人 {self.username} 正在连接...", 'info')
                    self.set_status('online')
                    self.current_reconnect_attempt = 0
                except Exception as e:
                    self.add_log(f"连接失败: {str(e)}", 'error')
                    self.set_status('error')
                    self.schedule_reconnect()
            
            reactor.callFromThread(connect)
            return True
            
        except Exception as e:
            self.add_log(f"加入服务器失败: {str(e)}", 'error')
            self.set_status('error')
            return False
    
    def leave(self):
        try:
            if self.connector and self.reactor_running:
                connector_ref = self.connector
                def disconnect():
                    try:
                        if connector_ref is not None:
                            connector_ref.disconnect()
                            self.add_log(f"机器人 {self.username} 已断开连接", 'info')
                    except Exception as e:
                        self.add_log(f"断开连接时出错: {str(e)}", 'warning')
                
                reactor.callFromThread(disconnect)
            elif self.connector:
                self.add_log(f"机器人 {self.username} 已断开连接 (reactor未运行)", 'info')
                
            self.connector = None
            self.factory = None
            self.set_status('offline')
            self.current_reconnect_attempt = 0
            return True
            
        except Exception as e:
            self.add_log(f"离开服务器失败: {str(e)}", 'error')
            return False
    
    def on_disconnected(self, reason):
        self.add_log(f"连接断开: {reason}", 'warning')
        self.set_status('offline')
        
        # 尝试重连（如果启用了自动加入）
        if self.auto_join and self.host:
            self.schedule_reconnect()
    
    def schedule_reconnect(self):
        if self.current_reconnect_attempt >= self.max_reconnect_attempts:
            self.add_log(f"已达到最大重连次数 ({self.max_reconnect_attempts})，停止重连", 'error')
            self.set_status('error')
            return
        
        self.current_reconnect_attempt += 1
        self.add_log(f"将在 {self.reconnect_delay} 秒后尝试重连 (尝试 {self.current_reconnect_attempt}/{self.max_reconnect_attempts})...", 'info')
        
        def reconnect():
            time.sleep(self.reconnect_delay)
            if self.host and self.status != 'online':
                self.join(f"{self.host}:{self.port}")
        
        reconnect_thread = threading.Thread(target=reconnect, daemon=True)
        reconnect_thread.start()
    
    def shutdown(self):
        self.add_log("正在关闭机器人...", 'info')
        self.leave()
        
        if self.reactor_running:
            try:
                reactor.callFromThread(reactor.stop)
            except:
                pass


# 全局机器人实例
_bot_instance = None


def get_bot_instance(username="WakeUpBot", auto_join=True, log_callback=None):
    global _bot_instance
    if _bot_instance is None:
        _bot_instance = BotManager(username, auto_join, log_callback)
    return _bot_instance


def reset_bot_instance():
    global _bot_instance
    if _bot_instance:
        _bot_instance.shutdown()
    _bot_instance = None

