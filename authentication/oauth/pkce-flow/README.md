# OAuth Code Flow w/ PKCE RFC7636 Samples

Samples in this folder feature client-side authentication flows based on [RFC7636](https://tools.ietf.org/html/rfc7636), also known as "Authorization Code Flow with PKCE" or simply "PKCE Flow". This spec is based on standard code flow but adds an ad-hoc `verifier` secret, which allows for more flexibility on the client side such as dynamic redirect ports (for mobile and native apps) and eliminates the neccesity for a client-side secret to be kept in-code.

Saxo uses a standard implementation of this specification. See [the OAuth Docs](https://auth0.com/docs/flows/concepts/auth-code-pkce) for more information on this authentication flow.

> Make sure the redirect URI configured on your app does **not** include a hard-coded port number (this needs to be assigned dynamically when sending the authorization request).
