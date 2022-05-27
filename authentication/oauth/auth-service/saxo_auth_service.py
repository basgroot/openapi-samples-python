import base64
import hashlib
import json
import logging
import os
import secrets
import webbrowser
from random import randint
from time import sleep
from typing import List
from urllib.parse import urlencode

import requests
from pydantic import AnyHttpUrl, parse_obj_as

from models import AuthTokenData, GrantType, HttpsUrl, OpenAPIAppConfig, RedirectServer

# reduce log level to remove debug messages from console output
logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(message)s", level=logging.DEBUG
)
logging.getLogger()


class SaxoAuthService:
    _token_data: AuthTokenData | None = None

    _auth_redirect_url: AnyHttpUrl | None = None
    _auth_received_callback: bool | None = None
    _auth_code: str | None = None
    _auth_received_state: str | None = None
    _auth_error_message: str | None = None
    _auth_code_verifier: bytes | None = None

    def __init__(self, app_config: OpenAPIAppConfig | None = None):
        """Create a new AuthService object with provided AppConfig.

        When initialized, config is loaded either directly from app_config argument or from "app_config.json".
        """

        if app_config:
            logging.debug("using config directly passed from app_config argument")
            self._app_config = app_config
        else:
            if os.path.isfile("app_config.json"):
                logging.debug("found config file 'app_config.json'")
                with open("app_config.json", "r") as config_file:
                    config_data = json.load(config_file)
                    self._app_config = parse_app_config(config_data)
            else:
                raise RuntimeError(
                    "no app config object found - make sure 'app_config.json' is available in this directory or load the config directly when initializing SaxoAuthService"
                )

    @property
    def logged_in(self) -> bool:
        if self._token_data:
            return True
        else:
            return False
        # if token expired...

    @property
    def available_redirect_urls(self) -> List[AnyHttpUrl]:
        return self._app_config.redirect_urls

    @property
    def grant_type(self) -> GrantType:
        return self._app_config.grant_type

    @property
    def api_base_url(self) -> HttpsUrl:
        return self._app_config.api_base_url

    @property
    def access_token(self) -> str:
        if not self.logged_in:
            raise ValueError(
                "you are not logged in currently - use login() to create a new session"
            )
        return self._token_data.access_token  # type: ignore[union-attr]

    def login(self, redirect_url: AnyHttpUrl = None, redirect_port: int = None) -> None:
        """Create a new API session by authenticating with Saxo SSO."""

        logging.debug(
            f"logging in to app: '{self._app_config.app_name}' using {self._app_config.grant_type}"
        )

        # defaults to first redirect url in config if not provided explicitly
        if self.grant_type is GrantType.CODE:
            if not redirect_url:
                self._auth_redirect_url = self._app_config.redirect_urls[0]
            elif not redirect_url in self._app_config.redirect_urls:
                raise ValueError(
                    "provided redirect url not valid for app config and won't be accepted by Saxo SSO"
                )
            else:
                self._auth_redirect_url = redirect_url

        if self.grant_type is GrantType.PKCE:
            if not redirect_url and not redirect_port:
                _redirect_port = randint(
                    1000, 9999
                )  # any of these ports are usually free
                _redirect_url = self._app_config.redirect_urls[0]
                self._auth_redirect_url = parse_obj_as(
                    AnyHttpUrl,
                    f"{_redirect_url.scheme}://{_redirect_url.host}:{_redirect_port}{_redirect_url.path}",  # type: ignore[union-attr]
                )
            else:
                self._auth_redirect_url = parse_obj_as(
                    AnyHttpUrl,
                    f"{redirect_url.scheme}://{redirect_url.host}:{redirect_port}{redirect_url.path}",  # type: ignore[union-attr]
                )  # type: ignore[union-attr]

        logging.debug(
            f"redirect url for callback: {self._auth_redirect_url.format()}"  # type: ignore[union-attr]
        )

        state = secrets.token_urlsafe(10)

        # these query params are always the same for Code and PKCE flows
        auth_request_query_params = {
            "response_type": "code",  # always 'code'
            "client_id": self._app_config.client_id,
            "state": state,
            "redirect_uri": self._auth_redirect_url,
        }

        if self.grant_type is GrantType.PKCE:
            verifier = base64.urlsafe_b64encode(secrets.token_bytes(64)).rstrip(b"=")
            digest = hashlib.sha256(verifier).digest()
            challenge = base64.urlsafe_b64encode(digest).rstrip(b"=")
            self._auth_code_verifier = verifier

            auth_request_query_params.update(
                {
                    "code_challenge": challenge,  # type: ignore[dict-item]
                    "code_challenge_method": "S256",
                }
            )

        if self.grant_type is GrantType.CODE:
            auth_request_query_params.update(
                {"client_secret": self._app_config.client_secret}
            )

        auth_url = (
            self._app_config.auth_endpoint + "?" + urlencode(auth_request_query_params)
        )
        logging.debug(f"browser will be opened with url: {auth_url=}")
        webbrowser.open_new(auth_url)  # type: ignore[arg-type]
        server = self._create_redirect_server(self._auth_redirect_url)  # type: ignore[arg-type]
        server.start()

        while not self._auth_received_callback:
            try:
                sleep(1)
            except KeyboardInterrupt:
                logging.warning("keyboard interrupt received - shutting down...")
                exit(-1)

        server.shutdown()

        if self._auth_error_message:
            raise RuntimeError(
                f"error occured during authentication: {self._auth_error_message}"
            )

        if state != self._auth_received_state:
            raise RuntimeError("received state does not match original state")

        logging.debug("authentication successful!")

        self.exercise_authorization(auth_code=self._auth_code)

    def _create_redirect_server(self, redirect_url: AnyHttpUrl) -> RedirectServer:
        from flask import Flask, request

        app = Flask(__name__)

        @app.route(redirect_url.path)  # type: ignore[arg-type]
        def handle_callback() -> str:
            """
            Saxo SSO will redirect to this endpoint after the user authenticates.
            """

            logging.debug("received callback")
            self._auth_received_callback = False
            self._auth_code = None
            self._auth_received_state = None
            self._auth_error_message = None

            if "error" in request.args:
                self._auth_error_message = (
                    request.args["error"] + ": " + request.args["error_description"]
                )
                render_text = (
                    "Error occurred. Please check the application command line."
                )
            else:
                self._auth_code = request.args["code"]
                render_text = (
                    "Authentication succeeded! Please go back to the application."
                )

            self._auth_received_state = request.args["state"]
            self._auth_received_callback = True

            return render_text

        return RedirectServer(app, redirect_url)

    def logout(self) -> None:
        self._token_data = None
        self._auth_redirect_url = None
        self._auth_received_callback = None
        self._auth_code = None
        self._auth_received_state = None
        self._auth_error_message = None

        logging.debug("logout completed")

    def refresh(self) -> None:
        if not self.logged_in:
            raise ValueError(
                "you are not logged in currently - use login() to create a new session"
            )
        self.exercise_authorization()

    def exercise_authorization(self, auth_code: str = None) -> None:
        """Exercizes the provided auth_code, defaults to using the refresh token."""

        token_request_params = {}

        # auth_code is exercized
        if auth_code:
            token_request_params.update(
                {
                    "grant_type": "authorization_code",
                    "code": auth_code,
                    "redirect_uri": self._auth_redirect_url,
                    "client_id": self._app_config.client_id,
                }
            )
            if self._app_config.grant_type is GrantType.CODE:
                token_request_params.update(
                    {
                        "client_secret": self._app_config.client_secret,
                    }
                )
            elif self._app_config.grant_type is GrantType.PKCE:
                token_request_params.update(
                    {
                        "code_verifier": self._auth_code_verifier,  # type: ignore[dict-item]
                    }
                )

        # by deafult, use refresh token
        if not auth_code:
            token_request_params.update(
                {
                    "grant_type": "refresh_token",
                    "refresh_token": self._token_data.refresh_token,  # type: ignore[union-attr]
                }
            )
            if self._app_config.grant_type is GrantType.CODE:
                token_request_params.update(
                    {
                        "redirect_uri": self._auth_redirect_url,
                        "client_id": self._app_config.client_id,
                        "client_secret": self._app_config.client_secret,
                    }
                )
            elif self.grant_type is GrantType.PKCE:
                token_request_params.update(
                    {
                        "code_verifier": self._auth_code_verifier,  # type: ignore[dict-item]
                    }
                )

        response = requests.post(
            self._app_config.token_endpoint, params=token_request_params
        )
        if response.status_code == 201:
            logging.debug("access & refresh token created/refreshed successfully")
            self._token_data = AuthTokenData.parse_obj(response.json())
        else:
            raise RuntimeError("error occurred while attempting to retrieve token")


def parse_app_config(app_config_object: dict) -> OpenAPIAppConfig:
    return OpenAPIAppConfig.parse_obj(app_config_object)
