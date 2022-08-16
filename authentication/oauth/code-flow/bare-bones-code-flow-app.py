# tested in Python 3.10
# required packages: flask, requests (see requirements.txt)
# formatted using black, flake8

import threading
import secrets
import webbrowser
import requests  # https://requests.readthedocs.io doesn't support HTTP/2
import logging

from time import sleep

from urllib.parse import urlparse
from flask import Flask, request
from werkzeug.serving import make_server


# reduce logger level to remove debug messages from console output
logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(message)s", level=logging.DEBUG
)
logging.getLogger()

app = Flask(__name__)

# copy your app configuration from https://www.developer.saxo/openapi/appmanagement
# using the "Copy App Object" link on the top-right of the app page
app_config = {
    "AppKey": ...,
    "AuthorizationEndpoint": "https://sim.logonvalidation.net/authorize",
    "TokenEndpoint": "https://sim.logonvalidation.net/token",
    "GrantType": "Code",
    "OpenApiBaseUrl": "https://gateway.saxobank.com/sim/openapi/",
    "RedirectUrls": [...],
    "AppSecret": ...
}

if app_config["AppKey"] is ...:
    logging.error("looks like no app config data was pasted in - shutting down...")
    exit(-1)

# generate random 10-character string as state
state = secrets.token_urlsafe(10)

# parse redirect object (assuming first redirect url is localhost)
r_url = urlparse(app_config["RedirectUrls"][0])

# define server route that will handle the redirect callback
@app.route(r_url.path)
def handle_callback():
    """
    Saxo SSO will redirect to this endpoint after the user authenticates.
    """

    global received_callback, code, error_message, received_state
    error_message = None
    code = None

    if "error" in request.args:
        error_message = request.args["error"] + ": " + request.args["error_description"]
        render_text = "Error occurred. Please check the application command line."
    else:
        code = request.args["code"]
        render_text = "Authentication succeeded! Please go back to the application."

    received_state = request.args["state"]
    received_callback = True

    return render_text


class ServerThread(threading.Thread):
    """
    The Flask server runs inside a thread, and will be terminated when the callback is received.
    """

    def __init__(self, app):
        threading.Thread.__init__(self)
        host = urlparse(app_config["RedirectUrls"][0]).hostname
        port = urlparse(app_config["RedirectUrls"][0]).port
        self.server = make_server(host, port, app)
        self.ctx = app.app_context()
        self.ctx.push()

    def run(self):
        logging.debug("starting server and listen for callback from Saxo...")
        self.server.serve_forever()

    def shutdown(self):
        logging.debug("terminating server...")
        self.server.shutdown()


auth_request_params = {
    "response_type": "code",
    "client_id": app_config["AppKey"],
    "state": state,
    "redirect_uri": app_config["RedirectUrls"][0],
    "client_secret": app_config["AppSecret"],
}

# prepare the request so it is never actually sent (need the url for the browser to open)
auth_url = requests.Request(
    "GET", url=app_config["AuthorizationEndpoint"], params=auth_request_params
).prepare()

# this variable will flip to 'True' when the Flask server receives a callback from Saxo SSO
received_callback = False

logging.debug("opening browser and loading authorization URL...")
webbrowser.open_new(auth_url.url)

server = ServerThread(app)
server.start()

# wait for login to be completed by the user, until then listen for redirect
while not received_callback:
    try:
        sleep(1)
    except KeyboardInterrupt:
        logging.warning("keyboard interrupt received - shutting down...")
        server.shutdown()
        exit(-1)

logging.debug("received callback")
server.shutdown()

if state != received_state:
    logging.error("received state does not match original state.")
    exit(-1)

if error_message:
    logging.error("received error message - authentication not successful")
    logging.error(error_message)
    exit(-1)

logging.debug("authentication successful - requesting token...")

# use the application configuration data pasted above to formulate token request
token_request_params = {
    "grant_type": "authorization_code",
    "code": code,
    "redirect_uri": app_config["RedirectUrls"][0],
    "client_id": app_config["AppKey"],
    "client_secret": app_config["AppSecret"]
}

r = requests.post(app_config["TokenEndpoint"], params=token_request_params)

if r.status_code != 201:
    logging.error("error occurred while retrieving token - shutting down...")
    exit(-1)

token_data = r.json()

logging.debug(f"received token data: {token_data}")

logging.debug("requesting users/me from OpenAPI...")

headers = {
    "Authorization": f"Bearer {token_data['access_token']}"
}

r = requests.get(app_config["OpenApiBaseUrl"] + "port/v1/users/me", headers=headers)

# The X-Correlation header should be logged at every request! Only with this ID Saxo can help troubleshooting issues.
# https://openapi.help.saxo/hc/en-us/articles/4434784593309
x_correlation = r.headers["x-correlation"]

if r.status_code != 200:
    logging.error(f"error occurred querying user data from the OpenAPI - shutting down with X-Correlation header: {x_correlation}")

user_data = r.json()

logging.debug(f"sucessfully received user data: {user_data}")

logging.debug("exercizing refresh token to obtain new token data...")

# use the application configuration data pasted above to formulate refresh token request
refresh_request_params = {
    "grant_type": "refresh_token",
    "refresh_token": token_data["refresh_token"],
    "redirect_uri": app_config["RedirectUrls"][0],
    "client_id": app_config["AppKey"],
    "client_secret": app_config["AppSecret"]
}

r = requests.post(app_config["TokenEndpoint"], params=refresh_request_params)

if r.status_code != 201:
    logging.debug("error occurred while retrieving token - shutting down...")
    exit(-1)

token_data = r.json()

logging.debug(f"sucessfully refreshed tokens: {token_data}")

logging.debug("sample completed successfully - shutting down...")
exit(0)
