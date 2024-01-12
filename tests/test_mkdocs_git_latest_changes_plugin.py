# SPDX-FileCopyrightText: 2023 Thomas Breitner
#
# SPDX-License-Identifier: MIT

# The method working_directory is copied from project timvink/mkdocs-git-authors-plugin
# and licensed under MIT. Thank you timvink.


import re
import os
import shutil
import subprocess

from contextlib import contextmanager
from pathlib import Path

import pytest
from git import Repo


DOCS_DIR = "docs"
BUILD_DIR = "site"
PRROJECT_CONFIG = "mkdocs.yml"
PAGE_W_LATEST_CHANGES_FILENAME = "latest-changes"


@contextmanager
def working_directory(path):
    """
    Temporarily change working directory.
    A context manager which changes the working directory to the given
    path, and then changes it back to its previous value on exit.
    Usage:
    ```python
    # Do something in original directory
    with working_directory('/my/new/path'):
        # Do something in new directory
    # Back to old directory
    ```
    """
    prev_cwd = os.getcwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(prev_cwd)


@pytest.fixture
def project(tmp_path):
    # Create a temporary directory for the Git repository
    repo_path = tmp_path / "test_repo"
    repo_path.mkdir()
    repo = Repo.init(repo_path)

    # Bootstrap mkdocs project
    config_file_path = repo_path / PRROJECT_CONFIG
    config_file_path.write_text(
        "site_name: mkdocs-plugin-test\nrepo_name: github\nplugins:\n  - git-latest-changes"
    )

    docs_dir = repo_path / DOCS_DIR
    docs_dir.mkdir(parents=True, exist_ok=True)

    page_file_path = repo_path / DOCS_DIR / "index.md"
    page_file_path.write_text("# Home")

    # Yield the repository object to the tests
    yield repo

    # Clean up: Delete the temporary repository after the test
    repo.close()
    shutil.rmtree(repo_path)


def run_build(dir) -> subprocess.CompletedProcess[bytes]:
    with working_directory(dir):
        return subprocess.run(["mkdocs", "build", "--strict"])


def test_mkdocs_wo_latest_changes_marker_build(project: Repo):
    # Test an unsuspicious build
    with working_directory(project.working_tree_dir):
        assert run_build(project.working_tree_dir)


def test_mkdocs_w_limit_to_docs_dir_config(project: Repo):
    with working_directory(project.working_tree_dir):
        config_file_path = Path(PRROJECT_CONFIG)

        # Test if a file not in docs_dir is included in {{ latest_changes }}
        config_file_path.write_text(
            """
site_name: mkdocs-plugin-test
strict: true
plugins:
  - git-latest-changes:
      limit_to_docs_dir: False
        """
        )

        project.index.add([str(config_file_path)])
        project.index.commit("Set plugin config to include all files from git ls-files")

        latest_changes_file_path = (
            Path(project.working_tree_dir)
            / DOCS_DIR
            / f"{PAGE_W_LATEST_CHANGES_FILENAME}.md"
        )
        latest_changes_file_path.write_text("{{ latest_changes }}")

        project.index.add([str(latest_changes_file_path)])
        project.index.commit("Added latest changes page")

        assert run_build(project.working_tree_dir)

        latest_changes_page = (
            Path(project.working_tree_dir)
            / BUILD_DIR
            / PAGE_W_LATEST_CHANGES_FILENAME
            / "index.html"
        )
        assert latest_changes_page.exists()

        contents = latest_changes_page.read_text()
        assert re.search(
            "<td>Set plugin config to include all files from git ls-files</td>",
            contents,
        )

        # Test if a file not in docs_dir is not included in {{ latest_changes }}
        config_file_path.write_text(
            """
site_name: mkdocs-plugin-test
strict: true
plugins:
  - git-latest-changes:
      limit_to_docs_dir: True
        """
        )

        assert run_build(project.working_tree_dir)
        contents = latest_changes_page.read_text()
        assert not re.search(
            "<td>Set plugin config to include all files from git ls-files</td>",
            contents,
        )


@pytest.mark.parametrize(
    "msg,msg_rendered",
    [
        pytest.param(
            "Added latest changes page",
            "Added latest changes page",
            id="simple_message",
        ),
        pytest.param(
            "This commit message contains <html>",
            "This commit message contains &lt;html&gt;",
            id="message_w_html",
        ),
        pytest.param(
            'This commit message contains "double quotes"',
            "This commit message contains &quot;double quotes&quot;",
            id="message_w_double_quotes",
        ),
        pytest.param(
            r"This commit message contains a \t tab character",
            r"This commit message contains a \\t tab character",
            id="message_w_tab_char",
        ),
        pytest.param(
            r"This commit message contains a \h newline character",
            r"This commit message contains a \\h newline character",
            id="message_w_newline_char",
        ),
    ],
)
def test_commit_message_conversion(project: Repo, msg: str, msg_rendered: str) -> None:
    with working_directory(project.working_tree_dir):
        latest_changes_file_path = (
            Path(project.working_tree_dir)
            / DOCS_DIR
            / f"{PAGE_W_LATEST_CHANGES_FILENAME}.md"
        )
        latest_changes_file_path.write_text("{{ latest_changes }}")

        project.index.add([str(latest_changes_file_path)])
        project.index.commit(msg)
        assert project.head.is_valid()

        assert run_build(project.working_tree_dir)

        latest_changes_page = (
            Path(project.working_tree_dir)
            / BUILD_DIR
            / PAGE_W_LATEST_CHANGES_FILENAME
            / "index.html"
        )
        assert latest_changes_page.exists(), "%s does not exist" % latest_changes_page

        contents = latest_changes_page.read_text()
        # print(f"{contents=}")

        # The marker `{{ latest_changes }}` should not exist in the generated page
        assert not re.search("{{ latest_changes }}", contents)

        # The commit message should be displayed in the generated <table>
        assert re.search(f"<td>{msg_rendered}</td>", contents)
