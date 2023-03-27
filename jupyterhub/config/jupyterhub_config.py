import asyncio
import functools
import os

from jupyterhub.auth import Authenticator
from jupyterhub.handlers import BaseHandler, LogoutHandler
import requests
from jupyterhub.handlers.pages import SpawnHandler
from tornado import web
from urllib.parse import urlparse


# Custom authentication code to be mounted when running the hub (using hub.extraFiles in z2jh mode, or COPY / volumes
# with Docker if working locally). Could be moved to a module (Pypi / Github), but this would require maintaining
# our own z2jh hub image, as it is not possible to install additional libraries without doing so.
class AppAuthenticator(Authenticator):
    """This custom authenticator class uses the cookies set by the app component to authenticate, using a HTTP endpoint
    in the app component.

    In addition to authenticating the user, the app component also sends credentials (STS tokens
    for AWS S3 access for example). These credentials will be stored using Jupyterhub auth_state, and set as
    environment variables on the spawner.

    These credentials are only valid for a few hours. There is no way to update environment variables on a running
    single-user server, so to mitigate the issue, we will:

    - Make sure that fresh credentials are regenerated when spawning a single-user server
    - Force shutdowns of single-user servers when the user logs out, so that, for the overzealous user that works on
      the same server for 10+ hours without interruption, logging out can be used as an escape hatch to restart her
      server with newly-generated credentials

    """

    def get_handlers(self, app):
        return [
            (r"/login", AppAuthenticatorLoginHandler),
            (r"/logout", AppAuthenticatorLogoutHandler),
        ]

    async def _app_request(self, url, handler):
        loop = asyncio.get_running_loop()
        cookies = {
            "sessionid": handler.cookies["sessionid"].value,
            "csrftoken": handler.cookies["csrftoken"].value,
        }
        headers = {
            "X-CSRFToken": handler.cookies["csrftoken"].value,
            "Referer": f"{handler.request.protocol}://{handler.request.host}"
        }

        try:
            # We need to avoid blocking calls here, otherwise the whole Tornado loop is blocked and cannot process
            # other requests
            response = await loop.run_in_executor(
                None,
                functools.partial(
                    requests.post,
                    url,
                    cookies=cookies,
                    headers=headers
                ),
            )
        except requests.RequestException as e:
            self.log.error(f"Error when calling {url} ({e})")
            raise ValueError("Unexpected")

        if response.status_code != 200:
            self.log.error(
                f"Non-200 response when calling {url} ({response.status_code})"
            )
            raise ValueError("Unexpected")

        return response.json()

    async def authenticate(self, handler, data):
        """Authenticate with the app component using the app cookies. We won't need to use the data argument, as
        the cookies are accessible on the handler itself."""

        try:
            authentication_data = await self._app_request(os.environ["AUTHENTICATION_URL"], handler)
        except ValueError as e:
            self.log.warning(f"Error when authenticating ({e})")
            return None

        return {
            "name": authentication_data["username"],
        }

    async def pre_spawn_start(self, user, spawner):
        """Before spawning a single-user server, we need to read the auth state (where user credentials are stored)
        and set these credentials as environment variables on the spawner. This auth state is created during
        authenticate() calls."""

        if spawner.name == "":  # Default credentials, OpenHexa legacy (outside workspaces)
            legacy_mode = True
            credentials_data = await self._app_request(os.environ["DEFAULT_CREDENTIALS_URL"], spawner.handler)
        else:  # Workspace mode
            legacy_mode = False
            credentials_url = os.environ["WORKSPACE_CREDENTIALS_URL"].replace("<workspace_slug>", spawner.name)
            credentials_data = await self._app_request(credentials_url, spawner.handler)

            # Let's use the hash generated on the app side
            spawner.pod_name = f"jupyter-{credentials_data['notebooks_server_hash']}"

            # Disable persistent storage in workspaces
            if len(spawner.volumes) > 0 and spawner.volumes[0]["name"].startswith("volume-"):
                spawner.volumes = spawner.volumes[1:]
                spawner.volume_mounts = spawner.volume_mounts[1:]
                spawner.storage_pvc_ensure = False
                spawner.pvc_name = None

        spawner.environment.update({
            **credentials_data["env"],
            "OPENHEXA_LEGACY": "true" if legacy_mode else "false"
        })


class AppAuthenticatorLoginHandler(BaseHandler):
    """This login handler directly triggers a login operation, that will use AppAuthenticator.authenticate()."""

    async def get(self):
        user = await self.login_user({})

        if user is None:
            raise web.HTTPError(401, "Your user could not be authenticated")

        return self.redirect(self.get_next_url(user))


class AppAuthenticatorLogoutHandler(LogoutHandler):
    # To logout the user from openhexa also on jupyterhub, the logout
    # from openhexa will send us here, after jupyterhub logout the
    # the user, this endpoint will redirect to the login page of openhexa
    # TODO: use API https://github.com/jupyterhub/jupyterhub/issues/3688)
    async def render_logout_page(self):
        redirect_url = os.environ["LOGOUT_REDIRECT_URL"]
        return self.redirect(redirect_url, permanent=False)


# Authentication configuration
c.JupyterHub.authenticator_class = AppAuthenticator
# We use auth state to store user credentials
c.Authenticator.enable_auth_state = True  # TODO: we might want to remove this
# See AppAuthenticator.pre_spawn_start() and AppAuthenticator.post_spawn_stop() for details
c.Authenticator.refresh_pre_spawn = True  # TODO: might not be necessary, check
# Will shutdown single-user servers on logout, which can be useful in our case to regenerate fresh credentials
# (As our login is automatic, logging out will trigger an immediate login, so logging out results in
# restarting a single-user server with fresh credentials)
c.JupyterHub.shutdown_on_logout = True

# Use Jupyterlab by default
c.Spawner.default_url = "/lab"

# Allow hub to be embedded in an iframe
c.JupyterHub.tornado_settings.update({
    "headers": {"Content-Security-Policy": os.environ["CONTENT_SECURITY_POLICY"]}
})

# Named servers
c.JupyterHub.allow_named_servers = True

# Services
c.JupyterHub.services.append(
    {
        # give the token a name
        "name": "service-api",
        "api_token": os.environ["HUB_API_TOKEN"],
    },
)
c.JupyterHub.load_roles.append(
    {
        "name": "api-role",
        "scopes": [
            "admin:users",
            "admin:servers"
        ],
        "services": [
            "service-api",
        ],
    }
)
