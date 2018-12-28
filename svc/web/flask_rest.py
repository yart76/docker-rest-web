from flask import Flask
import requests
import json
from collections import namedtuple
import docker
from time import sleep
from flask_restful import abort

app = Flask(__name__)

def convert(dictionary):
    return namedtuple('GenericDict', dictionary.keys())(**dictionary)

@app.route('/')
def main() -> str:
    return 'This is reply from main page'

@app.route('/ping')
def ping() -> str:
	url = "http://127.0.0.1:5001/ping"
	ret = ""
	try:
		client = docker.from_env()
		c = client.containers.run("python-ping", name='ping', detach=True, ports={'5001/tcp': 5001})
		sleep(2)
		headers = {'Content-Type': 'text/plain'}
		r = requests.get(url)
		print(r.json())
		result = convert(r.json())
		#data = r.json()
		c.stop()
		ret = r.text
		c.stop()
		c.remove()
	except docker.errors.APIError as e:
		abort(500, message=e.explanation)
	return ret



if __name__ == '__main__':
      app.run(host='0.0.0.0', port=5002)
