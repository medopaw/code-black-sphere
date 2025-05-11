import os
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '..', '.env'))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, '..', 'app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JUDGE0_API_URL = os.environ.get('JUDGE0_API_URL') or 'http://localhost:2358'
    JUDGE0_API_KEY = os.environ.get('JUDGE0_API_KEY') # Optional, leave empty if not used
