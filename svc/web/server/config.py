
import os

class BaseConfig(object):
    """Base configuration."""
    L_SERVER = os.getenv("L_SERVER", "192.168.33.80,192.168.33.60")
    DEF_PROTOCOL = os.getenv("DEF_PROTOCOL", "tcp")
    DOCKER_PORT = os.getenv("DOCKER_PORT", 2375)
    DEF_IMAGE_NAME = os.getenv("DEF_IMAGE_NAME", "python-ping")
    DEF_IMAGE_VERSION = os.getenv("DEF_IMAGE_VERSION", "latest")
    DEF_CONTAINER_NAME = os.getenv("DEF_CONTAINER_NAME", "ping")
    DEF_CONTAINER_PORT = os.getenv("DEF_CONTAINER_PORT", "5001")
    DEF_PATH = os.getenv("DEF_PATH", "ping")
    IMAGE_NAME = "{}:{}".format(DEF_IMAGE_NAME, DEF_IMAGE_VERSION)

