#!/usr/bin/env python3

"""Handling REST request on the server, looks for available nodes, indentifies if clients has
available ports, verifies if image is on remote server and if required downloads it,
starts container, forward request, receive response and stop remote container. Response is returned back to client"""

import socket
from time import sleep
from contextlib import closing
import requests
import docker
from flask_restful import abort
import redis
from flask import request, jsonify
from server import createApp

app = createApp()

"""Container statuses"""
RUNNING = "running"
STOPPED = "stopped"
REMOVED = "removed"

#Add commands and state of the container

#Default connection to redis"""
redis_c = redis.from_url(app.config.get("DEF_REDIS_URL"), charset="utf-8", decode_responses=True)

"""Dictionary for storing stats data"""
stats_map = {"n_visits": redis_c.get("n_visits"),
             "n_cntr_provisioned": redis_c.get("n_cntr_provisioned"),
             "n_cntr_accessed": redis_c.get("n_cntr_accessed"),
            }

def _redis_put_container_data(cnt, server, port):

    cntr = {"cntr_id": cnt.id,
            "name": cnt.name,
            "status": cnt.status,
            "accessed": 0,
            "port": port,
            "node": server}
    redis_c.hmset("cntr_%s" % cnt.short_id, cntr)
    stats_map["n_cntr_provisioned"] = redis_c.incr('n_cntr_provisioned')


"""Returns if port is available"""
def _is_port_available(host, port):
    app.logger.info("Verifying if port {} is available on {} node".format(port, host))
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as sock:
        if sock.connect_ex((host, port)) == 0:
            app.logger.debug("Port {} is used".format(port))
            return False
        else:
            app.logger.debug("Port {} is not used".format(port))
            return True

"""Looks through available ports starting from 5001 + replica number defined in configuration"""
def _get_port_number(host, init_port=5001):
    for number in range(int(app.config.get("DEF_REPLICA_NUMBER"))):
        n_port = init_port + number
        bln = _is_port_available(host, n_port)
        if bln:
            return n_port
    return None

"""Looking through defined node list in configuration and returns the first one able connect to"""
def _get_available_client():
    app.logger.info("Verify if host available and connection can be specified")
    client = None
    port = None
    srv = "127.0.0.1"
    for srv in app.config.get("L_SERVER").split(","):
        app.logger.info("Connecting to {} node".format(srv))
        try:
            client = docker.DockerClient(base_url=('{}://{}:{}').format(
                app.config.get("DEF_PROTOCOL"), srv, app.config.get("DOCKER_PORT")))
            app.logger.debug("Asking for ping")
            client.ping()
            app.logger.info("Connected to docker instance on {} node".format(srv))
            port = _get_port_number(srv)
            if port is None:
                app.logger.info("{} node doesn't have any available ports".format(srv))
                continue
            break
        except requests.exceptions.RequestException as e:
            app.logger.error("{} node or connection to it is not available".format(srv))
            return(client, srv, port)
    return (client, srv, port)

"""Check if container is already running on the remote side"""
def _verify_container_running(client):
    app.logger.info("Verify if container is running")
    try:
        for cnt in client.containers.list():
            if app.config.get("DEF_CONTAINER_NAME") == cnt.name:
                app.logger.info("{} container is running".format(app.config.get("DEF_CONTAINER_NAME")))
                return cnt
        app.logger.info("{} container is not running".format(app.config.get("DEF_CONTAINER_NAME")))
        return None
    except docker.errors.DockerException as e:
        app.logger.error(str(e))
        abort(500, message=str(e))


"""Verify if image is available on function node and if it's not then pulls it from repository"""
def _verify_image_exists(client, server):
    for i in client.images.list():
        app.logger.info(i)
        for tag in i.tags:
            app.logger.info(tag)
            if app.config.get("DEF_IMAGE_NAME") in tag:
                app.logger.info(("{} image exists on the {} node").format(
                    app.config.get("DEF_IMAGE_NAME"), server))
                return i
    app.logger.info(("{} image is not yet build or pulled on the {} node").format(
        app.config.get("DEF_IMAGE_NAME"), server))
    app.logger.info("Pulling {} image".format(app.config.get("FULL_IMAGE_NAME")))
    try:
        image = client.images.pull(app.config.get("FULL_IMAGE_NAME"))
        return image
    except docker.errors.DockerException as e:
        app.logger.error(str(e))
        abort(500, message=str(e))

"""Start container and return reference to it"""
def _get_container(client, server, port):
    i = _verify_image_exists(client, server)
    if i is None:
        return None
    app.logger.info("Starting container from {} image".format(app.config.get("FULL_IMAGE_NAME")))
    try:
        cnt = client.containers.run(app.config.get("FULL_IMAGE_NAME"),
                                name=app.config.get("DEF_CONTAINER_NAME") + str(port), detach=True,
                            ports={app.config.get("DEF_CONTAINER_PORT"):port})
    except docker.errors.DockerException as e:
        app.logger.error(str(e))
        abort(500, message=str(e))

    """Nice to have for starting container"""
    sleep(2)

    _redis_put_container_data(cnt, server, port)
    return cnt


"""Simple route for verifying availability"""
@app.route('/')
def main() -> str:
    return 'This is reply from main page'

"""Handles request to available and remotely runninng preconfigured node"""
@app.route('/ping')
def ping() -> str:
    stats_map["n_visits"] = redis_c.incr('n_visits')
    ret = "Empty return"
    cntr = None
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
            cntr = _get_container(client, ip_node, port)
        if cntr is not None:
            url = "http://{}:{}{}".format(ip_node, port, request.path)
            app.logger.debug(request.path)
            app.logger.debug(url)
            session = requests.Session()
            req = requests.Request(request.method, url, data=request.data,
                                   headers=request.headers)
            prepped = req.prepare()
            resp = session.send(prepped)
            stats_map["n_cntr_accessed"] = redis_c.incr('n_cntr_accessed')
            redis_c.hmset("cntr_%s" % cntr.short_id, {"status": RUNNING, "accessed": 1})
            ret = resp.text
            app.logger.info("Response is received")
            app.logger.info("Stopping container")
            cntr.stop()
            redis_c.hmset("cntr_%s" % cntr.short_id, {"status": STOPPED})
            app.logger.info("Removing container")
            cntr.remove()
            redis_c.hmset("cntr_%s" % cntr.short_id, {"status": REMOVED})
    except docker.errors.DockerException as e:
        app.logger.error(str(e))
        abort(500, message=str(e))
    finally:
        if client is not None:
            client.close()
    return ret

"""Return recorded statistics in json format"""
@app.route('/stats')
def stats():
    containers = [redis_c.hgetall(container) for container in redis_c.keys('cntr_*')]
    ret = "Number of accessed /ping path is {}".format(redis_c.get("n_visits"))
    app.logger.info(ret)
    return jsonify({"stats_map": stats_map}, {"cntr": containers})


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002)
