import os
from datetime import timedelta
from dotenv import load_dotenv
import urllib.parse

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))


raw_db_url = os.environ.get('DATABASE_URL')

if raw_db_url and raw_db_url.startswith("postgres://"):
    SQLALCHEMY_DATABASE_URI = raw_db_url.replace("postgres://", "postgresql+psycopg2://", 1)
elif raw_db_url:
    SQLALCHEMY_DATABASE_URI = raw_db_url

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY')
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)
    
    SQLALCHEMY_DATABASE_URI = SQLALCHEMY_DATABASE_URI
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    SQLALCHEMY_POOL_RECYCLE = 300
    SQLALCHEMY_POOL_SIZE = 5
    SQLALCHEMY_POOL_TIMEOUT = 10