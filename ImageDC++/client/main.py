from yaspin import yaspin
from cli_utils import CLIUtils
from client import SocketIOClient


def main():
    cli = CLIUtils()
    cli.display_title()

    name = cli.get_text_input("name", "What's your name?")

    server_url = "http://localhost:8080"

    client = SocketIOClient(server_url)
    with yaspin(text="Connecting to the server...", color="blue") as spinner:
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
                "Please enter the path to your image file",
            )
            try:
                client.upload_image(path)
            except FileNotFoundError:
                cli.log_error("The provided file was not found!")
            except ValueError as e:
                cli.log_error(str(e))

        elif choice == "Download Images":
            print("No")
        else:
            break


if __name__ == "__main__":
    main()
