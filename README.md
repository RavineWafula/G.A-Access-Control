# G.A-Access-Control
Access control project with mqtt broker that interfaces with the database.

For usability, add a folder called "instance" in the project folder inside
which you ought to create a "config.py" file where you store the sensitive
configurations of your project that include the following:

SECRET_KEY = ''
SQLALCHEMY_DATABASE_URI = ''
FLASKY_ADMIN = ''
MAIL_SERVER = 'smtp.gmail.com'
MAIL_PORT = '587'
MAIL_USE_TLS = 'true'
MAIL_USERNAME = ''
MAIL_PASSWORD = ''
FLASKY_MAIL_SUBJECT_PREFIX = ''
FLASKY_MAIL_SENDER = ''
TEMPLATES_AUTO_RELOAD = True
MQTT_BROKER_URL = ''
MQTT_BROKER_PORT = 1883
MQTT_CLIENT_ID = ''
MQTT_CLEAN_SESSION = True
SECTRET = ''
MQTT_USERNAME = ''
MQTT_PASSWORD = ''
MQTT_KEEPALIVE = 5
MQTT_TLS_ENABLED = False
MQTT_LAST_WILL_TOPIC = ''
MQTT_LAST_WILL_MESSAGE = 'bye'
MQTT_LAST_WILL_QOS = 2
