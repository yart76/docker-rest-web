import requests
import json
from collections import namedtuple
import docker
from time import sleep
from flask_restful import abort
from server import createApp
from flask import request
import socket
from contextlib import closing

app = createApp()

#Add default logging function and debug
#Make proper error handling
#Add commands and state of the container
#Fix strings with port number
#Add remote host availability functionality


def convert(dictionary):
    return namedtuple('GenericDict', dictionary.keys())(**dictionary)

def _is_port_available(host, port):
	app.logger.info("Verifying if port {} is available on {} node".format(port, host))
	with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as sock:
		if sock.connect_ex((host, port)) == 0:
			print("Port {} is used".format(port))
			return False
		else:
			print("Port {} is not used".format(port))
			return True

def _get_port_number(host, init_port=5001): 
	for n in range(app.config.get("DEF_REPLICA_NUMBER")):
		p = init_port + n
		b = _is_port_available(host, p)
		if b: return p
	return None


def _get_available_client():
	app.logger.info("Verify if host available and connection can be specified")
	client = None
	port = None
	for s in app.config.get("L_SERVER").split(","):
		print("Connecting to {} node".format(s))
		client = docker.DockerClient(base_url=('{}://{}:{}').format(app.config.get("DEF_PROTOCOL"), s, app.config.get("DOCKER_PORT")))
		try:
			print("Asking for ping")
			p = client.ping()
			print("Connected to docker instance on {} node".format(s))
			port = _get_port_number(s)
			if port is None:
				app.logger.info("{} node doesn't have any available ports".format(s))
				continue
			break
		except requests.exceptions.RequestException as e:
			print("{} node or connection to it is not available".format(s))
			return(client, s, port)

	return (client, s, port)

def verify_container_running(client, server):
	print("Verify if container is running")
	for c in client.containers.list():
		if app.config.get("DEF_CONTAINER_NAME") == c.name:
			print("{} container is running".format(app.config.get("DEF_CONTAINER_NAME")))
			return c
	print("{} container is not running".format(app.config.get("DEF_CONTAINER_NAME")))
	return None

def verify_image_exists(client, server):
	for i in client.images.list():
		print(i)
		for t in i.tags:
			print(t)
			if app.config.get("DEF_IMAGE_NAME") in t:
				app.logger.info(("{} image exists on the {} node").format(app.config.get("DEF_IMAGE_NAME"), server))
				return i
	
	app.logger.info(("{} image is not yet build or pulled on the {} node").format(app.config.get("DEF_IMAGE_NAME"), server))
	app.logger.info("Pulling {} image".format(app.config.get("FULL_IMAGE_NAME")))
	i = client.images.pull(app.config.get("FULL_IMAGE_NAME"))
	return i

def start_container(client, server, port):
	i = verify_image_exists(client, server)
	if i is None: return None

	ports_formatted = "'{}/{}':{}".format(port, app.config.get("DEF_PROTOCOL"), app.config.get("DEF_CONTAINER_PORT"))
	print(ports_formatted)
	app.logger.info("Starting container from {} image".format(app.config.get("FULL_IMAGE_NAME")))
	c = client.containers.run(app.config.get("FULL_IMAGE_NAME"), name=app.config.get("DEF_CONTAINER_NAME") + str(port), detach=True,
		ports={app.config.get("DEF_CONTAINER_PORT"):port})
	sleep(2)
	return c


	
@app.route('/')
def main() -> str:
    return 'This is reply from main page'

@app.route('/ping')
def ping() -> str:
	ret = "Empty return"
	c = None
	try:
		client, ip_node, port = _get_available_client()
		if (client is None) or (port is None):
			msg = "Unable to connect to any of the servers {}".format(app.config.get("L_SERVER"))
			app.logger.info(msg)
			return msg
		else:
			#c = verify_container_running(client, ip_node)
			#if c is None: c = start_container(client, server)
			c = start_container(client, ip_node, port)
			if c is not None:
				#headers = {'Content-Type': 'text/plain'}
				url = "http://{}:{}{}".format(ip_node, port, request.path)
				app.logger.debug(request.path)
				app.logger.debug(url)
				s = requests.Session()
				req = requests.Request(request.method, url, data=request.data, headers=request.headers)
				prepped = req.prepare()
				r = s.send(prepped)
				#result = convert(r.json())
				print(r.headers)
				ret = r.text
				app.logger.info("Response is received")
				app.logger.info("Stopping container")
				c.stop()
				app.logger.info("Removing container")
				c.remove()
	except docker.errors.DockerException as e:
		app.logger.error(e.explanation)
		abort(500, message=e.explanation)
	finally:
		client.close()
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
