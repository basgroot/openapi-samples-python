# Saxo OpenAPI Python Samples

![Python](https://img.shields.io/badge/language-Python%203.6%2B-blue)

This repository contains sample code for developers working with [Saxo's OpenAPI](https://www.home.saxo/platforms/api) using Python.

To get started, make sure you:

1. [Create a (free) developer account](https://www.developer.saxo/accounts/sim/signup) on the Developer Portal
2. Check out the [Reference Documentation](https://www.developer.saxo/openapi/referencedocs) and [Learn](https://www.developer.saxo/openapi/learn) sections
3. Obtain a [24-hour access token](https://www.developer.saxo/openapi/token/current) (this is required to run most sample code in this repo)
4. Play with developer tools provided such as the [Tutorial](https://www.developer.saxo/openapi/tutorial), [Explorer](https://www.developer.saxo/openapi/explorer), and [Application Management](https://www.developer.saxo/openapi/appmanagement)

> Note: step `3` and `4` require a developer account.

## Requirements

All samples in this repository have been tested in Python versions 3.6 and up. Check the individual `.py` files for required packages. For example:

```Python
# tested in Python 3.6+
# required packages: flask, requests
```

Every sample requires either app configuration (obtained through [Application Management](https://www.developer.saxo/openapi/appmanagement)) or a 24-hour access token copied directly into the code. These variables will always be named `app_config` or `token`.

> In case you are facing issues such as `401 Unauthorized` or `Application key not registered`, check if you copied the required input correctly.

## Content

This repository is broken down by subject, each of which includes sample code in multiple languages.

**Table of contents:**

1. Authentication OAuth
2. Authentication Certificate-based
3. Basic Client Information
3. Querying the Instrument Universe
4. Client Portfolio Details
5. Placing Orders
6. Managing Orders/Positions
7. WebSocket Streaming

