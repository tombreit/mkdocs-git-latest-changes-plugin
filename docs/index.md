<!--
SPDX-FileCopyrightText: 2023 Thomas Breitner

SPDX-License-Identifier: MIT
-->

# mkdocs-git-latest-changes-plugin

MkDocs plugin that allows you to display a list of recently modified pages from the Git log

- [Repository](https://github.com/tombreit/mkdocs-git-latest-changes-plugin)
- [Issues](https://github.com/tombreit/mkdocs-git-latest-changes-plugin/issues)
- [PyPI package](https://pypi.org/project/mkdocs-git-latest-changes-plugin/)

## Features

- Get all files of your MkDocs project currently in git with their file path, commit message, commit timestamp, commit hash and author.
- Sort by commit timestamp descending.
- Convert this to a markdown table.
- Substitute the marker string <code>&#123;&#123; latest_changes &#125;&#125;</code> with this markdown table.
- Enjoy your latest changes table rendered by your MkDocs theme.

## Configuration

```yaml
# mkdocs.yml plugin configuration example
plugins:
  - git-latest-changes:
      limit_to_docs_dir: True
      repo_vendor: gitea
      enabled_on_serve: True
      history_limit: 5
      timestamp_format: "%Y-%m-%d %H:%M"
      table_features:
        - "page_path_link"
        - "timestamp"
        - "author"
        - "message"
```

- `limit_to_docs_dir`

    Limit <code>&#123;&#123; latest_changes &#125;&#125;</code> to your pages in your `docs_dir` and exclude the git history information for other files from your project repository via plugin config `limit_to_docs_dir`.  
    Boolean, defaults to `False`.

- `repo_vendor`

    Set the "vendor" of your remote repository (currently supported: `bitbucket`, `github`, `gitlab` and `gitea`) via `repo_vendor` to get linkified commit hashes and filepaths. If not set, `repo_name` is used.

- `enabled_on_serve`

    Not amused by slow builds during `serve` while developing your docs? Disable this plugin only when running MkDocs via `mkdocs serve` and only trigger this plugins functionality on builds (`mkdocs build`).  
    Boolean, defaults to `True`.

- `history_limit`

    Not interested in all the old commits? Limit the table of recent changes using `history_limit = N`. `N` should be a positive integer, negative values or zero disables this option.  
    Integer, defaults to `-1`.

- `timestamp_format`

    Format of the timestamp in the generated recent changes table.  
    String, defaults to `%Y-%m-%d %H:%M:%S`.

- `table_features`

    The "table_features" define the columns and their order.  
    Available features:

<div style="margin-left: 24px;">

```yaml
- "filepath"
- "file_link_git_repo"
- "page_path_link"
- "timestamp"
- "author"
- "message"
- "commit_hash_link"
```

List, defaults to:

```yaml
- "file_link_git_repo"
- "timestamp"
- "author"
- "message"
- "commit_hash_link"
```

</div>

## Hints

- This plugin depends of having any commits in the current git branch.
- An error will be raised/rendered if no git repository exists.
- For linked git commit hashes and filenames, the [MkDocs config variable `repo_url`](https://www.mkdocs.org/user-guide/configuration/#repo_url) must be set and point your repository.
- Relax warnings with `--no-strict` (via MkDocs [strict configuration](https://www.mkdocs.org/user-guide/configuration/#strict), [cli](https://www.mkdocs.org/user-guide/cli/)), e.g. if a expected file is not in the git working tree.
- Log level: Request debug information for this plugin via MkDocs `--verbose / -v` command line flag.
- If you want to spare your audience git and the technical aspects of your repo: Configure your recent changes table e.g. via:

<div style="margin-left: 24px;">

```yaml
  - git-latest-changes:
      limit_to_docs_dir: True
      timestamp_format: "%Y-%m-%d %H:%M"
      table_features:
        - "page_path_link"
        - "timestamp"
        - "author"
        - "message"
```

</div>

## CI/CD

Use in a CI environment may require some tweaking and fixes situations where the git history is not available (e.g. `"HEAD is a detached symbolic reference as it points to <commit hash>`):

```yaml
# GitLab / .gitlab-ci.yml
job:
  script:
    # Returning to branch from detached HEAD
    - git switch $CI_COMMIT_REF_NAME
    - <your CI script>
  variables:
    GIT_DEPTH: 0         # [1]
    GIT_STRATEGY: clone  # [2]
```

<small markdown>

- [1] <https://docs.gitlab.com/ee/ci/runners/configure_runners.html#shallow-cloning>
- [2] <https://docs.gitlab.com/ee/ci/runners/configure_runners.html#git-strategy>

</small>

## Latest changes demo

### Code

<pre><code># docs_dir/file.md

&#123;&#123; latest_changes &#125;&#125;
</code></pre>

### Rendered

{{ latest_changes }}
