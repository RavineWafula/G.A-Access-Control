# app/__init__.py

# third-party imports
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_bootstrap import Bootstrap
from flask_mail import Mail
from flask_moment import Moment, moment
from flask_pagedown import PageDown

from flask_mqtt import Mqtt
from flask_socketio import SocketIO

import os

#from flask_mysqldb import MySQL

# local imports
from config import app_config

# db variable initialization 
db = SQLAlchemy()
mail = Mail()
moment = Moment()
pagedown = PageDown()
mqtt = Mqtt()
socketio = SocketIO()
bootstrap = Bootstrap()
#mysql = MySQL()

login_manager = LoginManager()
login_manager.login_view = 'auth.login'

log_list = []

def create_app(config_name):
    if os.getenv('FLASK_CONFIG')=='production':
        app = Flask(__name__)
        app.config.update(SECRET_KEY=os.getenv('SECRET_KEY'),
                          SQLALCHEMY_DATABASE_URI=os.getenv('SQLALCHEMY_DATABASE_URI'),
                          FLASKY_ADMIN=os.getenv('FLASKY_ADMIN'),
                          MAIL_USERNAME = os.getenv('MAIL_USERNAME'),
                          MAIL_PASSWORD = os.getenv('MAIL_PASSWORD'),

                          FLASKY_MAIL_SUBJECT_PREFIX = '[G.A Access Control]',
                          FLASKY_MAIL_SENDER = 'G.A Access Control <machaniravine98@gmail.com>',
                          TEMPLATES_AUTO_RELOAD = True,
                          MQTT_BROKER_URL = 'Enivar.mysql.pythonanywhere-services.com',
                          MQTT_BROKER_PORT = 1883,
                          MQTT_CLIENT_ID = 'publisher',
                          MQTT_CLEAN_SESSION = True,
                          SECTRET = '12345678',
                          MQTT_USERNAME = '',
                          MQTT_PASSWORD = '',
                          MQTT_KEEPALIVE = 5,
                          MQTT_TLS_ENABLED = False,
                          MQTT_LAST_WILL_TOPIC = '/dashboard',
                          MQTT_LAST_WILL_MESSAGE = 'bye',
                          MQTT_LAST_WILL_QOS = 2,
                          MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.gmail.com'),
                          MAIL_PORT = int(os.environ.get('MAIL_PORT', '587')),
                          MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'true').lower() in ['true', 'on', '1'])
                    

    else:
        app = Flask(__name__, instance_relative_config=True)
        #app.config.from_object(app_config[config_name])
        app.config.from_pyfile('config.py')
    
    #Bootstrap(app)
    bootstrap.init_app(app)
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_message = "Not logged in!"
    login_manager.login_view = "auth.login"

    mail.init_app(app)
    moment.init_app(app)
    pagedown.init_app(app)
    mqtt.init_app(app)
    socketio.init_app(app)
    #mysql.init_app(app)
    

    migrate = Migrate(app, db)

    from app import models

    from .main import main as main_blueprint
    app.register_blueprint(main_blueprint)

    from .auth import auth as auth_blueprint
    app.register_blueprint(auth_blueprint, url_prefix='/auth')

    try: 
        mqtt.subscribe("transmit", 1)
        print('Subscribed')
    except: print('Not subscribed')
    
    return app

