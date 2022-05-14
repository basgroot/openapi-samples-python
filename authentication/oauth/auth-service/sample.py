import requests

from saxo_auth_service import SaxoAuthService, parse_app_config

app_config = {
    "AppName": "Your application config data is pasted here...",
    "AppKey": ...,
    "AuthorizationEndpoint": ...,
    "TokenEndpoint": ...,
    "GrantType": ...,
    "OpenApiBaseUrl": ...,
    "RedirectUrls": [...],
    "AppSecret": ...,
}

saxo_auth = SaxoAuthService(parse_app_config(app_config))

saxo_auth.login()

print(f"{saxo_auth.logged_in=}")

print(saxo_auth.access_token)

response = requests.get(
    url=f"{saxo_auth.api_base_url}port/v1/users/me",
    headers={"Authorization": f"Bearer {saxo_auth.access_token}"},
)
print(response.json())

saxo_auth.refresh()

print(saxo_auth.access_token)

saxo_auth.logout()

print(f"{saxo_auth.logged_in=}")
