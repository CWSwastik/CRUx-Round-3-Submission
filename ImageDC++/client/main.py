import os
import socket
from cli_utils import CLIUtils
from client import SocketIOClient
from typing import Union


def setup_client(name: str, cli: CLIUtils) -> Union[SocketIOClient, None]:
    """
    This function sets up the client by connecting to the server.
    Automatically determines the server URL assuming it's running on the LAN and on port 8080.
    If an automatic connection attempt fails, the user is prompted to enter the server URL manually.

    Args:
        name (str): The client's name for identification.
        cli (CLIUtils): An instance of CLIUtils for handling command-line interactions.

    Returns:
        SocketIOClient or None: A SocketIOClient instance if the connection is successful,
        or None if the connection fails.
    """

    # Automatically figure out the server url (assuming its running on LAN and on port 8080)

    server_url = f"http://{socket.gethostbyname(socket.gethostname())}:8080"

    client = SocketIOClient(server_url)
    with cli.spinner(text="Connecting to the server...", color="green") as spinner:
        cli.wait(0.5)
        try:
            client.connect(name)
            spinner.text = "Connected to the server"
            spinner.ok("[✓]")
            return client
        except ConnectionError as e:
            spinner.stop()
            cli.log_error(str(e))

    server_url = (
        cli.get_text_input(
            "server_url",
            "Failed to autoconnect to server, please enter the server url",
        )
        or "http://localhost:8080"
    )

    client.server_url = server_url
    with cli.spinner(text="Connecting to the server...", color="green") as spinner:
        cli.wait(0.5)
        try:
            client.connect(name)
            spinner.text = "Connected to the server"
            spinner.ok("[✓]")
            return client
        except ConnectionError as e:
            spinner.stop()
            cli.log_error(str(e))
            return None


def upload_images(cli: CLIUtils, client: SocketIOClient) -> None:
    """
    This function allows the user to upload either a single image file or an entire folder of image files to the server.
    If a folder is provided, all image files within the folder are uploaded.

    Args:
        cli (CLIUtils): An instance of CLIUtils for handling command-line interactions.
        client (SocketIOClient): An instance of SocketIOClient for server communication.

    Returns:
        None
    """

    path = cli.get_path(
        "path",
        "Please enter the path to your image file or folder of image files",
    )
    if os.path.isdir(path):
        with cli.spinner("Uploading folder...", color="green") as spinner:
            n_files = client.upload_folder(path)
            spinner.text = f"Folder uploaded! ({n_files}/{n_files} files)"
            spinner.ok("[✓]")

    else:
        try:
            with cli.spinner("Uploading image...", color="green") as spinner:
                cli.wait(0.3)
                client.upload_image(path)
                spinner.text = "Image uploaded!"
                spinner.ok("[✓]")
        except FileNotFoundError:
            cli.log_error("The provided file was not found!")
        except ValueError as e:
            cli.log_error(str(e))


def download_images(name: str, cli: CLIUtils, client: SocketIOClient) -> None:
    """
    This function allows the user to search for images on the server based on a query (defaulting to the user's name) and select images to download.
    Selected images are compressed into a ZIP file.

    Args:
        name (str): The user's name for identification.
        cli (CLIUtils): An instance of CLIUtils for handling command-line interactions.
        client (SocketIOClient): An instance of SocketIOClient for server communication.

    Returns:
        None
    """

    query = (
        cli.get_text_input("query", "Enter search query (default: your name)") or name
    )
    with cli.spinner(text="Searching for images..."):
        cli.wait(0.3)
        images = client.search_for_images(query)

    if len(images) == 0:
        print("[!] Uh Oh! Seems like there are no images that match this query.")
    else:
        display_text = {}
        for img in images:
            user, _, fname = img.partition("__")
            display_text[fname + f" (Uploader: {user})"] = img

        items = cli.get_selected_items(
            "choices",
            "Please choose the images that you'd like to download (space to select, enter to confirm)",
            display_text,
        )
        items = [display_text[i] for i in items]

        if not items:
            print("[!] Not downloading any images as none were selected.")
            return

        zip_path = cli.get_path(
            "path", "Please enter the output file path (ending in .zip)"
        )
        with cli.spinner("Downloading images...", color="green") as spinner:
            cli.wait(0.3)
            res = client.download_images(items, zip_path)
            if res[0]:
                spinner.text = (
                    f"{len(items)}/{len(images)} Images downloaded to {zip_path}!"
                )
                spinner.ok("[✓]")
            else:
                spinner.text = f"Failed to download images: {res[1]}"
                spinner.color = "red"
                spinner.fail("[X]")


def main():
    cli = CLIUtils()
    cli.display_title()

    name = cli.get_text_input("name", "What's your name?")
    if not name:
        cli.log_warning("No name provided. Using default name: 'Anonymous'")
        name = "Anonymous"

    client = setup_client(name, cli)
    if client is None:
        return

    while True:
        cli.wait()
        choice = cli.get_multi_choice_input(
            "choice",
            "What would you like to do?",
            ["Upload Images", "Download Images", "Quit"],
        )

        if choice == "Upload Images":
            upload_images(cli, client)
        elif choice == "Download Images":
            download_images(name, cli, client)
        else:
            break


if __name__ == "__main__":
    main()
