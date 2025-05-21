"""Test configuration file."""

import os

class TestConfig:
    """Test configuration."""
    
    # Flask
    TESTING = True
    SECRET_KEY = 'test-secret-key'
    
    # Database
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Judge0
    JUDGE0_API_URL = 'http://localhost:2358'
    JUDGE0_API_KEY = 'test-key'
    
    # DeepSeek
    DEEPSEEK_API_KEY = 'test-key'
    
    # Other settings
    DEFAULT_PROBLEM_ID = 1 
