import requests
import json
from collections import namedtuple
import docker
from time import sleep
from flask_restful import abort
from server import createApp
from flask import request, jsonify
import socket
from contextlib import closing
import redis

app = createApp()
redis_c = redis.from_url(app.config.get("DEF_REDIS_URL"), charset="utf-8", decode_responses=True)

"""Dictionary for storing stats data"""
stats_map = {"n_visits": redis_c.get("n_visits"),
		"n_cntr_provisioned": redis_c.get("n_cntr_provisioned"),
		"n_cntr_accessed": redis_c.get("n_cntr_accessed"),
}

"""Container statuses"""
RUNNING = "running"
STOPPED = "stopped"
REMOVED = "removed"

#Add default logging function and debug
#Make proper error handling
#Add commands and state of the container

def _is_port_available(host, port):
	app.logger.info("Verifying if port {} is available on {} node".format(port, host))
	with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as sock:
		if sock.connect_ex((host, port)) == 0:
			app.logger.debug("Port {} is used".format(port))
			return False
		else:
			app.logger.debug("Port {} is not used".format(port))
			return True

def _get_port_number(host, init_port=5001): 
	for n in range(int(app.config.get("DEF_REPLICA_NUMBER"))):
		p = init_port + n
		b = _is_port_available(host, p)
		if b: return p
	return None


def _get_available_client():
	app.logger.info("Verify if host available and connection can be specified")
	client = None
	port = None
	for s in app.config.get("L_SERVER").split(","):
		app.logger.info("Connecting to {} node".format(s))
		client = docker.DockerClient(base_url=('{}://{}:{}').format(app.config.get("DEF_PROTOCOL"), s, app.config.get("DOCKER_PORT")))
		try:
			app.logger.debug("Asking for ping")
			p = client.ping()
			app.logger.info("Connected to docker instance on {} node".format(s))
			port = _get_port_number(s)
			if port is None:
				app.logger.info("{} node doesn't have any available ports".format(s))
				continue
			break
		except requests.exceptions.RequestException as e:
			app.logger.error("{} node or connection to it is not available".format(s))
			return(client, s, port)

	return (client, s, port)

def verify_container_running(client, server):
	app.logger.info("Verify if container is running")
	for c in client.containers.list():
		if app.config.get("DEF_CONTAINER_NAME") == c.name:
			app.logger.info("{} container is running".format(app.config.get("DEF_CONTAINER_NAME")))
			return c
	app.logger.info("{} container is not running".format(app.config.get("DEF_CONTAINER_NAME")))
	return None

def verify_image_exists(client, server):
	for i in client.images.list():
		app.logger.info(i)
		for t in i.tags:
			app.logger.info(t)
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
	app.logger.info(ports_formatted)
	app.logger.info("Starting container from {} image".format(app.config.get("FULL_IMAGE_NAME")))
	c = client.containers.run(app.config.get("FULL_IMAGE_NAME"), name=app.config.get("DEF_CONTAINER_NAME") + str(port), detach=True,
		ports={app.config.get("DEF_CONTAINER_PORT"):port})
	sleep(2)

	cntr = {"cntr_id": c.id,
    	"name": c.name,
    	"status": c.status,
    	"accessed": 0,
    	"port": port,
    	"node": server}

	redis_c.hmset("cntr_%s" % c.short_id, cntr)
	stats_map["n_cntr_provisioned"] = redis_c.incr('n_cntr_provisioned')
	return c


	
@app.route('/')
def main() -> str:
    return 'This is reply from main page'

@app.route('/ping')
def ping() -> str:
	stats_map["n_visits"]=redis_c.incr('n_visits')
	ret = "Empty return"
	c = None
	client = None
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
				stats_map["n_cntr_accessed"]=redis_c.incr('n_cntr_accessed')
				redis_c.hmset("cntr_%s" % c.short_id, {"status": RUNNING, "accessed": 1})				
				ret = r.text
				app.logger.info("Response is received")
				app.logger.info("Stopping container")
				c.stop()
				redis_c.hmset("cntr_%s" % c.short_id, {"status": STOPPED})
				app.logger.info("Removing container")
				c.remove()
				redis_c.hmset("cntr_%s" % c.short_id, {"status": REMOVED})
	except docker.errors.DockerException as e:
		app.logger.error(e.explanation)
		abort(500, message=e.explanation)
	finally:
		client.close()
	return ret


@app.route('/stats')
def stats():
	containers = [redis_c.hgetall(container) for container in redis_c.keys('cntr_*')]
    #return [marshal(c, container_fields) for c in containers]
	ret = "Number of accessed /ping path is {}".format(redis_c.get("n_visits"))
	app.logger.info(ret)

	#return [marshal(c, cntr_fields) for c in containers]
	#return jsonify(c for c in containers)
	return jsonify({"stats_map": stats_map}, {"cntr": containers})
	#for c in containers:
	#	return c

if __name__ == '__main__':
      app.run(host='0.0.0.0', port=5002)
