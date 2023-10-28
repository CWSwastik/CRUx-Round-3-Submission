from .database import Database

import re
import openai
import aiohttp


def parse_time_to_seconds(time_str):
    """
    Parses a time duration string and returns the total time in seconds.

    Args:
        time_str (str): A string representing a time duration in various formats, such as "1 hour 2 min 24 sec,"
                       "3 h 30 min," or "45s."

    Returns:
        int: The total time duration in seconds.
    """

    day_pattern = r"(\d+)\s*(d|day(s)?)"
    hour_pattern = r"(\d+)\s*(h|hour|hours)"
    minute_pattern = r"(\d+)\s*(m|min|minute|minutes)"
    second_pattern = r"(\d+)\s*(s|sec|second|seconds)"

    days = 0
    hours = 0
    minutes = 0
    seconds = 0

    time_str = time_str.lower()

    if re.search(day_pattern, time_str):
        days_match = re.search(day_pattern, time_str)
        days = int(days_match.group(1))

    if re.search(hour_pattern, time_str):
        hours_match = re.search(hour_pattern, time_str)
        hours = int(hours_match.group(1))

    if re.search(minute_pattern, time_str):
        minutes_match = re.search(minute_pattern, time_str)
        minutes = int(minutes_match.group(1))

    if re.search(second_pattern, time_str):
        seconds_match = re.search(second_pattern, time_str)
        seconds = int(seconds_match.group(1))

    total_seconds = days * 24 * 3600 + hours * 3600 + minutes * 60 + seconds

    return total_seconds


def is_valid_github_repo_url(url):
    """
    Checks if a given URL is a valid GitHub repository URL.

    Args:
        url (str): The URL to check.

    Returns:
        bool: True if the URL is a valid GitHub repository URL, False otherwise.
    """

    github_repo_pattern = r"^https?://github\.com/[\w-]+/[\w-]+$"

    match = re.match(github_repo_pattern, url)

    return match is not None


async def extract_github_file_content(
    session: aiohttp.ClientSession, github_file_url: str
):
    """
    Extracts the content of a file from a GitHub URL.

    Args:
        session (aiohttp.ClientSession): An aiohttp session.
        github_file_url (str): The URL of the file to extract.

    Returns:
        str | None: The content of the file, or None if the file could not be found.
    """

    async with session.get(github_file_url) as response:
        if response.status == 200:
            return await response.text()
        return None


async def generate_documentation(file_content: str) -> str:
    """
    Generates documentation for a given code in markdown format.

    Args:
        file_content (str): The code to generate documentation for.

    Returns:
        str: The generated documentation.
    """

    prompt = f"Generate documentation for this code in .MD format: ```{file_content}```"
    response = await openai.ChatCompletion.acreate(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
    )
    return response.choices[0].message.content
