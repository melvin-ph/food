import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'foodshare-super-secret-key-change-in-prod-2026')
    MONGO_URI = os.getenv('MONGO_URI', 'mongodb://localhost:27017/')
    MONGO_DB_NAME = os.getenv('MONGO_DB_NAME', 'foodshare_db')
    APP_ENV = os.getenv('APP_ENV', 'development')
    APP_TIMEZONE = os.getenv('APP_TIMEZONE', 'Asia/Kolkata')
    MAX_CONTENT_LENGTH = int(os.getenv('MAX_CONTENT_LENGTH', 5242880))  # 5MB
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'images', 'uploads')
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = 86400  # 24 hours
