"""OAuth2 provider patched here.

The provider that comes with flask_oauthlib enables OpenID Connect, but we
don't want to support that in this application.
"""
from flask_oauthlib.provider import OAuth2Provider


class PatchedOAuth2Provider(OAuth2Provider):
    """Patched version of the OAuth2Provider class."""
    @property
    def server(self):
        """The default implementation returns a Server endpoint (oauthlib)
        whose handler for the `code` response type delegates to either the
        "vanilla" authorization code workflow or the OIDC workflow, depending
        on the scopes present in the request. This function modifies the
        returned Server to use only the "vanilla" grant workflow instead.
        """
        server = super().server

        # the handler for the `none` response type does not attempt OIDC
        auth_grant = server.response_types['none']
        server.response_types['code'] = auth_grant

        return server
