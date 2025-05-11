# SPDX-FileCopyrightText: 2023 Thomas Breitner
#
# SPDX-License-Identifier: MIT

# The method working_directory() is copied from project timvink/mkdocs-git-authors-plugin
# and licensed under MIT. Thank you timvink.


import re
import os
import html
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
def project(tmp_path, request=None):
    subdir_path = getattr(request, "param", "") if request else ""
    repo_path = tmp_path / "test_repo"
    nested_path = repo_path / subdir_path if subdir_path else repo_path
    nested_path.mkdir(parents=True, exist_ok=True)
    repo = Repo.init(repo_path)

    config_file_path = nested_path / PRROJECT_CONFIG
    config_file_path.write_text(
        "site_name: mkdocs-plugin-test\nrepo_name: github\nplugins:\n  - git-latest-changes"
    )

    docs_dir = nested_path / DOCS_DIR
    docs_dir.mkdir(parents=True, exist_ok=True)

    page_file_path = nested_path / DOCS_DIR / "index.md"
    page_file_path.write_text("# Home")

    # Store nested_path as an attribute of the repo object
    repo.nested_path = nested_path

    yield repo

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

        # The marker `{{ latest_changes }}` should not exist in the generated page
        assert not re.search("{{ latest_changes }}", contents)

        # The commit message should be displayed in the generated <table>
        assert re.search(f"<td>{msg_rendered}</td>", contents)


def test_mkdocs_w_history_limit_config(project: Repo):
    with working_directory(project.working_tree_dir):
        FIRST_COMMIT_MSG = "First commit message"
        SECOND_COMMIT_MSG = "Second commit message"

        config_file_path = Path(PRROJECT_CONFIG)

        # Test if a file not in docs_dir is included in {{ latest_changes }}
        config_file_path.write_text(
            """
site_name: mkdocs-plugin-test
strict: true
plugins:
  - git-latest-changes
        """
        )

        project.index.add([str(config_file_path)])
        project.index.commit(FIRST_COMMIT_MSG)

        latest_changes_file_path = (
            Path(project.working_tree_dir)
            / DOCS_DIR
            / f"{PAGE_W_LATEST_CHANGES_FILENAME}.md"
        )
        latest_changes_file_path.write_text("{{ latest_changes }}")

        project.index.add([str(latest_changes_file_path)])
        project.index.commit(SECOND_COMMIT_MSG)

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
            f"<td>{FIRST_COMMIT_MSG}</td>",
            contents,
        )

        assert re.search(
            f"<td>{SECOND_COMMIT_MSG}</td>",
            contents,
        )

        # New config with history_limit
        config_file_path.write_text(
            """
site_name: mkdocs-plugin-test
strict: true
plugins:
  - git-latest-changes:
      history_limit: 1
        """
        )

        assert run_build(project.working_tree_dir)
        contents = latest_changes_page.read_text()
        assert not re.search(
            f"<td>{FIRST_COMMIT_MSG}</td>",
            contents,
        )


@pytest.mark.parametrize("project", ["", "subdir", "subdir/subsubdir"], indirect=True)
def test_mkdocs_w_git_dir_in_parent_dir_config(project):
    repo = project
    nested_path = repo.nested_path

    with working_directory(repo.working_tree_dir):
        latest_changes_file_path = (
            nested_path / DOCS_DIR / f"{PAGE_W_LATEST_CHANGES_FILENAME}.md"
        )
        latest_changes_file_path.write_text("{{ latest_changes }}")

        repo.index.add([str(latest_changes_file_path)])
        relative_path = nested_path.relative_to(repo.working_tree_dir)
        commit_message = (
            f"Added latest changes page in {relative_path}"
            if str(relative_path) != "."
            else "Added latest changes page in root"
        )
        repo.index.commit(commit_message)
        assert repo.head.is_valid()

        assert run_build(str(nested_path))

        latest_changes_page = (
            nested_path / BUILD_DIR / PAGE_W_LATEST_CHANGES_FILENAME / "index.html"
        )
        assert latest_changes_page.exists(), f"{latest_changes_page} does not exist"

        contents = latest_changes_page.read_text()

        assert "{{ latest_changes }}" not in contents
        assert commit_message in contents


def test_timestamp_format_config(project: Repo):
    """Test that the timestamp_format config option correctly formats timestamps and fails for invalid formats."""
    with working_directory(project.working_tree_dir):
        # Create a page with the latest_changes marker
        latest_changes_file_path = (
            Path(project.working_tree_dir)
            / DOCS_DIR
            / f"{PAGE_W_LATEST_CHANGES_FILENAME}.md"
        )
        latest_changes_file_path.write_text("{{ latest_changes }}")

        # Add file and make a commit
        project.index.add([str(latest_changes_file_path)])
        project.index.commit("Added latest changes page")

        # Test default format
        assert run_build(project.working_tree_dir)
        latest_changes_page = (
            Path(project.working_tree_dir)
            / BUILD_DIR
            / PAGE_W_LATEST_CHANGES_FILENAME
            / "index.html"
        )
        contents = latest_changes_page.read_text()
        # Default format is "%Y-%m-%d %H:%M:%S", e.g., "2023-01-01 12:34:56"
        assert re.search(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}", contents)

        # Test custom format
        config_file_path = Path(PRROJECT_CONFIG)
        config_file_path.write_text("""
site_name: mkdocs-plugin-test
strict: true
plugins:
  - git-latest-changes:
      timestamp_format: "%d.%m.%Y"
        """)

        assert run_build(project.working_tree_dir)
        contents = latest_changes_page.read_text()
        # Should now match custom format, e.g., "01.01.2023"
        assert re.search(r"\d{2}\.\d{2}\.\d{4}", contents)
        assert not re.search(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}", contents)

        # Test invalid format: should fail
        config_file_path.write_text("""
site_name: mkdocs-plugin-test
strict: true
plugins:
  - git-latest-changes:
      timestamp_format: "%invalid%"
        """)

        process = run_build(project.working_tree_dir)
        assert process.returncode != 0


def assert_feature_presence(*, contents, feature, commit_data, config):
    """Assert that a specific feature is present in the HTML output"""
    if feature == "timestamp":
        timestamp_str = (
            f"<td>{commit_data['commit_timestamp']:{config.timestamp_format}}</td>"
        )
        assert timestamp_str in contents, f"Timestamp {timestamp_str} not found"
    elif feature == "author":
        assert (
            f"<td>{commit_data['commit_author_escaped']}</td>" in contents
        ), "Author not found"
    elif feature == "message":
        assert commit_data["commit_msg"] in contents, "Commit message not found"
    elif feature == "commit_hash_link":
        # As we only test a minimal config without a remote repository,
        # the commit hash is not linked.
        hash_short = commit_data["commit_hash_short"]
        assert f"<td>{hash_short}</td>" in contents, "Commit hash not found"
    elif feature == "filepath":
        assert f"<td>{commit_data['filepath']}</td>" in contents, "Filepath not found"
    elif feature == "page_path_link":
        # Too lazy to get the actual relative path
        assert (
            f'<td><a href="./">{commit_data["filepath"]}</a></td>' in contents
        ), "Page path link not found"
    elif feature == "file_link_git_repo":
        # This feature is not tested, makes only sense if a remote repository is set
        pass


@pytest.fixture
def table_features_setup(project):
    """Setup fixture for table_features tests."""
    from mkdocs_git_latest_changes_plugin.plugin import GitLatestChangesPluginConfig

    config = GitLatestChangesPluginConfig()
    config_file_path = Path(PRROJECT_CONFIG)
    commit_message = "Test commit for table features"

    # As we only have one page, on which there is also the latest changes marker
    src_filepath = Path(DOCS_DIR) / f"{PAGE_W_LATEST_CHANGES_FILENAME}.md"
    dest_filepath = Path(BUILD_DIR) / PAGE_W_LATEST_CHANGES_FILENAME / "index.html"

    with working_directory(project.working_tree_dir):
        # Create a page with the latest_changes marker
        latest_changes_file_path = Path(project.working_tree_dir) / src_filepath
        latest_changes_file_path.write_text("{{ latest_changes }}")

        # Add file and make a commit
        project.index.add([str(latest_changes_file_path)])
        project.index.commit(commit_message)

        commit_timestamp = project.head.commit.committed_datetime
        commit_author = project.head.commit.author.name
        commit_author_escaped = html.escape(commit_author)
        commit_hash_short = project.head.commit.hexsha[:7]

    return {
        "config": config,
        "config_file_path": config_file_path,
        "commit_data": {
            "commit_timestamp": commit_timestamp,
            "commit_author_escaped": commit_author_escaped,
            "commit_msg": commit_message,
            "commit_hash_short": commit_hash_short,
            "filepath": str(src_filepath),
            "file_link_git_repo": str(src_filepath),
            "page_path_link": str(dest_filepath),
        },
        "src_filepath": src_filepath,
        "dest_filepath": dest_filepath,
    }


def test_table_features_default_config(project, table_features_setup):
    """Test table features with default configuration."""
    setup = table_features_setup

    with working_directory(project.working_tree_dir):
        assert run_build(project.working_tree_dir)
        latest_changes_page = Path(project.working_tree_dir) / setup["dest_filepath"]
        contents = latest_changes_page.read_text()

        # Check all default features
        for feature in setup["config"].table_features:
            assert_feature_presence(
                contents=contents,
                feature=feature,
                commit_data=setup["commit_data"],
                config=setup["config"],
            )


def test_table_features_all_features(project, table_features_setup):
    """Test table features with all valid features explicitly configured."""
    setup = table_features_setup

    with working_directory(project.working_tree_dir):
        # Configure all valid features
        setup["config_file_path"].write_text("""
site_name: mkdocs-plugin-test
strict: true
plugins:
  - git-latest-changes:
      table_features:
        - filepath
        - file_link_git_repo
        - page_path_link
        - timestamp
        - author
        - message
        - commit_hash_link
        """)

        assert run_build(project.working_tree_dir)
        latest_changes_page = Path(project.working_tree_dir) / setup["dest_filepath"]
        contents = latest_changes_page.read_text()

        # Check all features are present
        all_features = [
            "filepath",
            "file_link_git_repo",
            "page_path_link",
            "timestamp",
            "author",
            "message",
            "commit_hash_link",
        ]

        for feature in all_features:
            assert_feature_presence(
                contents=contents,
                feature=feature,
                commit_data=setup["commit_data"],
                config=setup["config"],
            )


def test_table_features_invalid_config(project, table_features_setup):
    """Test table features with invalid features (should fail)."""
    setup = table_features_setup

    with working_directory(project.working_tree_dir):
        # Configure with invalid features
        setup["config_file_path"].write_text("""
site_name: mkdocs-plugin-test
strict: true
plugins:
  - git-latest-changes:
      table_features:
        - invalid_feature
        - another_invalid
        """)

        process = run_build(project.working_tree_dir)
        assert process.returncode != 0
