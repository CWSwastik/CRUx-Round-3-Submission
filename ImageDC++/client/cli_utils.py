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
                "qname",
                message=qmsg,
                choices=choices,
            ),
        ]
        answers = inquirer.prompt(questions)
        return answers[qname]
