import os
from dotenv import load_dotenv

# path of the application directory
basedir = os.path.abspath(os.path.dirname(__file__))
# load environment variables
load_dotenv(os.path.join(basedir, '.env'))


class Config(object):
    # encryption key for authentications
    SECRET_KEY = os.environ.get('SECRET_KEY') or \
        'ADD_KEY_HERE'

    # database settings
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # mail server settings
    MAIL_SERVER = os.environ.get('MAIL_SERVER')
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 25)
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS') is not None
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    ADMINS = ['ADMIN_EMAILS_HERE']

    # mc rcon server settings
    MC_SERVER_IP = os.environ.get('MC_SERVER_IP')
    MC_SERVER_PASSWORD = os.environ.get('MC_SERVER_PASSWORD')
