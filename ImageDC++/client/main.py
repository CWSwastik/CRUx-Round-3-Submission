import os
from cli_utils import CLIUtils
from client import SocketIOClient


def main():
    cli = CLIUtils()
    cli.display_title()

    name = cli.get_text_input("name", "What's your name?")

    server_url = "http://localhost:8080"

    client = SocketIOClient(server_url)
    with cli.spinner(text="Connecting to the server...", color="blue") as spinner:
        cli.wait(0.5)
        try:
            client.connect(name)
            spinner.text = "Connected to the server"
            spinner.ok("✅ ")
        except ConnectionError as e:
            spinner.stop()
            cli.log_error(str(e))
            return

    while True:
        cli.wait()
        choice = cli.get_multi_choice_input(
            "choice",
            "What would you like to do?",
            ["Upload Images", "Download Images", "Quit"],
        )

        if choice == "Upload Images":
            path = cli.get_path(
                "path",
                "Please enter the path to your image file or folder of image files",
            )
            if os.path.isdir(path):
                client.upload_folder(path)
            else:
                try:
                    with cli.spinner("Uploading image...") as spinner:
                        cli.wait(0.3)
                        client.upload_image(path)
                        spinner.text = "Image uploaded!"
                        spinner.ok("✅ ")
                except FileNotFoundError:
                    cli.log_error("The provided file was not found!")
                except ValueError as e:
                    cli.log_error(str(e))

        elif choice == "Download Images":
            query = cli.get_text_input("query", "Enter search query")
            with cli.spinner(text="Searching for images..."):
                cli.wait(0.3)
                images = client.search_for_images(query)

            # TODO: Sort by user, like show users first, then their images containing the query
            if len(images) == 0:
                print(
                    "[!] Uh Oh! Seems like there are no images that match this query."
                )
            else:
                result = cli.get_selected_items(
                    "choices",
                    "Please choose the images that you'd like to download",
                    images,
                )
                zip_path = cli.get_path("path", "Please enter the output path")
                with cli.spinner("Downloading images...") as spinner:
                    cli.wait(0.3)
                    client.download_images(result, zip_path)
                    spinner.text = f"Images downloaded to {zip_path}!"
                    spinner.ok("✅ ")
        else:
            break


if __name__ == "__main__":
    main()
