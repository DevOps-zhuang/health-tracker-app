# Configuration settings for the health tracker application

import os
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
load_dotenv()

# Get the base directory of the application
basedir = os.path.abspath(os.path.dirname(__file__))
instance_path = os.path.join(basedir, 'instance')

# Ensure instance directory exists
if not os.path.exists(instance_path):
    os.makedirs(instance_path)

# Configuration class for different environments
class Config:
    # Secret key for session management
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'health-tracker-default-key'
    
    # Database configuration - use absolute path
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        f'sqlite:///{os.path.join(instance_path, "health_tracker.sqlite")}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

class DevelopmentConfig(Config):
    DEBUG = True

class ProductionConfig(Config):
    DEBUG = False

# Select configuration based on environment
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}

# Get current configuration
def get_config():
    env = os.environ.get('FLASK_ENV') or 'default'
    return config[env]
# Generated by Copilot