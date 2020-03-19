# Python WebSocket Samples

The sample files included in this folder demonstrate implementations of client-side WebSocket streaming using Saxo's OpenAPI with both the `websocket` and `websockets` modules in Python.

Both samples include the basic setup required to create a websocket connection, handle messages, and correctly close a connection.

A `EURUSD` price stream is created as example subscription in both samples for demonstration purposes. The actual subscription itself matters less in this context, as the main focus is on correctly setting up the underlying WebSocket connection. The `/infoprice` subscription can easily be replaced by other services that support streaming such as `ENS`, `/port/v1/orders` and `/port/v1/positions`, `root/v1/session/features` etc.

The samples write all data to the terminal. To complete this flow, delta updates should be merged with the original `Snapshot` data to create an up-to-date state of the EURUSD quote:

```
Successfully created subscription
Snapshot data:
{'Data': [{'AssetType': 'FxSpot',
           'LastUpdated': '2020-03-19T12:31:57.787000Z',
           'Quote': {'Amount': 100000,
                     'Ask': 1.07371,
                     'Bid': 1.0737,
                     'DelayedByMinutes': 0,
                     'ErrorCode': 'None',
                     'Mid': 1.073705,
                     'PriceSource': 'SBFX',
                     'PriceSourceType': 'Firm',
                     'PriceTypeAsk': 'Tradable',
                     'PriceTypeBid': 'Tradable'},
           'Uic': 21}]}
Now receiving delta updates:
[{'LastUpdated': '2020-03-19T12:31:58.841000Z',
  'Quote': {'Ask': 1.07373, 'Bid': 1.07371, 'Mid': 1.07372},
  'Uic': 21}]
[{'LastUpdated': '2020-03-19T12:32:00.047000Z',
  'Quote': {'Ask': 1.07374, 'Mid': 1.073725},
  'Uic': 21}]
[{'LastUpdated': '2020-03-19T12:32:01.073000Z',
  'Quote': {'Ask': 1.07356, 'Bid': 1.07355, 'Mid': 1.073555},
  'Uic': 21}]
User interrupted the interpreter - closing connection.
```
