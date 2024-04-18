import asyncio
import functools
import os

import requests
from jupyterhub.auth import Authenticator
from jupyterhub.handlers import BaseHandler, LogoutHandler
from jupyterhub.utils import new_token
from tornado import web


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

    async def _app_request(self, url, handler, **extra):
        loop = asyncio.get_running_loop()
        try:
            cookies = {
                "sessionid": handler.cookies["sessionid"].value,
                "csrftoken": handler.cookies["csrftoken"].value,
            }
        except KeyError:
            self.log.warning("Missing cookies")
            raise ValueError("Unexpected")

        headers = {
            "X-CSRFToken": handler.cookies["csrftoken"].value,
            "Referer": f"{handler.request.protocol}://{handler.request.host}",
        }

        try:
            # We need to avoid blocking calls here, otherwise the whole Tornado loop is blocked and cannot process
            # other requests
            response = await loop.run_in_executor(
                None,
                functools.partial(
                    requests.post, url, cookies=cookies, headers=headers, **extra
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
            authentication_data = await self._app_request(
                os.environ["AUTHENTICATION_URL"], handler
            )
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
        if (
            spawner.name == ""
        ):  # Default credentials, OpenHEXA legacy (outside workspaces)
            credentials_data = await self._app_request(
                os.environ["DEFAULT_CREDENTIALS_URL"], spawner.handler
            )
        else:  # Workspace mode
            credentials_data = await self._app_request(
                os.environ["WORKSPACE_CREDENTIALS_URL"],
                spawner.handler,
                data={"workspace": spawner.name},
            )

            # Let's use the hash generated on the app side
            spawner.pod_name = f"jupyter-{credentials_data['notebooks_server_hash']}"

            # SET DOCKER IMAGE
            if credentials_data.get("image") is not None:
                self.log.info(f"Using custom image: {credentials_data['image']}")
                spawner.image = credentials_data["image"]

            # Disable persistent storage in workspaces
            if len(spawner.volumes) > 0 and spawner.volumes[0]["name"].startswith(
                "volume-"
            ):
                spawner.volumes = spawner.volumes[1:]
                spawner.volume_mounts = spawner.volume_mounts[1:]
                spawner.storage_pvc_ensure = False
                spawner.pvc_name = None

        # Double the brackets to avoid the KubeSpawner to interpret them as placeholders (cfr https://github.com/jupyterhub/kubespawner/pull/642)
        if c.JupyterHub.spawner_class == "dockerspawner.DockerSpawner":
            extra_env = credentials_data["env"]
        else:
            extra_env = {
                key: value.replace("{", "{{").replace("}", "}}")
                for key, value in credentials_data["env"].items()
            }
        spawner.environment.update(
            {
                **extra_env,
                "HEXA_SERVER_URL": os.environ["HEXA_SERVER_URL"],
                "HEXA_WORKSPACE": spawner.name,
            }
        )


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

    async def get(self):
        # Authenticate the user using the sessionid and csrftoken in the cookies
        authenticated = await self.authenticate({})
        user = None
        if authenticated:
            user = self.find_user(authenticated["name"])
        # We override the _jupyterhub_user attribute to make sure that the logout operation will be performed
        self._jupyterhub_user = user

        # Call the default handler that will shut down servers if set in config
        response = await super().get()

        # If we had a user, we set a new cookie_id to force a new login
        # We have to do this because the default behavior of JupyterHub is to
        # clear the session cookie on the client side but not updates the
        # cookie_id in the database
        # Since we call this endpoint from openhexa-app, we cannot clear the cookie
        # on the client side (they are on different domains)
        if user:
            self.log.info(f"Logging out user {user}")
            user.cookie_id = new_token()
            self.db.add(user)
            self.db.commit()
            self.log.info(f"User {user.name} logged out")

        return response

    async def render_logout_page(self):
        redirect_url = os.environ["LOGOUT_REDIRECT_URL"]
        return self.redirect(redirect_url, permanent=False)


# Authentication configuration
c.JupyterHub.authenticator_class = AppAuthenticator
# We use auth state to store user credentials
c.Authenticator.enable_auth_state = True  # TODO: we might want to remove this
# See AppAuthenticator.pre_spawn_start() and AppAuthenticator.post_spawn_stop() for details
c.Authenticator.refresh_pre_spawn = True  # TODO: might not be necessary, check
# Will shut down single-user servers on logout, which can be useful in our case to regenerate fresh credentials
# (As our login is automatic, logging out will trigger an immediate login, so logging out results in
# restarting a single-user server with fresh credentials)
c.JupyterHub.shutdown_on_logout = True

# Use Jupyterlab by default
c.Spawner.default_url = "/lab"

# Allow hub to be embedded in an iframe
c.JupyterHub.tornado_settings.update(
    {"headers": {"Content-Security-Policy": os.environ["CONTENT_SECURITY_POLICY"]}}
)

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
        "scopes": ["admin:users", "admin:servers"],
        "services": [
            "service-api",
        ],
    }
)

# Set additional labels on pods (useful for monitoring & billing)
c.KubeSpawner.extra_labels = {"hexa-workspace": "{servername}"}
