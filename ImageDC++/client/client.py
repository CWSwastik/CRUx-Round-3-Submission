import time
import imghdr
import base64
import socketio
from pathlib import Path
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

    def connect(self, name):
        try:
            self.sio.connect(self.server_url, headers={"name": name})
        except sioConnectionError:
            raise ConnectionError(
                f"Failed to connect to the server at {self.server_url}"
            )

    def disconnect(self):
        self.sio.disconnect()

    def upload_image(self, path):
        if imghdr.what(path) is None:
            raise ValueError("The provided file is not an image!")

        with open(path, "rb") as f:
            filedata = base64.b64encode(f.read())

        data = {"filename": Path(path).name, "filedata": filedata}
        self.sio.emit("upload_image", data=data)

    def search_for_images(self, query):
        result = self.sio.call("search", query, timeout=5)
        return result

    def download_images(self, images, to_path):
        zipfile = self.sio.call("download_images", images, timeout=5)
        with open(to_path, "wb") as f:
            f.write(zipfile)
