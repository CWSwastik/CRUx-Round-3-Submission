import io
import os
import zipfile
from typing import List, Dict


class User:
    """
    Represents a user with a unique identifier (SID) and a name.

    Args:
        sid (str): The user's unique identifier.
        name (str): The user's name.

    Attributes:
        sid (str): The user's unique identifier.
        name (str): The user's name.
        shared (List): A list of the names of the files this user shared.
    """

    def __init__(self, sid: str, name: str) -> None:
        self.sid = sid
        self.name = name
        self.shared: List[str] = []  # A list of the names of the files this user shared

    def __repr__(self) -> str:
        return f"<User name={self.name} sid={self.sid}>"


def ensure_non_clashing_name(name: str, names: List[str]):
    """
    Ensure that a given name does not clash with any names in a list.

    Args:
        name (str): The input name to check.
        names (List): A list of existing names to check against.

    Returns:
        str: A non-clashing name based on the input name.
    """

    modified_name = name
    counter = 1

    while modified_name in names:
        counter += 1
        modified_name = f"{name}{counter}"

    return modified_name


def clean_name(name):
    """
    Clean a name by replacing consecutive underscores with a single underscore.

    Args:
        name (str): The input name to clean.

    Returns:
        str: The cleaned name with consecutive underscores replaced by a single underscore.

    Example:
        cleaned_name = clean_name("example__name")
        print(cleaned_name)  # Output: "example_name"
    """

    parts = name.split("_")
    cleaned_parts = [parts[0]]  # Initialize with the first part
    for part in parts[1:]:
        if part:  # Ignore empty parts
            cleaned_parts.append(part)
    return "_".join(cleaned_parts)


def zip_images(images: Dict[str, bytes]) -> bytes:
    """
    Create a ZIP archive from a dictionary of images.

    Args:
        images (Dict): A dictionary of image data, where keys are filenames and values are bytes.

    Returns:
        bytes: A bytes object containing the ZIP archive data.
    """

    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w") as zipf:
        for img_name in images:
            folder, _, fname = img_name.partition("__")
            zipf.writestr(os.path.join(folder, fname), images[img_name])

    zip_buffer.seek(0)
    return zip_buffer.read()
