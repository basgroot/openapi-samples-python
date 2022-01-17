# Python WebSocket Samples

The sample files included in this folder demonstrate implementations of client-side WebSocket streaming using Saxo's OpenAPI with both the `websocket` and `websockets` modules in Python.

Both samples include the basic setup required to create a websocket connection, handle messages, and correctly close a connection.

A EURUSD price stream is created as example subscription in both samples for demonstration purposes. The actual subscription itself matters less in this context, as the main focus is on correctly setting up the underlying WebSocket connection. The `/infoprice` subscription can easily be replaced by other services that support streaming such as `ENS`, `/port/v1/orders` and `/port/v1/positions`, `root/v1/session/features` etc.

The samples write all data to the terminal. To complete this flow, delta updates should be merged with the original `Snapshot` data to create an up-to-date state of the EURUSD quote:

```
Successfully created subscription
Snapshot data:
{'Data': [{'AssetType': 'FxSpot',
           'LastUpdated': '2022-01-17T12:11:25.698000Z',
           'PriceSource': 'SBFX',
           'Quote': {'Amount': 100000,
                     'Ask': 1.14145,
                     'Bid': 1.14125,
                     'DelayedByMinutes': 0,
                     'ErrorCode': 'None',
                     'MarketState': 'Open',
                     'Mid': 1.14135,
                     'PriceSource': 'SBFX',
                     'PriceSourceType': 'Firm',
                     'PriceTypeAsk': 'Tradable',
                     'PriceTypeBid': 'Tradable'},
           'Uic': 21}]}
Now receiving delta updates:
[{'LastUpdated': '2022-01-17T12:11:29.620000Z',
  'Quote': {'Ask': 1.14146, 'Bid': 1.14126, 'Mid': 1.14136},
  'Uic': 21}]
[{'LastUpdated': '2022-01-17T12:11:35.354000Z',
  'Quote': {'Ask': 1.14151, 'Bid': 1.14131, 'Mid': 1.14141},
  'Uic': 21}]
[{'LastUpdated': '2022-01-17T12:11:36.257000Z',
  'Quote': {'Ask': 1.14154, 'Bid': 1.14134, 'Mid': 1.14144},
  'Uic': 21}]
User interrupted the interpreter - closing connection.
```
