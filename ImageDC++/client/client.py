import time
import socketio
from socketio.exceptions import ConnectionError as sioConnectionError


class SocketIOClient:
    def __init__(self, server_url):
        self.server_url = server_url
        self.sio = socketio.Client()

        @self.sio.on("connect")
        def on_connect():
            pass

        @self.sio.on("disconnect")
        def on_disconnect():
            print("Disconnected from the server")

    def connect(self):
        try:
            self.sio.connect(self.server_url)
        except sioConnectionError:
            raise ConnectionError(
                f"Failed to connect to the server at {self.server_url}"
            )

    def disconnect(self):
        self.sio.disconnect()
