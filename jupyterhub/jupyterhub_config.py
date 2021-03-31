import os
from jupyterhub.auth import DummyAuthenticator

c = get_config()

# General
c.Spawner.default_url = "/lab"
c.Spawner.args = [
    "--ResourceUseDisplay.track_cpu_percent=True"
]

# Docker Spawner (see https://github.com/jupyterhub/dockerspawner)
c.JupyterHub.spawner_class = "dockerspawner.DockerSpawner"
c.DockerSpawner.image = os.environ["JUPYTER_IMAGE"]
c.DockerSpawner.debug = True

# This is really useful to avoid "dangling containers" that cannot connect to the Hub anymore
# (and the dreaded The "'ip' trait of a Server instance must be a unicode string, but a value of None
# <class 'NoneType'> was specified" error - see https://github.com/jupyterhub/jupyterhub/issues/2213 and
# https://github.com/defeo/jupyterhub-docker/issues/5)
c.DockerSpawner.remove = True
c.DockerSpawner.network_name = os.environ["DOCKER_NETWORK_NAME"]

# c.DockerSpawner.env_keep = ["FOO", "BAR"]

# Volume mounts & environment variables
# c.DockerSpawner.volumes = {
#     f"{os.environ['PROJECT_PATH']}/some-dir": "/some-dir"
# }
# c.DockerSpawner.environment = {
#     "FOO": "BAR"
# }

c.JupyterHub.hub_ip = "0.0.0.0"  # listen on all interfaces
c.JupyterHub.hub_connect_ip = os.environ[
    "HUB_IP"
]  # ip as seen on the docker network. Can also be a hostname.

# TODO: custom auth
c.JupyterHub.authenticator_class = DummyAuthenticator
c.DummyAuthenticator.password = "openhexa"

# Use Postgres as the hub database
c.JupyterHub.db_url = os.environ["HUB_DB_URL"]

# shutdown the server after no activity for an hour
#c.NotebookApp.shutdown_no_activity_timeout = 60 * 60
# shutdown kernels after no activity for 20 minutes
# c.MappingKernelManager.cull_idle_timeout = 20 * 60
# check for idle kernels every two minutes
# c.MappingKernelManager.cull_interval = 2 * 60

# Allow hub to be embedded in an iframe
c.JupyterHub.tornado_settings = {'headers': {'Content-Security-Policy': "frame-ancestors 'self' http://localhost:8000"}}
