import os
import time
import imghdr
import base64
import socketio
from pathlib import Path
from socketio.exceptions import ConnectionError as sioConnectionError


class SocketIOClient:
    """
    This class represents a client that communicates with the server using SocketIO.
    """

    def __init__(self, server_url):
        self.server_url = server_url
        self.sio = socketio.Client()

        @self.sio.on("connect")
        def on_connect():
            pass

        @self.sio.on("disconnect")
        def on_disconnect():
            print("[!] Disconnected from the server, exiting...")
            os._exit(0)

    def connect(self, name):
        try:
            self.sio.connect(self.server_url, headers={"name": name})
        except sioConnectionError:
            raise ConnectionError(
                f"Failed to connect to the server at {self.server_url}"
            )

    def disconnect(self):
        self.sio.disconnect()

    def _is_not_image(self, path):
        """
        Check if a file at the provided path is not an image.
        """
        return imghdr.what(path) is None

    def upload_image(self, path):
        """
        Upload a single image file to the server.
        """
        if self._is_not_image(path):
            raise ValueError("The provided file is not an image!")

        with open(path, "rb") as f:
            filedata = base64.b64encode(f.read())

        data = {"filename": Path(path).name, "filedata": filedata}
        self.sio.emit("upload_image", data=data)

    def upload_folder(self, folder_path):
        """
        Upload all image files from a folder to the server.
        """

        count = 0  # Keep a track of the number of files uploaded
        folder_name = Path(folder_path).name

        for root, _, files in os.walk(folder_path):
            for file in files:
                file_path = os.path.join(root, file)
                if self._is_not_image(file_path):
                    # Don't upload non-image files
                    continue
                relative_path = os.path.relpath(file_path, folder_path)
                file_name = relative_path.replace(os.path.sep, "_")
                with open(file_path, "rb") as file_content:
                    self.sio.emit(
                        "upload_image",
                        {
                            "filename": f"{folder_name}_{file_name}",
                            "filedata": base64.b64encode(file_content.read()),
                        },
                    )
                    count += 1

        return count

    def search_for_images(self, query):
        """
        Search for images on the server based on a query.
        """

        result = self.sio.call("search", query, timeout=5)
        return result

    def download_images(self, images, to_path):
        """
        Download selected images from the server and save them to a ZIP file.
        """

        zipfile = self.sio.call("download_images", images, timeout=5)
        try:
            with open(to_path, "wb") as f:
                f.write(zipfile)
            return True, "Images downloaded successfully!"
        except PermissionError:
            return (
                False,
                "Permission denied, you may have not provided a correct file path (ending in .zip)!",
            )
