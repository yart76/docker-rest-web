
import os

class BaseConfig(object):
    """Base configuration."""
    L_SERVER = os.getenv("L_SERVER", "192.168.33.60,192.168.33.70")
    DEF_PROTOCOL = os.getenv("DEF_PROTOCOL", "tcp")
    DOCKER_PORT = os.getenv("DOCKER_PORT", 2375)
    DEF_IMAGE_NAME = os.getenv("DEF_IMAGE_NAME", "python-ping")
    DEF_REG_NAME = os.getenv("DEF_REG_NAME", "docker.io")
    DEF_REP_NAME = os.getenv("DEF_REP_NAME", "jartamon")
    DEF_IMAGE_VERSION = os.getenv("DEF_IMAGE_VERSION", "latest")
    DEF_CONTAINER_NAME = os.getenv("DEF_CONTAINER_NAME", "ping")
    DEF_CONTAINER_PORT = os.getenv("DEF_CONTAINER_PORT", 5001)

    # Default number of replicas that can be run on each node defined in L_SERVER variable
    DEF_REPLICA_NUMBER = os.getenv("DEF_REPLICA_NUMBER", 2)
    DEF_PATH = os.getenv("DEF_PATH", "ping")
    IMAGE_NAME = "{}/{}:{}".format(DEF_REP_NAME, DEF_IMAGE_NAME, DEF_IMAGE_VERSION)
    FULL_IMAGE_NAME = "{}/{}".format(DEF_REG_NAME, IMAGE_NAME)

    DEF_REDIS_URL = os.getenv("DEF_REDIS_URL", "redis://web-redis:6379/0")

