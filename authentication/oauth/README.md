# OAuth Samples

Saxo supports implementations of 3 different OAuth specifications. Make sure you pick the right flow that corresponds to the grant type selected [on the Developer Portal](https://www.developer.saxo/openapi/appmanagement).

> Implicit flow is not supported for Python as the token response is redirected to the callback URI with the access token in a `hash fragment`, which cannot be accessed by back-end services such as a Flask server. The OAuth organisation actually [recommends against using implicit flows entirely](https://oauth.net/2/grant-types/implicit/), in favour of the new PKCE flow.