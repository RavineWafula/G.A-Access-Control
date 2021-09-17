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
    app = Flask(__name__, instance_relative_config=True)
    #app.config.from_object(app_config[config_name])
    app.config.from_pyfile('config.py')
    db.init_app(app)
    
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

