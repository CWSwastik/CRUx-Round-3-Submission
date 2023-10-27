import io
import os
import zipfile
from typing import List, Dict


class User:
    def __init__(self, sid: str, name: str) -> None:
        self.sid = sid
        self.name = name
        self.shared: List = []  # A list of the names of the files this user shared

    def __repr__(self) -> str:
        return f"<User name={self.name} sid={self.sid}>"


def ensure_non_clashing_name(name, names):
    modified_name = name
    counter = 1

    while modified_name in names:
        counter += 1
        modified_name = f"{name}{counter}"

    return modified_name


def zip_images(images: Dict[str, bytes]) -> bytes:
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w") as zipf:
        for img_name in images:
            folder, _, fname = img_name.partition("__")
            zipf.writestr(os.path.join(folder, fname), images[img_name])

    zip_buffer.seek(0)
    return zip_buffer.read()
