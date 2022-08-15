# tested in Python 3.6+
# required packages: websockets, requests

import asyncio
import json
import secrets
from pprint import pprint

import requests
import websockets

# copy your (24-hour) token here
TOKEN = ""

# create a random string for context ID and reference ID
CONTEXT_ID = secrets.token_urlsafe(10)
REF_ID = secrets.token_urlsafe(5)


def create_subscription(context_id, ref_id, token):
    response = requests.post(
        "https://gateway.saxobank.com/sim/openapi/trade/v1/infoprices/subscriptions",
        headers={"Authorization": "Bearer " + token},
        json={
            "Arguments": {"Uics": "21, 22, 23", "AssetType": "FxSpot"},
            "ContextId": context_id,
            "ReferenceId": ref_id,
        },
    )

    if response.status_code == 201:
        print("Successfully created subscription")
        print("Snapshot data:")
        pprint(response.json()["Snapshot"])
        print("Now receiving delta updates:")
    elif response.status_code == 401:
        print("Error setting up subscription - check TOKEN value")
        exit()


def decode_message(message):
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


async def streamer(context_id, ref_id, token):
    url = f"wss://streaming.saxobank.com/sim/openapi/streamingws/connect?contextId={context_id}"
    headers = {"Authorization": f"Bearer {token}"}

    async with websockets.connect(url, extra_headers=headers) as websocket:
        async for message in websocket:
            decode_message(message)


# Only one app is entitled to receive realtime prices. This is handled via the primary session.
# More info on keeping the status: https://saxobank.github.io/openapi-samples-js/websockets/primary-monitoring/
def take_primary_session():
    requests.put(
        "https://gateway.saxobank.com/sim/openapi/root/v1/sessions/capabilities",
        headers={"Authorization": "Bearer " + TOKEN},
        json={"TradeLevel": "FullTradingAndChat"},
    )


if __name__ == "__main__":
    take_primary_session()
    try:
        create_subscription(CONTEXT_ID, REF_ID, TOKEN)
        asyncio.get_event_loop().run_until_complete(streamer(CONTEXT_ID, REF_ID, TOKEN))
    except KeyboardInterrupt:
        print("User interrupted the interpreter - closing connection.")
        exit()
