# SPDX-FileCopyrightText: 2023 Thomas Breitner
#
# SPDX-License-Identifier: MIT

"""
MkDocs Plugin plugin that allows you to display a list of recently
modified pages from the Git log.
"""


import json
import unicodedata
from operator import itemgetter
from dataclasses import dataclass

from git import Repo
from git.exc import GitCommandError, InvalidGitRepositoryError

from mkdocs.exceptions import PluginError
from mkdocs.plugins import BasePlugin, get_plugin_logger
from mkdocs.structure.files import Files
from mkdocs.structure.pages import Page
from mkdocs.config.defaults import MkDocsConfig
from mkdocs.config.base import Config

from typing import Optional


log = get_plugin_logger(__name__)


@dataclass
class RepoURLs:
    commit_hash_url: str
    filepath_url: str


def get_error_message(error: Exception) -> str:
    template = "An exception of type {0} occurred. Arguments:\n{1!r}"
    msg = template.format(type(error).__name__, error.args)
    return msg


def get_remote_repo_urls(
    *,
    repo_url: str,
    repo_name: str,
    branch: str,
    commit_hash: str,
    commit_hash_short: str,
    filepath: str,
) -> RepoURLs:
    """
    Build URLs for a given git hash, file and a repository as a markdown link. Currently only
    for Github and Gitlab.

    Github:
    repo_url:   https://github.com/<ns>/<project>
    commit_url: https://github.com/<ns>/<project>/commit/<hash>
    file_url:   https://github.com/<ns>/<project>/blob/<branch>/<filepath>

    Gitlab:
    repo_url:   https://gitlab.com/<ns>/<project>
    commit_url: https://gitlab.com/<ns>/<project>/-/commit/<hash>
    file_url:   https://gitlab.com/<ns>/<project>/-/blob/<branch>/<filepath>
    """

    supported_remote_repos = {
        "github": {
            "hash_url_tpl": "[{linktext}]({repo_url}/commit/{commit_hash})",
            "filepath_url_tpl": "[{linktext}]({repo_url}/blob/{branch}/{filepath})",
        },
        "gitlab": {
            "hash_url_tpl": "[{linktext}]({repo_url}/-/commit/{commit_hash})",
            "filepath_url_tpl": "[{linktext}]({repo_url}/-/blob/{branch}/{filepath})",
        },
    }

    repo_name = repo_name.lower()
    # Initialize result dataclass with plain commit_hash and filepath,
    # not formatted as markdown links
    repo_urls = RepoURLs(commit_hash_url=commit_hash, filepath_url=filepath)

    if repo_name not in supported_remote_repos.keys():
        log.warning(
            f"Repository config.repo_name '{repo_name} not supported.\
                    Only '{supported_remote_repos.keys()}' supported. Commit\
                    hashes and filepaths will not be linkified."
        )

    if all([repo_url, repo_name]):
        # Update dataclass with markdown links

        repo_urls.commit_hash_url = supported_remote_repos[repo_name][
            "hash_url_tpl"
        ].format(
            linktext=commit_hash_short,
            commit_hash=commit_hash,
            repo_url=repo_url,
        )
        repo_urls.filepath_url = supported_remote_repos[repo_name][
            "filepath_url_tpl"
        ].format(
            linktext=filepath,
            filepath=filepath,
            repo_url=repo_url,
            branch=branch,
        )

    return repo_urls


def render_table(loginfos: list[dict[str, str]]) -> str:
    """
    Convert list of dicts with git changelog entries to markdown table:

    | filepath                         | timestamp           | hash                      | author   | message            |
    | -------------------------------- | ------------------- | ------------------------- | -------- | ------------------ |
    | [index.md](remote-repo-index.md) | 2023-11-17 14:20:10 | [4401df1](full-hash-link) | John Doe | Fixed typo         |
    | [setup.md](remote-repo-setup.md) | 2023-11-16 12:55:07 | [84b1b0d](full-hash-link) | Jane Roe | Initial setup docs |
    """

    # Build an internal representation with latest changes data
    rows: list[list[str]] = []
    for index, loginfo in enumerate(loginfos):
        if index == 0:
            column_header_row = [column_header for column_header in loginfo.keys()]
            separator_row = [
                "-" * len(column_header) for column_header in column_header_row
            ]
            data_row = [cell for cell in loginfo.values()]
            rows.extend([column_header_row] + [separator_row] + [data_row])
        else:
            data_row = [cell for cell in loginfo.values()]
            rows.append(data_row)

    # Convert the internal representation to markdown table
    markdown_rows: list[str] = []
    col_separator = " | "
    for row in rows:
        markdown_row = f"{col_separator}{col_separator.join(row)}{col_separator}"
        markdown_rows.append(markdown_row)

    markdown_table = "\n".join(markdown_rows)

    return markdown_table


def sanitize(string: str) -> str:
    # log.debug(f"sanitize: `{string}`...")
    # Strip unicode control characters from string:
    sanitized_string = "".join(
        ch for ch in string if unicodedata.category(ch)[0] != "C"
    )

    return str(sanitized_string)


def get_recent_changes(*, repo_url: str, repo_name: str) -> str:
    try:
        repo = Repo()
        branch = repo.active_branch
        git = repo.git
    except InvalidGitRepositoryError as invalid_repo_error:
        msg = get_error_message(invalid_repo_error)
        # Only log a warning to allow running via `--no-strict`
        log.warning(msg)
        return f"Warning: {msg}"
    except Exception as error:
        # Trigger a MkDocs BuildError via raising a PluginError. Causes
        # MkDocs to abort, even if running in no-strict mode.
        msg = get_error_message(error)
        log.warning(msg)
        raise PluginError(msg)
    else:
        log.debug(f"Initialized repo `{repo}`, branch `{branch}`...")
        files = git.ls_files()
        files = files.split("\n")

    loginfos = []
    for file in files:
        log.debug(f"Processing file `{file}`...")

        try:
            loginfo = git.log(
                "-1",
                '--pretty=format:{"Timestamp": "%cd", "hash_short": "%h", "hash_full": "%H", "Author": "%an", "Message": "%s"}',
                "--date=format:%Y-%m-%d %H:%M:%S",
                file,
            )
            loginfo = f"{sanitize(loginfo)}"
            loginfo = json.loads(loginfo)

            repo_urls = get_remote_repo_urls(
                repo_url=repo_url,
                repo_name=repo_name,
                branch=branch,
                commit_hash=loginfo["hash_full"],
                commit_hash_short=loginfo["hash_short"],
                filepath=file,
            )

            # Dictionary insert order defines the result column order
            fileinfo = {"Filepath": repo_urls.filepath_url}
            fileinfo.update(loginfo)
            fileinfo.update({"Commit": repo_urls.commit_hash_url})

            # We do not need the full git hash any more
            del fileinfo["hash_full"]
            del fileinfo["hash_short"]

            loginfos.append(fileinfo)
        except GitCommandError as git_command_error:
            # Only log a warning to allow running via `--no-strict`
            msg = get_error_message(git_command_error)
            log.warning(msg)
        except Exception as error:
            # Trigger a MkDocs BuildError via raising a PluginError. Causes
            # MkDocs to abort, even if running in no-strict mode.
            msg = get_error_message(error)
            log.warning(msg)
            raise PluginError(msg)

    loginfos = sorted(loginfos, key=itemgetter("Timestamp"), reverse=True)

    return render_table(loginfos)


class GitLatestChangesPluginConfig(Config):
    pass


class GitLatestChangesPlugin(BasePlugin[GitLatestChangesPluginConfig]):
    """
    Mkdocs plugin to render latest changes from Git.
    Reference: https://www.mkdocs.org/user-guide/plugins
    """

    def on_page_markdown(
        self, markdown: str, /, *, page: Page, config: MkDocsConfig, files: Files
    ) -> Optional[str]:
        marker = "{{ latest_changes }}"
        if marker in markdown:
            log.debug(f"Found latest_changes marker in {page.file.src_uri}")

            # Make mypy happy
            # Argument "repo_url" to "get_recent_changes" has incompatible type
            # "str | None"; expected "str"  [arg-type]
            repo_url = str(config.repo_url or "")
            repo_name = str(config.repo_name or "")

            latest_changes = get_recent_changes(repo_url=repo_url, repo_name=repo_name)
            markdown = markdown.replace(marker, latest_changes)

        return markdown
