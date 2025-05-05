# SPDX-FileCopyrightText: 2023 Thomas Breitner
#
# SPDX-License-Identifier: MIT

from typing import List
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from .models import Loginfo


template_dir = Path(__file__).parent / "templates"
env = Environment(loader=FileSystemLoader(template_dir))


def render_table(
    *, loginfos: List[Loginfo], changelog_features: List[str], timestamp_format: str
) -> str:
    """
    Render markdown table using external Jinja2 template with configurable columns

    Args:
        loginfos: List of Loginfo objects containing change data
        changelog_features: List of column identifiers controlling table structure
    """
    if not loginfos:
        return "No recent changes found."

    # Mapping of feature IDs to human-readable column headers
    column_headers = {
        "filepath": "File",
        "timestamp": "Date",
        "commit_hash_link": "Commit",
        "author": "Author",
        "message": "Description",
        "page_link_git_repo": "File (Git)",
        "page_link_rendered": "Page",
    }

    context = {
        "loginfos": loginfos,
        "features": changelog_features,
        "timestamp_format": timestamp_format,
        "column_headers": column_headers,
    }

    template = env.get_template("recent_changes_table.md.j2")
    table_rendered: str = template.render(context).strip()

    return table_rendered
