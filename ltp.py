import asyncio
import json
import websockets
import datetime


async def websocket_handler(share,access_token):
    access_token = access_token
    api_key="7bysRZCyXtO7xy9uxk9EtZbNMa2sH6qr"
    if access_token:
        api_key = "7bysRZCyXtO7xy9uxk9EtZbNMa2sH6"
        uri = f"wss://streams.myespresso.com/espstream/api/stream?ACCESS_TOKEN={access_token}&API_KEY={api_key}"
        feed = {"action": "feed", "key": ["ltp"], "value": [share]}

        async with websockets.connect(uri) as ws:
            await ws.send(json.dumps(feed))

            while True:
                try:
                    message = await ws.recv()
                    data = json.loads(message)
                    data=data["data"]
                    # Check if the received data is a list (JSON format)
                    if isinstance(data, list):
                        # Assuming the list contains a dictionary with key 'ltp', extract the 'ltp' value
                        ltp_value = data[0]['ltp']
                        print('LTP:', ltp_value)
                        return ltp_value

                    # Check if the received data is a dictionary (non-JSON format)
                    elif isinstance(data, dict) and 'status' in data and 'message' in data:
                        print("Received non-JSON data:", data['message'])

                except json.JSONDecodeError as e:
                    print("Received non-JSON data:", message)
                except Exception as ex:
                    print("An error occurred:", ex)
    else:
        print("No valid access token found.")


if __name__ == "__main__":
    asyncio.run(websocket_handler("NC25","eyJ0eXAiOiJzZWMiLCJhbGciOiJIUzI1NiJ9.eyJqdGkiOiIzVmg2WDhmQ2hWbXNRSTZYTUJSMWF3Z2RKNzJGM2h0bnJBdWxMWVZKZWZVVDhOMlZCUHR4UnJ1MnkxSXhMNEw4OGQ5QUlrc0FXcWlPMmc5SVduVjZBZEZZbGZJSWdQUHJLVlAzQ0hKT3QzaVIwZll4ZTlKV25Ha3ZNUTc2UWg3czhnMjNoUWxGV3o3OFA3YlRFZmFnY2RUc2JjRUNTamYvQ1F5Qlh6Y1JYZ2M9IiwiaWF0IjoxNzA5NjIxNDgyLCJleHAiOjE3MDk2NjMzOTl9.KOXyPyTlO7YcucZYp9LDpqurk22rp6smKGa6UUJsMAA"))
