# This config file is meant be for local, docker-compose development. It loads the main config file
# (jupyterhub_config.py) before applying local-only configuration

import os
from pathlib import Path

from dockerspawner import DockerSpawner

# Load main config file
main_config_file_path = Path(__file__).parent / Path("jupyterhub_config.py")
load_subconfig(str(main_config_file_path.resolve()))

# Configure the hub ip
# (unnecessary in z2jh mode)
# listen on all interfaces
c.JupyterHub.hub_ip = "0.0.0.0"
# ip as seen on the docker network. Can also be a hostname.
c.JupyterHub.hub_connect_ip = os.environ["HUB_IP"]

# Docker Spawner configuration (see https://github.com/jupyterhub/dockerspawner)
# (In z2jh mode, Kubespawner is used instead)

c.JupyterHub.spawner_class = "dockerspawner.DockerSpawner"
if os.environ.get('PROXY_HOSTNAME_AND_PORT') is not None:
    scheme = 'https' if os.environ.get(
        'TRUST_FORWARDED_PROTO') == 'true' else 'http'
    url = os.environ.get('PROXY_HOSTNAME_AND_PORT')
    origin = f'{scheme}://{url}'
    c.DockerSpawner.args = [f'--NotebookApp.allow_origin={origin}']
    c.JupyterHub.tornado_settings = {
        'headers': {
            'Access-Control-Allow-Origin': origin,
        },
    }
c.DockerSpawner.image = os.environ["JUPYTER_IMAGE"]
c.DockerSpawner.allowed_images = (
    "*"  # To allow all images to be used via user_options (needed for workspaces)
)
c.Spawner.debug = True  # Seems necessary to see spawner logs / to check
c.Spawner.cmd = "singleuser"
c.DockerSpawner.debug = True
c.DockerSpawner.extra_host_config = {
    "privileged": True,
    "devices": "/dev/fuse"
}
c.DockerSpawner.post_start_cmd = 'sh -c "python3 /home/jovyan/.hexa_scripts/fuse_mount.py && python3 /home/jovyan/.hexa_scripts/wrap_up.py"'

# This is really useful to avoid "dangling containers" that cannot connect to the Hub anymore
# (and the dreaded The "'ip' trait of a Server instance must be a unicode string, but a value of None
# <class 'NoneType'> was specified" error - see https://github.com/jupyterhub/jupyterhub/issues/2213 and
# https://github.com/defeo/jupyterhub-docker/issues/5)
c.DockerSpawner.remove = True
c.DockerSpawner.network_name = os.environ["DOCKER_NETWORK_NAME"]

# We want the spawner to keep this environment variable so that it is forwarded to single-user servers
# (In z2jh mode, CONTENT_SECURITY_POLICY is set explicitly)
c.DockerSpawner.env_keep = ["CONTENT_SECURITY_POLICY"]

#  DB configuration
# (In z2jh mode, configured through hub.db)
c.JupyterHub.db_url = os.environ["HUB_DB_URL"]
