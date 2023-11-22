"""
MkDocs Plugin
"""

import json
import unicodedata
from operator import itemgetter
from pathlib import Path

from git import Repo, Git

from mkdocs.plugins import BasePlugin, get_plugin_logger
from mkdocs.config import config_options
from mkdocs.structure.pages import Page
from mkdocs.exceptions import PluginError


log = get_plugin_logger(__name__)


def get_remote_repo_url(repo_url, repo_name, branch, commit_hash=None, filepath=None):
    """
    Build URL for a given git hash or file and a repository. Currently only
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

    if not all([repo_url, repo_name]):
        return ""

    repo_name = repo_name.lower()

    supported_remote_repos = {
        "github": {
            "commit_spacer": "/commit/",
            "file_spacer": f"/blob/{branch}/",
        },
        "gitlab": {
            "commit_spacer": "/-/commit/",
            "file_spacer": f"/-/blob/{branch}/",
        }
    }

    if repo_name not in supported_remote_repos.keys():
        return

    if commit_hash:
        repo_url = f"{repo_url}{supported_remote_repos[repo_name]['commit_spacer']}{commit_hash}"
    elif filepath:
        repo_url = f"{repo_url}{supported_remote_repos[repo_name]['file_spacer']}{filepath}"

    return repo_url


def render_table(loginfos: list[dict]) -> str:
    """
    Convert list of dicts with git changelog entries to markdown table: 

    | filepath                         | timestamp           | hash                      | author   | message            |
    | -------------------------------- | ------------------- | ------------------------- | -------- | ------------------ |
    | [index.md](remote-repo-index.md) | 2023-11-17 14:20:10 | [4401df1](full-hash-link) | John Doe | Fixed typo         |
    | [setup.md](remote-repo-setup.md) | 2023-11-16 12:55:07 | [84b1b0d](full-hash-link) | Jane Roe | Initial setup docs |
    """

    # Build an internal representation with latest changes data
    rows: list = []
    for index, loginfo in enumerate(loginfos):
        if index == 0:
            column_header_row = [column_header for column_header in loginfo.keys()]
            separator_row = ['-' * len(column_header) for column_header in column_header_row]
            data_row = [cell for cell in loginfo.values()]
            rows.extend([column_header_row] + [separator_row] + [data_row])
        else:
            data_row = [cell for cell in loginfo.values()]
            rows.append(data_row)

    # Convert the internal representation to markdown table
    markdown_rows: list = []
    col_separator = " | "
    for row in rows:
        markdown_row = f"{col_separator}{col_separator.join(row)}{col_separator}"
        markdown_rows.append(markdown_row)
    
    markdown_table = "\n".join(markdown_rows)

    return markdown_table


def sanitize(string: str) -> str:
    # log.debug(f"sanitize: `{string}`...")
    # Strip unicode control characters from string:
    sanitized_string = "".join(ch for ch in string if unicodedata.category(ch)[0]!="C")

    return str(sanitized_string)


def get_recent_changes(*, repo_url, repo_name):
    repo = Repo(Path.cwd())
    branch = repo.active_branch
    g = Git(repo)
    g.init()

    log.debug(f"Initialized repo `{repo}`, branch `{branch}`...")
    
    files = g.ls_files()
    files = files.split("\n")

    loginfos = []
    for file in files:
        log.debug(f"Processing file `{file}`...")

        try:
            loginfo = g.log(
                "-1",
                '--pretty=format:{"Timestamp": "%cd", "Hash": "%h", "hash_full": "%H", "Author": "%an", "Message": "%s"}',
                "--date=format:%Y-%m-%d %H:%M:%S",
                file
            )
            loginfo = f"{sanitize(loginfo)}"
            loginfo = json.loads(loginfo)

            repo_commit_url = get_remote_repo_url(repo_url, repo_name, branch, commit_hash=loginfo['hash_full'])
            repo_file_url = get_remote_repo_url(repo_url, repo_name, branch, filepath=file)
            
            # Dictionary insert order defines the result column order
            fileinfo = {
                "Filepath": f"[{file}]({repo_file_url})" if repo_file_url else f"{file}"
            }
            fileinfo.update(loginfo)
            fileinfo.update({
                "Hash": f"[{loginfo['Hash']}]({repo_commit_url})" if repo_commit_url else f"{loginfo['Hash']}",
            })

            # We do not need the full git hash any more
            del fileinfo['hash_full']
            loginfos.append(fileinfo)
        except Exception as error:
            msg = f"Exception while trying to get git loginfo: {error}"
            # raise PluginError(msg)
            log.info(msg)
            pass
    
    loginfos = sorted(loginfos, key=itemgetter('Timestamp'), reverse=True)
    return render_table(loginfos)


class GitLatestChangesPlugin(BasePlugin):
    """
    Mkdocs plugin to render latest changes from Git.
    Reference: https://www.mkdocs.org/user-guide/plugins
    """
 
    def on_page_markdown(
        self, markdown: str, page: Page, config, **kwargs
    ) -> str:

        marker = "{{ latest_changes }}"
        if marker in markdown:
            log.debug(f"Found latest_changes marker in {page.file.src_uri}")
            latest_changes = get_recent_changes(repo_url=config.repo_url, repo_name=config.repo_name)
            markdown = markdown.replace(marker, latest_changes)

        return markdown
