import os
import time
import pyfiglet
import inquirer
from colorama import just_fix_windows_console, Fore, Style


class CLIUtils:
    def __init__(self) -> None:
        just_fix_windows_console()

    def display_title(self):
        title = pyfiglet.figlet_format("Image DC ++", font="big")
        print(Fore.RED + title + Style.RESET_ALL)

    def get_text_input(self, qname, qmsg):
        questions = [inquirer.Text(qname, qmsg)]
        answers = inquirer.prompt(questions)

        return answers[qname]

    def get_multi_choice_input(self, qname, qmsg, choices):
        questions = [
            inquirer.List(
                qname,
                message=qmsg,
                choices=choices,
            ),
        ]
        answers = inquirer.prompt(questions)
        return answers[qname]

    def get_path(self, qname, qmsg):
        questions = [
            inquirer.Path(
                qname,
                message=qmsg,
                path_type=inquirer.Path.ANY,
            ),
        ]
        answers = inquirer.prompt(questions)
        return os.path.abspath(answers[qname])

    def log_message(self, message):
        print("[-] LOG: " + message)

    def log_warning(self, message):
        print(Fore.YELLOW + "[!] WARNING: " + message + Style.RESET_ALL)

    def log_error(self, message):
        print(
            "["
            + Fore.RED
            + "X"
            + Style.RESET_ALL
            + "]"
            + Fore.RED
            + " ERROR: "
            + message
            + Style.RESET_ALL
        )
        time.sleep(1)
