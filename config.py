import os

class Config:
    """配置管理类，从环境变量读取配置"""
    
    # 必需的 Cookie（用于启动服务器）
    MINEHOST_COOKIE = os.environ.get('MINEHOST_COOKIE', '')
    
    # 服务器 ID
    MINEHOST_SERVER_ID = os.environ.get('MINEHOST_SERVER_ID', '181408')
    
    # 网页访问密码
    WEB_PASSWORD = os.environ.get('WEB_PASSWORD', 'admin123')
    
    # 检查间隔（秒）
    CHECK_INTERVAL = int(os.environ.get('CHECK_INTERVAL', '60'))
    
    # Flask 密钥
    SECRET_KEY = os.environ.get('SECRET_KEY', 'your-secret-key-here-change-in-production')
    
    # API URLs
    STATUS_API_URL = f'https://www.minehost.io/api/server/{MINEHOST_SERVER_ID}/status'
    START_URL = f'https://www.minehost.io/server/{MINEHOST_SERVER_ID}/start'
    
    @classmethod
    def validate(cls):
        """验证必需的配置是否存在"""
        if not cls.MINEHOST_COOKIE:
            print("警告: MINEHOST_COOKIE 未设置，启动服务器功能将无法使用")
        return True
