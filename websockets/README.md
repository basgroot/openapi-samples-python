# Python WebSocket Samples

The sample files included in this folder demonstrate implementations of client-side WebSocket streaming using Saxo's OpenAPI with both the `websocket` and `websockets` modules in Python.

Both samples include the basic setup required to create a websocket connection, handle messages, and correctly close a connection.

A `EURUSD` price stream is created as example subscription in both samples for demonstration purposes. The actual subscription itself matters less in this context, as the main focus is on correctly setting up the underlying WebSocket connection. The `/infoprice` subscription can easily be replaces by other services that support streaming such as `ENS`, `/port/v1/orders` and `/port/v1/positions`, `root/v1/session/features` etc.