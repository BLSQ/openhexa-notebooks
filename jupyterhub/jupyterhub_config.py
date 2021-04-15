import os
from jupyterhub.auth import Authenticator
from jupyterhub.handlers import BaseHandler
import requests
from tornado import gen, web


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
                cookies={
                    "sessionid": self.cookies["sessionid"].value,
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
