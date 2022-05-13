# OAuth Code Flow RFC6749 4.1 Samples

The sample in this folder features a client-side authentication flow implementation based on [RFC6749 section 4.1 - Authorization Code Grant](https://tools.ietf.org/html/rfc6749#section-4.1), also known as "Authorization Code Flow" or simply "Code Flow".

Saxo uses a standard implementation of this specification. See [the OAuth Docs](https://auth0.com/docs/flows/concepts/auth-code) for more information on this authentication flow.

> Note: make sure to copy the app object from the developer portal into the source code, otherwise the sample will error out with below message.

```
2022-05-13 10:52:15,595 | ERROR | looks like no app config data was pasted in - shutting down...
```

Typical token lifetimes are 20 minutes for the `access_token` and 1 hour for the `refresh_token`. Make sure to repeat the last step in the sample to keep the session alive and replace the 'old' `access_token` value with the new one.