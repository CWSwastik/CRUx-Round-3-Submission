import io
import base64
import zipfile
from typing import List, Dict


class User:
    def __init__(self, sid: str, name: str) -> None:
        self.sid = sid
        self.name = name
        self.shared: List = []  # A list of the names of the files this user shared

    def __repr__(self) -> str:
        return f"<User name={self.name} sid={self.sid}>"


def zip_images(images: Dict[str, bytes]) -> bytes:
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w") as zipf:
        for img_name in images:
            zipf.writestr(img_name, images[img_name])

    zip_buffer.seek(0)
    return zip_buffer.read()
