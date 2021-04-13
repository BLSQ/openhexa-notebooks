import os
from jupyterhub.auth import Authenticator
from jupyterhub.handlers import BaseHandler
import requests
from tornado import gen, web

c = get_config()

# General
c.Spawner.default_url = "/lab"
c.Spawner.args = ["--ResourceUseDisplay.track_cpu_percent=True"]

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

c.DockerSpawner.env_keep = ["APP_URL"]

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


# Authentication
# Our custom authenticator uses a login handler that forwards the cookies from the app component for
# cross-components authentication


class AppAuthenticatorLoginHandler(BaseHandler):
    """This login handler uses the cookies set by our app component. As the app and notebooks components run
    on the same domain, we can make a request to the app component using the cookies that it had set."""

    def get(self):
        try:
            response = requests.post(
                os.environ["APP_CREDENTIALS_URL"],
                data={"csrfmiddlewaretoken": self.cookies["csrftoken"].value},
                cookies={
                    "sessionid": self.cookies["sessionid"].value,
                    "csrftoken": self.cookies["csrftoken"].value,
                },
            )
        except requests.RequestException:
            raise web.HTTPError(401)

        if response.status_code == 200:
            response_data = response.json()
            user = self.user_from_username(response_data["username"])
            self.set_login_cookie(user)

            # Attach credentials to the user model - they will be used later to set env variables on the spawner
            user._credentials = {"env": response_data["env"]}
            next_url = self.get_next_url(user)
            self.redirect(next_url)

        raise web.HTTPError(401)


class AppAuthenticator(Authenticator):
    """This authenticator redefines the handlers to use our cookies-based login handler."""

    def pre_spawn_start(self, user, spawner):
        super().pre_spawn_start(user, spawner)
        # Update the spawner env variables with the credentials attached earlier (see AppAuthenticatorLoginHandler)
        if hasattr(user, "_credentials"):
            spawner.environment.update(user._credentials["env"])

    def get_handlers(self, app):
        return [
            (r"/login", AppAuthenticatorLoginHandler),
        ]

    @gen.coroutine
    def authenticate(self, *args):
        """This authenticator does not support "form" authentication."""

        raise NotImplementedError()


c.JupyterHub.authenticator_class = AppAuthenticator

# Use Postgres as the hub database
c.JupyterHub.db_url = os.environ["HUB_DB_URL"]

# shutdown the server after no activity for an hour
# c.NotebookApp.shutdown_no_activity_timeout = 60 * 60
# shutdown kernels after no activity for 20 minutes
# c.MappingKernelManager.cull_idle_timeout = 20 * 60
# check for idle kernels every two minutes
# c.MappingKernelManager.cull_interval = 2 * 60

# Allow hub to be embedded in an iframe
c.JupyterHub.tornado_settings = {
    "headers": {
        "Content-Security-Policy": f"frame-ancestors 'self' {os.environ['APP_URL']}"
    }
}
