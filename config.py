import os

class Config:
    
    MINEHOST_COOKIE = os.environ.get('MINEHOST_COOKIE', '')
    
    MINEHOST_SERVER_ID = os.environ.get('MINEHOST_SERVER_ID', '181408')
    
    WEB_PASSWORD = os.environ.get('WEB_PASSWORD', 'admin123')
    
    CHECK_INTERVAL = int(os.environ.get('CHECK_INTERVAL', '60'))
    
    SECRET_KEY = os.environ.get('SECRET_KEY', 'your-secret-key-here-change-in-production')
    
    STATUS_API_URL = f'https://www.minehost.io/api/server/{MINEHOST_SERVER_ID}/status'
    START_URL = f'https://www.minehost.io/server/{MINEHOST_SERVER_ID}/start'
    
    BOT_USERNAME = os.environ.get('BOT_USERNAME', 'WakeUpBot')
    BOT_AUTO_JOIN = os.environ.get('BOT_AUTO_JOIN', 'true').lower() == 'true'
    
    @classmethod
    def validate(cls):
        if not cls.MINEHOST_COOKIE:
            print("警告: MINEHOST_COOKIE 未设置，启动服务器功能将无法使用")
        return True
