# run.py
import os
from logging import debug
from app import create_app

from app import socketio

config_name = os.getenv('FLASK_CONFIG')
app = create_app(config_name)
app.debug = True

if __name__ == '__main__':
    #app.run()
    socketio.run(app, host='127.0.0.1', port=5000, use_reloader=False, debug=False, threaded=True)
    