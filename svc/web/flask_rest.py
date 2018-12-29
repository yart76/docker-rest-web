import requests
import json
from collections import namedtuple
import docker
from time import sleep
from flask_restful import abort
from server import createApp

app = createApp()

#Add default logging function and debug
#Make proper error handling
#Add commands and state of the container
#Fix strings with port number


def convert(dictionary):
    return namedtuple('GenericDict', dictionary.keys())(**dictionary)

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
				print(("{} image exists on the {} node").format(app.config.get("DEF_IMAGE_NAME"), server))
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
	ret = ""
	c = None
	try:
		for s in app.config.get("L_SERVER"):
			print(s)
			client = docker.DockerClient(base_url=('{}://{}:{}').format(app.config.get("DEF_PROTOCOL"), s, app.config.get("DOCKER_PORT")))
			print("Connected to docker instance on {} node".format(s))
			#client = docker.from_env()
			c = verify_container_running(client, s)
			#Add verification about running comntainer?
			if c is not None:
				headers = {'Content-Type': 'text/plain'}
				url = "http://{}:5001/{}".format(s, app.config.get("DEF_PATH"))
				print(url)
				r = requests.get(url)
				print(r.json())
				result = convert(r.json())
				#data = r.json()
				ret = r.text
				c.stop()
				c.remove()
	except docker.errors.APIError as e:
		abort(500, message=e.explanation)
	return ret



if __name__ == '__main__':
      app.run(host='0.0.0.0', port=5002)
