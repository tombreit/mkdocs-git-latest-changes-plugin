# SPDX-FileCopyrightText: 2023 Thomas Breitner
#
# SPDX-License-Identifier: MIT

from datetime import datetime
from operator import attrgetter

from mkdocs.plugins import get_plugin_logger
from mkdocs.exceptions import PluginError

from git import Repo
from git.exc import GitCommandError, InvalidGitRepositoryError

from .helpers import get_error_message, sanitize_string
from .models import Loginfo  # SUPPORTED_REMOTE_REPOS

log = get_plugin_logger(__name__)


# def get_repo_vendor(
#     *, repo_url: str | None, repo_name: str | None, repo_vendor_configured: str
# ) -> str:
#     """
#     Figure out the repo_vendor (eg. bitbucket, github, gitlab, gitea)
#     """
#     repo_vendor = ""

#     if not repo_url:
#         log.info(
#             "No repo_url given. Commit hashes and filepaths will not be linkified."
#         )

#     if not repo_name:
#         log.info(
#             "No repo_name given. Commit hashes and filepaths will not be linkified."
#         )

#     repo_vendor_discovered = repo_name.lower()
#     repo_vendor_configured = repo_vendor_configured.lower()

#     if repo_vendor_discovered and repo_vendor_configured:
#         if repo_vendor_configured != repo_vendor_discovered:
#             log.warning(
#                 f"Configured remote repo_vendor `{repo_vendor_configured}` differes from discovered repo_vendor `{repo_vendor_discovered}`. Using configured repo_vendor `{repo_vendor_configured}`."
#             )
#         repo_vendor = repo_vendor_configured
#     elif repo_vendor_discovered and not repo_vendor_configured:
#         log.debug(
#             f"Remote repo_vendor not specified (see config `repo_vendor`), using `{repo_vendor_discovered}`."
#         )
#         repo_vendor = repo_vendor_discovered
#     elif not repo_vendor_discovered and repo_vendor_configured:
#         repo_vendor = repo_vendor_configured

#     # Unsetting not supported repo_vendor
#     if repo_vendor and repo_vendor not in SUPPORTED_REMOTE_REPOS:
#         log.info(
#             f"Repository config.repo_vendor '{repo_vendor}' not supported. Only '{', '.join(SUPPORTED_REMOTE_REPOS.keys())}' supported. Commit hashes and filepaths will not be linkified."
#         )
#         repo_vendor = ""

#     return repo_vendor


def get_recent_changes(
    *,
    repo_url: str,
    repo_vendor: str,
    history_limit: int,
    limit_to_docs_dir: str,
    latest_changes_page_path: str,
) -> tuple[list["Loginfo"], str]:
    # Custom separator character for git log output
    SEP_HEX = "%x00"
    SEP_UNICODE = "\000"

    try:
        repo = Repo(search_parent_directories=True)
        branch = repo.active_branch
        git = repo.git
    except InvalidGitRepositoryError as invalid_repo_error:
        msg = get_error_message(invalid_repo_error)
        # Only log a warning to allow running via `--no-strict`
        log.warning(msg)
        # TODO: fix this str return, breaks MyPy return statement signature
        # return f"Warning: {msg}"
    except Exception as error:
        # Trigger a MkDocs BuildError via raising a PluginError. Causes
        # MkDocs to abort, even if running in no-strict mode.
        msg = get_error_message(error)
        log.warning(msg)
        raise PluginError(msg) from error
    else:
        log.debug(f"Initialized repo `{repo}`, branch `{branch}`...")
        files = git.ls_files(limit_to_docs_dir)
        files = files.split("\n")

    log.info(f"{len(files)} files found in git index and working tree.")

    # git log placeholders:
    # https://git-scm.com/docs/pretty-formats
    # The sequence must map to the list index in the loginfo dict
    # [0]: %cd : commiter date
    # [1]: %h  : abbreviated commit hash
    # [2]: %H  : full commit hash
    # [3]: %an : author name
    # [4]: %s  : subject
    git_log_format = f"%cd{SEP_HEX}%h{SEP_HEX}%H{SEP_HEX}%an{SEP_HEX}%s"

    loginfos = []
    for file in files:
        log.debug(f"Processing file `{file}`...")

        try:
            loginfo_raw = git.log(
                # Limit the number of commits to output; short form would be "-1"
                "--max-count=1",
                f"--pretty=format:{git_log_format}",
                "--date=iso8601-strict-local",
                file,
            )

            loginfo_safe = [
                sanitize_string(loginfo) for loginfo in loginfo_raw.split(SEP_UNICODE)
            ]

            timestamp_obj = datetime.fromisoformat(loginfo_safe[0])

            loginfo = Loginfo(
                filepath=file,
                timestamp=timestamp_obj,
                hash_short=loginfo_safe[1],
                hash_full=loginfo_safe[2],
                author=loginfo_safe[3],
                message=loginfo_safe[4],
                latest_changes_page_path=latest_changes_page_path,
                repo_vendor=repo_vendor,
                repo_url=repo_url,
                branch=branch,
            )
            loginfos.append(loginfo)

        except GitCommandError as git_command_error:
            # Only log a warning to allow running via `--no-strict`
            msg = get_error_message(git_command_error)
            log.warning(msg)
        except IndexError as index_error:
            msg = get_error_message(index_error)
            log.warning(f"{msg}. Possible cause: file {file} not commited yet.")
        except Exception as error:
            # Trigger a MkDocs BuildError via raising a PluginError. Causes
            # MkDocs to abort, even if running in no-strict mode.
            msg = get_error_message(error)
            log.warning(msg)
            raise PluginError(msg) from error

    loginfos = sorted(loginfos, key=attrgetter("timestamp"), reverse=True)

    # Only use this loginfo object if not excluded via history_limit
    # TODO: do not event create this loginfo object if not needed
    history_limit = history_limit if history_limit > 0 else False
    log.debug(f"history_limit set: {history_limit}.")

    history_limit_hint = ""
    if history_limit and len(loginfos) > history_limit:
        loginfos = loginfos[:history_limit]

        _pluralized_string = (
            "entry is" if history_limit == 1 else f"{history_limit} entries are"
        )
        _style = "margin-bottom: 1em; margin-top: 1em; padding-top: .5em; font-style: italic; font-size: smaller;"
        history_limit_hint = f'\n\n<p style="{_style}">Only the most recent {_pluralized_string} displayed.</p>\n\n'

    return (loginfos, history_limit_hint)
