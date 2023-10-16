from cli_utils import CLIUtils
from client import connect


def main():
    cli = CLIUtils()
    cli.display_title()

    name = cli.get_text_input("name", "What's your name?")
    print(f"Hi, {name}")

    connect()


if __name__ == "__main__":
    main()
