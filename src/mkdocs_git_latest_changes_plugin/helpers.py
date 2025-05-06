# SPDX-FileCopyrightText: 2023 Thomas Breitner
#
# SPDX-License-Identifier: MIT

import html
from datetime import datetime
from pathlib import Path
import re


def validate_timestamp_format(value: str) -> str:
    """
    Validate that the timestamp format is valid.
    TODO: there should be a better way
    """
    try:
        # Check if the format string contains at least one valid directive
        if not re.search(r"%[aAwdbBmyYHIpMSfzjUWcxX%]", value):
            raise ValueError(
                f"Format string '{value}' does not contain any valid datetime directives."
            )
        # Try formatting the current time with the given format to catch other errors
        datetime.now().strftime(value)
        return value
    except ValueError as exc:
        raise ValueError(
            f"Invalid timestamp format: '{value}'. Please use a valid datetime format."
        ) from exc


def get_rel_path(*, src_path: str, dest_path: str) -> str:
    # Ensure that the paths are absolute
    src_path_path = Path(src_path).resolve()
    dest_path_path = Path(dest_path).resolve()

    # Get parent directories of both files
    dest_path_dir = dest_path_path.parent
    src_path_dir = src_path_path.parent

    # Check if they're in the same directory
    is_same_dir = dest_path_dir == src_path_dir

    rendered_url = ""
    try:
        # Only try to get relative path if it makes sense
        if is_same_dir:
            rendered_url = dest_path_path.name
        else:
            rendered_url = dest_path_path.relative_to(src_path_dir).as_posix()
    except ValueError:
        pass

    return rendered_url


def get_error_message(error: Exception) -> str:
    template = "An exception of type {0} occurred. Arguments:\n{1!r}"
    msg = template.format(type(error).__name__, error.args)
    return msg


def sanitize_string(string: str) -> str:
    string = string.strip()
    string = html.escape(string)

    # Strip unicode control characters from string:
    # string = "".join(
    #     ch for ch in string if unicodedata.category(ch)[0] != "C"
    # )

    return string
