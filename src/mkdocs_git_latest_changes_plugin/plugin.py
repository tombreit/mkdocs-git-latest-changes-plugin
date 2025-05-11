# SPDX-FileCopyrightText: 2023 Thomas Breitner
#
# SPDX-License-Identifier: MIT

"""
MkDocs Plugin plugin that allows you to display a list of recently
modified pages from the Git log.
"""

from typing import Optional, Literal, Any

from mkdocs.plugins import BasePlugin, get_plugin_logger
from mkdocs.structure.files import Files
from mkdocs.structure.pages import Page
from mkdocs.config.defaults import MkDocsConfig
from mkdocs.config.base import Config
from mkdocs.config import config_options
from mkdocs.exceptions import PluginError

from .helpers import validate_timestamp_format
from .git_adapter import get_recent_changes, get_repo_vendor
from .presentation import render_table

log = get_plugin_logger(__name__)


class GitLatestChangesPluginConfig(Config):
    # Processing options
    limit_to_docs_dir = config_options.Type(bool, default=False)
    repo_vendor = config_options.Type(str, default="")
    enabled_on_serve = config_options.Type(bool, default=True)
    history_limit = config_options.Type(int, default=-1)
    timestamp_format = config_options.Type(str, default="%Y-%m-%d %H:%M:%S")

    # Display options
    # If adding new features: update template and feature_headers
    table_features = config_options.Type(
        list,
        # The default should match the behavior of previous versions of this plugin
        default=[
            "file_link_git_repo",
            "timestamp",
            "author",
            "message",
            "commit_hash_link",
        ],
    )

    # Calcuated attribute, not to be set by user
    tracked_dir: str = "."


class GitLatestChangesPlugin(BasePlugin[GitLatestChangesPluginConfig]):
    """
    Mkdocs plugin to render latest changes from Git.
    Reference: https://www.mkdocs.org/user-guide/plugins
    Adjusting program flow for serve/build adapted from, thanks @squidfunk
    https://github.com/squidfunk/mkdocs-material/blob/3e862b5e992e934a033413263f60ab0e95ed209f/src/plugins/info/plugin.py#L54
    """

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self.is_serve = False

    def on_startup(
        self, *, command: Literal["build", "gh-deploy", "serve"], dirty: bool
    ) -> None:
        self.is_serve = command == "serve"

    def on_config(self, config: MkDocsConfig) -> MkDocsConfig:
        if not self.config.enabled_on_serve and self.is_serve:
            log.info(
                "Plugin deactivated during `serve`. Hint: config option `enabled_on_serve`"
            )

        valid_table_features = {
            "filepath",
            "file_link_git_repo",
            "page_path_link",
            "timestamp",
            "author",
            "message",
            "commit_hash_link",
        }

        invalid_table_features = [
            feature
            for feature in self.config.table_features
            if feature not in valid_table_features
        ]

        if invalid_table_features:
            valid_features_str = ", ".join(
                f'"{f}"' for f in sorted(valid_table_features)
            )
            invalid_features_str = ", ".join(f'"{f}"' for f in invalid_table_features)

            raise PluginError(
                f"Invalid table_features: {invalid_features_str}\n"
                f"Valid options are: {valid_features_str}"
            )

        try:
            validate_timestamp_format(self.config.timestamp_format)
        except ValueError as e:
            raise PluginError(f"Invalid timestamp_format: {e}") from e

        self.config.repo_vendor = get_repo_vendor(
            repo_url=config.repo_url or "",
            repo_name=config.repo_name or "",
            repo_vendor=self.config.repo_vendor,
        )

        tracked_dir = self.config.tracked_dir
        if self.config.limit_to_docs_dir:
            log.debug(
                f"Plugin config limit_to_docs_dir enabled: Only take files from {config.docs_dir} into account."
            )
            tracked_dir = str(config.docs_dir)

        self.config.tracked_dir = tracked_dir

        return config

    def on_page_markdown(
        self, markdown: str, /, *, page: Page, config: MkDocsConfig, files: Files
    ) -> Optional[str]:
        """
        Search for the `{{ latest_changes }}` marker in the markdown and replace it
        with the latest changes from the Git log in the form of a markdown formatted table.
        """
        if not self.config.enabled_on_serve and self.is_serve:
            return None

        marker = "{{ latest_changes }}"

        if marker in markdown:
            log.debug(f"Found latest_changes marker in {page.file.src_uri}")

            # 0. Very verbose process flow...

            # 1. Prepare data accessible to the plugin (if not already done in on_config())
            repo_url = config.repo_url or ""  # Make MyPy happy

            # 2. Get the latest changes from the Git log
            git_loginfos, history_limit_hint = get_recent_changes(
                # Top level config options
                repo_url=repo_url,
                # Plugin config options
                repo_vendor=self.config.repo_vendor,
                history_limit=self.config.history_limit,
                limit_to_docs_dir=self.config.tracked_dir,
                latest_changes_page_path=page.file.abs_src_path or "",
            )

            # 3. Render the recent changes as markdown table
            recent_changes_markdown_table = render_table(
                loginfos=git_loginfos,
                table_features=self.config.table_features,
                timestamp_format=self.config.timestamp_format,
                limit_to_docs_dir=self.config.limit_to_docs_dir,
            )

            # 4. Append the history limit hint to the markdown table
            if history_limit_hint:
                recent_changes_markdown_table += f"\n\n{history_limit_hint}"

            # 5. Replace the marker in the markdown with the rendered table
            markdown = markdown.replace(marker, recent_changes_markdown_table)

        return markdown
