import logging
import re
import threading
from enum import Enum
from typing import List, Optional

from flask import Flask
from pydantic import (
    AnyHttpUrl,
    AnyUrl,
    BaseModel,
    ConstrainedStr,
    Field,
    root_validator,
)
from werkzeug.serving import make_server

logging.getLogger()


class ClientId(ConstrainedStr):
    regex = re.compile(r"^[a-f0-9]{32}$")


class ClientSecret(ClientId):
    pass


class HttpsUrl(AnyUrl):
    allowed_schemes = {"https"}


class GrantType(Enum):
    CODE = "Code"
    PKCE = "PKCE"


class OpenAPIAppConfig(BaseModel):
    """Dataclass for parsing and validating app config object from Saxo Developer Portal."""

    app_name: str = Field(..., alias="AppName")
    grant_type: GrantType = Field(..., alias="GrantType")
    client_id: ClientId = Field(..., alias="AppKey")
    client_secret: ClientSecret = Field(None, alias="AppSecret")
    auth_endpoint: HttpsUrl = Field(..., alias="AuthorizationEndpoint")
    token_endpoint: HttpsUrl = Field(..., alias="TokenEndpoint")
    api_base_url: HttpsUrl = Field(..., alias="OpenApiBaseUrl")
    redirect_urls: List[AnyHttpUrl] = Field(..., alias="RedirectUrls")

    @root_validator(pre=True)
    def client_secret_required_for_grant_type_code(cls, values: dict) -> dict:
        if values.get("grant_type") is GrantType.CODE:
            assert values.get(
                "client_secret"
            ), "client_secret required for Code grant type"
        if values.get("grant_type") is GrantType.PKCE:
            assert (
                values.get("client_secret") is None
            ), "client_secret must be None for PKCE grant type"
        return values


class AuthTokenData(BaseModel):
    access_token: str
    token_type: str
    expires_in: int
    refresh_token: str
    refresh_token_expires_in: int
    base_uri: Optional[str] = None


class RedirectServer(threading.Thread):
    """
    This Flask server runs inside a thread, and will be terminated when the callback is received.
    """

    def __init__(self, app: Flask, redirect_url: AnyHttpUrl):
        threading.Thread.__init__(self, daemon=True)
        host = redirect_url.host
        port = redirect_url.port
        self.server = make_server(host, port, app)  # type: ignore[arg-type]
        self.ctx = app.app_context()
        self.ctx.push()

    def run(self) -> None:
        logging.debug("starting server and listening for callback from Saxo...")
        self.server.serve_forever()

    def shutdown(self) -> None:
        logging.debug("terminating server...")
        self.server.shutdown()


app_config = {
    "AppName": "SIM Automated Test Suite - pkce flow",
    "AppKey": "fb5a4e5cca484043a7c3fed5c7329c2d",
    "AuthorizationEndpoint": "https://sim.logonvalidation.net/authorize",
    "TokenEndpoint": "https://sim.logonvalidation.net/token",
    "GrantType": "PKCE",
    "OpenApiBaseUrl": "https://gateway.saxobank.com/sim/openapi/",
    "RedirectUrls": ["http://localhost/redirect"],
}
