import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Bot configuration class"""
    
    # Discord Configuration
    DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
    BOT_PREFIX = os.getenv('BOT_PREFIX', '!')
    ADMIN_ROLE_ID = int(os.getenv('ADMIN_ROLE_ID', 0))
    
    # Bot Permissions
    BOT_PERMISSIONS = 8  # 봇에게 필요한 모든 권한
    
    # Database Configuration
    DATABASE_TYPE = os.getenv('DATABASE_TYPE', 'sqlite')  # 'sqlite' or 'supabase'
    DATABASE_PATH = os.getenv('DATABASE_PATH', 'database/bot.db')  # SQLite용
    
    # Supabase Configuration
    SUPABASE_URL = os.getenv('SUPABASE_URL')  # Supabase Project URL
    SUPABASE_ANON_KEY = os.getenv('SUPABASE_ANON_KEY')  # Supabase Anon Key
    
    # Logging Configuration
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE = os.getenv('LOG_FILE', 'logs/bot.log')
    
    # Question Form Fields
    REQUIRED_FIELDS = ['os', 'programming_language', 'error_message', 'purpose']
    OPTIONAL_FIELDS = ['code_snippet', 'log_files', 'screenshot', 'attempted_solutions']
    
    @classmethod
    def validate(cls):
        """Validate configuration"""
        if not cls.DISCORD_TOKEN:
            raise ValueError("DISCORD_TOKEN is required")
        if not cls.ADMIN_ROLE_ID:
            raise ValueError("ADMIN_ROLE_ID is required")
        
        # Validate database configuration
        if cls.DATABASE_TYPE == 'supabase':
            if not cls.SUPABASE_URL:
                raise ValueError("SUPABASE_URL is required when using Supabase")
            if not cls.SUPABASE_ANON_KEY:
                raise ValueError("SUPABASE_ANON_KEY is required when using Supabase")
        
        return True