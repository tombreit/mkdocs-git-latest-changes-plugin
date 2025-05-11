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
    *,
    loginfos: List[Loginfo],
    table_features: List[str],
    timestamp_format: str,
    limit_to_docs_dir: bool = False,
) -> str:
    """
    Render markdown table using external Jinja2 template with configurable columns

    Args:
        loginfos: List of Loginfo objects containing change data
        table_features: List of column identifiers controlling table structure
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
        "file_link_git_repo": "File (Git)",
        "page_path_link": "Page" if limit_to_docs_dir else "Page/File",
    }

    context = {
        "loginfos": loginfos,
        "features": table_features,
        "timestamp_format": timestamp_format,
        "column_headers": column_headers,
    }

    template = env.get_template("recent_changes_table.md.j2")
    table_rendered: str = template.render(context).strip()

    return table_rendered
