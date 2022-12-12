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

    async def authenticate(self, handler, data):
        """Authenticate with the app component using the app cookies. We won't need to use the data argument, as
        the cookies are accessible on the handler itself."""

        loop = asyncio.get_running_loop()
        app_credentials_url = os.environ["APP_CREDENTIALS_URL"]
        cookies = {
            "sessionid": handler.cookies["sessionid"].value,
            # "csrftoken": handler.cookies["csrftoken"].value,
        }

        try:
            # We need to avoid blocking calls here, otherwise the whole Tornado loop is blocked and cannot process
            # other requests
            response = await loop.run_in_executor(
                None,
                functools.partial(
                    requests.post,
                    app_credentials_url,
                    cookies=cookies,
                ),
            )
        except requests.RequestException as e:
            self.log.warning(f"Error when calling {app_credentials_url} ({e})")
            return None

        if response.status_code != 200:
            self.log.warning(
                f"Non-200 response when calling {app_credentials_url} ({response.status_code})"
            )
            return None

        response_data = response.json()

        # We use auth_state to store the credentials set by the app component - they will be read by the
        # pre_spawn_start() hook and set as environment variables on the spawner.
        return {
            "name": response_data["username"],
            "auth_state": {
                "env": response_data["env"],
            }
            # TODO: handle admin in app
            # "admin": response_data["admin"]
        }

    async def refresh_user(self, user, handler=None):
        """refresh_user is called in two different circumstances:

           1. When auth_refresh_age is reached
           2. When spawning a new single-user server (if refresh_pre_spawn is set to True, which is the case here)

        We don't really care about 1. at this stage, although it would be a good occasion to revoke (Jupyterhub) user
        access for users that have been blocked / deactivated in the app component. For now, street-smart users that
        have no access to the app component, and happen to know the URL of the notebooks component, can still enjoy
        some kind of Jupyterhub access for a few hours. Manually deleting the user in the Jupyterhub admin will do
        the trick until we implement a proper revoke system.

        We do care about 2. though - we have set refresh_pre_spawn to True, which means that every time a new
        single-user server is started, refresh_user() will be called. If the handler is a SpawnHandler
        (i.e we are not in a "auth_refresh_age" situation), we re-authenticate the user, to make sure that they
        have fresh credentials.
        """

        # No auth state -> re-authenticate
        if isinstance(handler, SpawnHandler):
            self.log.info(f"Regenerating fresh credentials for user {user.name}")

            return await self.authenticate(handler, {})

        return True

    async def pre_spawn_start(self, user, spawner):
        """Before spawning a single-user server, we need to read the auth state (where user credentials are stored)
        and set these credentials as environment variables on the spawner. This auth state is created during
        authenticate() calls."""

        auth_state = await user.get_auth_state()

        if auth_state is not None:
            spawner.environment.update(auth_state["env"])
        else:
            self.log.error(
                f"No auth state for user {user.name}",
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
    async def render_logout_page(self):
        redirect_url = os.environ["LOGOUT_REDIRECT_URL"]
        return self.redirect(redirect_url, permanent=False)


# Authentication configuration
c.JupyterHub.authenticator_class = AppAuthenticator
# We use auth state to store user credentials
c.Authenticator.enable_auth_state = True
# See AppAuthenticator.pre_spawn_start() and AppAuthenticator.post_spawn_stop() for details
c.Authenticator.refresh_pre_spawn = True
# Will shutdown single-user servers on logout, which can be useful in our case to regenerate fresh credentials
# (As our login is automatic, logging out will trigger an immediate login, so logging out results in
# restarting a single-user server with fresh credentials)
c.JupyterHub.shutdown_on_logout = True

# Use Jupyterlab by default
c.Spawner.default_url = "/lab"

# Allow hub to be embedded in an iframe
c.JupyterHub.tornado_settings = {
    "headers": {"Content-Security-Policy": os.environ["CONTENT_SECURITY_POLICY"]}
}
