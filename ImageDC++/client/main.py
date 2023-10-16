from cli_utils import CLIUtils
from client import connect


def main():
    cli = CLIUtils()
    cli.display_title()

    name = cli.get_text_input("name", "What's your name?")
    print(f"Hi, {name}")

    connect()

    while True:
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
                with open(path, "r") as f:
                    print(f.read())
            except FileNotFoundError:
                cli.log_error("The provided file was not found!")
        elif choice == "Download Images":
            print("No")
        else:
            break


if __name__ == "__main__":
    main()
