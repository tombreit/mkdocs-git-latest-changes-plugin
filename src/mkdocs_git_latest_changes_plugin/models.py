# SPDX-FileCopyrightText: Thomas Breitner
#
# SPDX-License-Identifier: MIT


from datetime import datetime
from dataclasses import dataclass

from .helpers import get_rel_path


SUPPORTED_REMOTE_REPOS = {
    # Github:
    # repo_url:   https://<repo_url>/<ns>/<project>
    # commit_url: https://<repo_url>/<ns>/<project>/commit/<hash>
    # file_url:   https://<repo_url>/<ns>/<project>/blob/<branch>/<filepath>
    # Gitlab:
    # repo_url:   https://<repo_url>/<ns>/<project>
    # commit_url: https://<repo_url>/<ns>/<project>/-/commit/<hash>
    # file_url:   https://<repo_url>/<ns>/<project>/-/blob/<branch>/<filepath>
    # Gitea:
    # repo_url:   https://<repo_url>/<ns>/<project>
    # commit_url: https://<repo_url>/<ns>/<project>/commit/<hash>
    # file_url:   https://<repo_url>/<ns>/<project>/src/branch/<branch>/<filepath>
    # Bitbucket:
    # repo_url:   https://<repo_url>/projects/<ns>/repos/<project>
    # commit_url: https://<repo_url>/projects/<ns>/repos/<project>/commits/<hash>
    # file_url:   https://<repo_url>/projects/<ns>/repos/<project>/browse/<filepath>?at=<branch>
    "github": {
        "hash_url_tpl": "{repo_url}/commit/{commit_hash}",
        "file_remote_url_tpl": "{repo_url}/blob/{branch}/{filepath}",
    },
    "gitlab": {
        "hash_url_tpl": "{repo_url}/-/commit/{commit_hash}",
        "file_remote_url_tpl": "{repo_url}/-/blob/{branch}/{filepath}",
    },
    "gitea": {
        "hash_url_tpl": "{repo_url}/commit/{commit_hash}",
        "file_remote_url_tpl": "{repo_url}/src/branch/{branch}/{filepath}",
    },
    "bitbucket": {
        "hash_url_tpl": "{repo_url}/commits/{commit_hash}",
        "file_remote_url_tpl": "{repo_url}/browse/{filepath}?at={branch}",
    },
}


@dataclass
class Loginfo:
    """
    Dataclass to hold the git log information to be passed to the template.
    """

    filepath: str
    timestamp: datetime
    author: str
    message: str
    hash_short: str
    hash_full: str
    repo_url: str
    latest_changes_page_path: str
    repo_vendor: str
    branch: str

    def _get_remote_url(self, url_type: str) -> str:
        templates = SUPPORTED_REMOTE_REPOS.get(self.repo_vendor, {})
        url_template = templates.get(url_type, "")

        if self.repo_url:
            return url_template.format(
                filepath=self.filepath,
                repo_url=self.repo_url,
                commit_hash=self.hash_full,
                branch=self.branch,
            )

        return ""

    @property
    def get_hash_url(self) -> str:
        """Generate commit hash URL"""
        return self._get_remote_url("hash_url_tpl")

    @property
    def get_file_remote_url(self) -> str:
        """Generate remote file URL"""
        return self._get_remote_url("file_remote_url_tpl")

    @property
    def get_file_local_url(self) -> str:
        """Generate local file URL"""
        rel_path = get_rel_path(
            src_path=self.latest_changes_page_path, dest_path=self.filepath
        )
        return rel_path
