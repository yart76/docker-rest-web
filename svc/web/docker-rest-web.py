import requests
import json
from collections import namedtuple
import docker
from time import sleep
from flask_restful import abort
from server import createApp
from flask import request

app = createApp()

#Add default logging function and debug
#Make proper error handling
#Add commands and state of the container
#Fix strings with port number
#Add remote host availability functionality


def convert(dictionary):
    return namedtuple('GenericDict', dictionary.keys())(**dictionary)

def get_available_client():
	app.logger.info("Verify if host available and connection can be specified")
	client = None
	for s in app.config.get("L_SERVER").split(","):
		print("Connecting to {} node".format(s))
		client = docker.DockerClient(base_url=('{}://{}:{}').format(app.config.get("DEF_PROTOCOL"), s, app.config.get("DOCKER_PORT")))
		try:
			print("Asking for ping")
			p = client.ping()
			print("Connected to docker instance on {} node".format(s))
			break
		except requests.exceptions.RequestException as e:
			print("{} node or connection to it is not available".format(s))		

	return (client, s)

def verify_container_running(client, server):
	print("Verify if container is running")
	for c in client.containers.list():
		if app.config.get("DEF_CONTAINER_NAME") == c.name:
			print("{} container is running".format(app.config.get("DEF_CONTAINER_NAME")))
			return c
		else:
			print("{} container is not running".format(app.config.get("DEF_CONTAINER_NAME")))
	return start_container(client, server)


def start_container(client, server):
	for i in client.images.list():
		print(i)
		for t in i.tags:
			print(t)
			if app.config.get("DEF_IMAGE_NAME") in t:
				app.logger.info(("{} image exists on the {} node").format(app.config.get("DEF_IMAGE_NAME"), server))
				ports_formatted = "'{}/{}':{}".format(app.config.get("DEF_CONTAINER_PORT"), 
					app.config.get("DEF_PROTOCOL"), app.config.get("DEF_CONTAINER_PORT"))
				print(ports_formatted)
				c = client.containers.run(app.config.get("DEF_IMAGE_NAME"), name=app.config.get("DEF_CONTAINER_NAME"), detach=True,
					ports={'5001/tcp':5001})
				sleep(2)
				return c
	
	print(("{} image is not yet build on the {} node").format(app.config.get("DEF_IMAGE_NAME"), server))
	return None


@app.route('/')
def main() -> str:
    return 'This is reply from main page'

@app.route('/ping')
def ping() -> str:
	ret = "Empty return"
	c = None
	try:
		client, ip_node = get_available_client()
		if client is None:
			msg = "Unable to connect to any of the servers {}", app.config.get("L_SERVER")
			app.logger.info(msg)
			return "Unable to connect to any of the servers {}", app.config.get("L_SERVER")
		else:
			c = verify_container_running(client, ip_node) 
			#headers = {'Content-Type': 'text/plain'}
			url = "http://{}:5001{}".format(ip_node, request.path)
			app.logger.debug(request.path)
			app.logger.debug(url)
			s = requests.Session()
			req = requests.Request(request.method, url, data=request.data, headers=request.headers)
			prepped = req.prepare()
			r = s.send(prepped)
			#result = convert(r.json())
			print(r.headers)
			ret = r.text
			c.stop()
			c.remove()
		client.close()
	except docker.errors.DockerException as e:
		app.logger.error(e.explanation)
		abort(500, message=e.explanation)
	return ret


@app.route('/stats')
def stats():
	app.logger.debug("Stats page")
	app.logger.info("Accessing Stats page")
	app.logger.error("Error page")
	print(request.method)
	print(request.headers)
	print(request.path)
	print(request.data)
	return resp.text

if __name__ == '__main__':
      app.run(host='0.0.0.0', port=5002)
