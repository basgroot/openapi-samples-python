# tested in Python 3.6+
# required packages: websocket-client, requests

import json
import secrets
from pprint import pprint

import requests
import websocket

# copy your (24-hour) token here
TOKEN = ""

# create a random string for context ID and reference ID
CONTEXT_ID = secrets.token_urlsafe(10)
REF_ID = secrets.token_urlsafe(5)


# when a new message is received the bytestring is parsed and payload is printed
# see here for more details on the byte layout of message frames: https://www.developer.saxo/openapi/learn/plain-websocket-streaming
def on_message(ws, message):
   index = 0
   while index < len(message):
        print(len(message));
        # Message identifier (8 bytes)
        # 64-bit little-endian unsigned integer identifying the message.
        # The message identifier is used by clients when reconnecting. It may not be a sequence number and no interpretation
        # of its meaning should be attempted at the client.
        msg_id = int.from_bytes(message[index:index + 8], byteorder="little")
        index += 8
        # Version number (2 bytes)
        # Ignored in this example. Get it using 'messageEnvelopeVersion = message.getInt16(index)'.
        index += 2
        # Reference id size 'Srefid' (1 byte)
        # The number of characters/bytes in the reference id that follows.
        ref_id_length = message[index]
        index += 1
        # Reference id (Srefid bytes)
        # ASCII encoded reference id for identifying the subscription associated with the message.
        # The reference id identifies the source subscription, or type of control message (like '_heartbeat').
        ref_id = message[index : index + ref_id_length].decode()
        index += ref_id_length
        # Payload format (1 byte)
        # 8-bit unsigned integer identifying the format of the message payload. Currently the following formats are defined:
        #  0: The payload is a UTF-8 encoded text string containing JSON. Used for this sample.
        #  1: The payload is a binary protobuffer message. See JavaScript repository for a Protobuf example.
        # The format is selected when the client sets up a streaming subscription so the streaming connection may deliver a mixture of message format.
        # Control messages such as subscription resets are not bound to a specific subscription and are always sent in JSON format.
        payload_format = message[index]
        if payload_format != 0:
            print(f"An unsupported payload_format is sent by the server: {payload_format}!")
        index += 1
        # Payload size 'Spayload' (4 bytes)
        # 64-bit little-endian unsigned integer indicating the size of the message payload.
        payload_size = int.from_bytes(message[index : index + 4], byteorder="little")
        index += 4
        # Payload (Spayload bytes)
        # Binary message payload with the size indicated by the payload size field.
        # The interpretation of the payload depends on the message format field.
        payload = message[index : index + payload_size].decode()
        index += payload_size
        print(f"Received message {msg_id}, for subscription {ref_id}, with payload:")
        pprint(json.loads(payload))


# handle incorrect token error
def on_error(ws, error):
    if type(error) is KeyboardInterrupt:  # user interrupted interpreter
        ws.close()
    elif error.status_code == 401:
        print(
            "Token could not be verified, please check if the TOKEN variable has been set correctly."
        )
    else:
        print(error)


# After the websocket is opened, the below code sends a POST request to subscribe to EURUSD prices (Uic 21) on the CONTEXT_ID that the websocket connection is listening to
def on_open(ws):
    print("Websocket handshake successful, creating subscription to OpenAPI...")

    response = requests.post(
        "https://gateway.saxobank.com/sim/openapi/trade/v1/infoprices/subscriptions",
        headers={"Authorization": "Bearer " + TOKEN},
        json={
            "Arguments": {"AssetType": "FxSpot", "Uics": "21, 22, 23"},
            "ContextId": CONTEXT_ID,
            "ReferenceId": REF_ID,
        },
    )

    if response.status_code == 201:
        print("Successfully created subscription")
        print("Snapshot data:")
        pprint(response.json()["Snapshot"])
        print("Now receiving delta updates:")
    else:
        print("Could not create subscription due to bad request")
        pprint(response.json())


# When the websocket is closed down, the the subscription is deleted on the server side
def on_close(ws):
    print(
        f"Deleting subscription with Context ID: {CONTEXT_ID} and Reference ID: {REF_ID}"
    )

    response = requests.delete(
        url=f"https://gateway.saxobank.com/sim/openapi/trade/v1/infoprices/subscriptions/{CONTEXT_ID}/{REF_ID}",
        headers={"Authorization": f"Bearer {TOKEN}"},
    )

    if response.status_code == 202:
        print("Successfully deleted subscription")
    else:
        print("Error occurred while deleting subscription - closing websocket")

    print("### websocket closed ###")


# Only one app is entitled to receive realtime prices. This is handled via the primary session.
# More info on keeping the status: https://saxobank.github.io/openapi-samples-js/websockets/primary-monitoring/
def take_primary_session():
    requests.put(
        "https://gateway.saxobank.com/sim/openapi/root/v1/sessions/capabilities",
        headers={"Authorization": "Bearer " + TOKEN},
        json={"TradeLevel": "FullTradingAndChat"},
    )


if __name__ == "__main__":

    print(f"Context ID for this session: {CONTEXT_ID}")
    print(f"Reference ID of price subscription: {REF_ID}")

    take_primary_session()

    # uncomment the below line to enable debugging output from websocket module
    # websocket.enableTrace(True)
    ws = websocket.WebSocketApp(
        f"wss://streaming.saxobank.com/sim/openapi/streamingws/connect?ContextId={CONTEXT_ID}",
        header={"Authorization": f"Bearer {TOKEN}"},
        on_message=on_message,
        on_error=on_error,
        on_close=on_close,
        on_open=on_open,
    )

    ws.run_forever()
