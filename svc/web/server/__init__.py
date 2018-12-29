from flask import Flask
import os

def createApp():
	app = Flask(__name__)
	#app_settings = os.getenv('APP_SETTINGS', 'server.config.BaseConfig')
	app.config.from_object('server.config.BaseConfig')
	return app