from .database import Database

import re


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
