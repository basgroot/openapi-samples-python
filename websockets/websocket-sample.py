# tested in Python 3.6+
# required packages: websocket-client, requests

import websocket, requests, secrets, string, json
from pprint import pprint

# copy your (24-hour) token here
TOKEN = 

# create a random string for context ID and reference ID
CONTEXT_ID = secrets.token_urlsafe(10)
REF_ID = secrets.token_urlsafe(5)


# when a new message is received the bytestring is parsed and payload is printed
# see here for more details on the byte layout of message frames: https://www.developer.saxo/openapi/learn/plain-websocket-streaming
def on_message(ws, message):
    msg_id = int.from_bytes(message[0:8], byteorder='little')
    ref_id_length = message[10]
    ref_id = message[11:11+ref_id_length].decode()
    payload_format = message[11+ref_id_length]
    payload_size = int.from_bytes(message[12+ref_id_length:16+ref_id_length], byteorder='little')
    payload = message[16+ref_id_length:16+ref_id_length+payload_size].decode()
    print(f'Received message {msg_id}, for subscription {ref_id}, with payload:')
    pprint(json.loads(payload))


# handle incorrect token error
def on_error(ws, error):
    if type(error) is KeyboardInterrupt:  # user interrupted interpreter
        ws.close()
    elif error.status_code == 401:
        print('Token could not be verified, please check if the TOKEN variable has been set correctly.')
    else:
        print(error)


# After the websocket is opened, the below code sends a POST request to subscribe to EURUSD prices (Uic 21) on the CONTEXT_ID that the websocket connection is listening to
def on_open(ws):
    print('Websocket handshake successful, creating subscription to OpenAPI...')

    response = requests.post(
        'https://gateway.saxobank.com/sim/openapi/trade/v1/infoprices/subscriptions',
        headers={'Authorization': 'Bearer ' + TOKEN},
        json={
            "Arguments": {
                "AssetType": "FxSpot",
                "Uics": 21
            },
	        'ContextId': CONTEXT_ID,
	        'ReferenceId': REF_ID
        }
    )

    if response.status_code == 201:
        print('Successfully created subscription')
        print('Snapshot data:')
        pprint(response.json()['Snapshot'])
        print('Now receiving delta updates:')
    else:
        print('Could not create subscription due to bad request')
        pprint(response.json())


# When the websocket is closed down, the the subscription is deleted on the server side
def on_close(ws):
    print(f'Deleting subscription with Context ID: {CONTEXT_ID} and Reference ID: {REF_ID}')

    response = requests.delete(
        url=f'https://gateway.saxobank.com/sim/openapi/trade/v1/infoprices/subscriptions/{CONTEXT_ID}/{REF_ID}',
        headers={'Authorization': f'Bearer {TOKEN}'}
    )
    
    if response.status_code == 202:
        print('Successfully deleted subscription')
    else:
        print('Error occurred while deleting subscription - closing websocket')
    
    print('### websocket closed ###')


if __name__ == "__main__":

    print(f'Context ID for this session: {CONTEXT_ID}')
    print(f'Reference ID of EURUSD price subscription: {REF_ID}')
    
    # uncomment the below line to enable debugging output from websocket module
    #websocket.enableTrace(True)
    ws = websocket.WebSocketApp(
        f'wss://streaming.saxobank.com/sim/openapi/streamingws/connect?ContextId={CONTEXT_ID}',
        header={'Authorization': f'Bearer {TOKEN}'},
        on_message = on_message,
        on_error = on_error,
        on_close = on_close,
        on_open = on_open
    )

    ws.run_forever()