# tested in Python 3.6+
# required packages: flask, requests

import threading
import secrets
import webbrowser
import requests

from time import sleep

from urllib.parse import urlparse
from pprint import pprint
from flask import Flask, request
from werkzeug.serving import make_server

app = Flask(__name__)

# copy your app configuration from https://www.developer.saxo/openapi/appmanagement
app_config = {
    "AppKey": "Your app name",
    "AuthorizationEndpoint": "https://sim.logonvalidation.net/authorize",
    "TokenEndpoint": "https://sim.logonvalidation.net/token",
    "GrantType": "Code",
    "OpenApiBaseUrl": "https://gateway.saxobank.com/sim/openapi/",
    "RedirectUrls": ["http://localhost:5000/redirect"],
    "AppSecret": "Your app secret"
}

# generate 10-character string as state
state = secrets.token_urlsafe(10)

# parse redirect
r_url = urlparse(app_config["RedirectUrls"][0])


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
        render_text = "Please return to the application."

    received_state = request.args["state"]
    received_callback = True

    return render_text


class ServerThread(threading.Thread):
    """
    The Flask server will run inside a thread.
    """

    def __init__(self, app):
        threading.Thread.__init__(self)
        host = urlparse(app_config["RedirectUrls"][0]).hostname
        port = urlparse(app_config["RedirectUrls"][0]).port
        self.server = make_server(host, port, app)
        self.ctx = app.app_context()
        self.ctx.push()

    def run(self):
        print("Starting server and listen for callback from Saxo...")
        self.server.serve_forever()

    def shutdown(self):
        print("Terminating server...")
        self.server.shutdown()


params = {
    "response_type": "code",
    "client_id": app_config["AppKey"],
    "state": state,
    "redirect_uri": app_config["RedirectUrls"][0],
    "client_secret": app_config["AppSecret"],
}

auth_url = requests.Request(
    "GET", url=app_config["AuthorizationEndpoint"], params=params
).prepare()

print("Opening browser and loading authorization URL...")
received_callback = False
webbrowser.open_new(auth_url.url)

server = ServerThread(app)
server.start()
while not received_callback:
    try:
        sleep(1)
    except KeyboardInterrupt:
        print("Caught keyboard interrupt. Shutting down...")
        server.shutdown()
        exit(-1)
server.shutdown()

if state != received_state:
    print("Received state does not match original state.")
    exit(-1)

if error_message:
    print("Received error message. Authentication not successful.")
    print(error_message)
    exit(-1)


print("Authentication successful. Requesting token...")

params = {
    "grant_type": "authorization_code",
    "code": code,
    "redirect_uri": app_config["RedirectUrls"][0],
    "client_id": app_config["AppKey"],
    "client_secret": app_config["AppSecret"],
}

r = requests.post(app_config["TokenEndpoint"], params=params)

if r.status_code != 201:
    print("Error occurred while retrieving token. Terinating.")
    exit(-1)

print("Received token data:")
token_data = r.json()

pprint(token_data)


print("Requesting user data from OpenAPI...")

headers = {"Authorization": f"Bearer {token_data['access_token']}"}

r = requests.get(app_config["OpenApiBaseUrl"] + "port/v1/users/me", headers=headers)

if r.status_code != 200:
    print("Error occurred querying user data from the OpenAPI. Terminating.")

user_data = r.json()

pprint(user_data)


print("Using refresh token to obtain new token data...")

params = {
    "grant_type": "refresh_token",
    "refresh_token": token_data["refresh_token"],
    "redirect_uri": app_config["RedirectUrls"][0],
    "client_id": app_config["AppKey"],
    "client_secret": app_config["AppSecret"],
}

r = requests.post(app_config["TokenEndpoint"], params=params)

if r.status_code != 201:
    print("Error occurred while retrieving token. Terinating.")
    exit(-1)

print("Received new token data:")
token_data = r.json()

pprint(token_data)
