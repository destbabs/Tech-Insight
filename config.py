import os
from datetime import timedelta

class Config:
    # Flask
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key-here'
    
    # Session
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
    
    # Cache
    CACHE_TYPE = 'simple'
    CACHE_DEFAULT_TIMEOUT = 300
    
    # File paths
    BOOKMARKS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'bookmarks')
    
    # API Keys (should be set in environment variables)
    OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
    NEWS_API_KEY = os.environ.get('NEWS_API_KEY')
    
    # Logging
    LOG_LEVEL = 'INFO'
    LOG_FILE = 'app.log' 