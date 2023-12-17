<!--
SPDX-FileCopyrightText: 2023 Thomas Breitner

SPDX-License-Identifier: MIT
-->

# mkdocs-git-latest-changes-plugin

MkDocs plugin that allows you to display a list of recently modified pages from the Git log

- [Repository](https://github.com/tombreit/mkdocs-git-latest-changes-plugin)
- [Issues](https://github.com/tombreit/mkdocs-git-latest-changes-plugin/issues)
- [PyPI package](https://pypi.org/project/mkdocs-git-latest-changes-plugin/)

## Feature

- Get all files of your MkDocs project currently in git with their file path, commit message, commit timestamp, commit hash and author.
- Sort by commit timestamp descending.
- Convert this to a markdown table.
- Substitute the marker string <code>&#123;&#123; latest_changes &#125;&#125;</code> with this markdown table.
- Enjoy your latest changes table rendered by your MkDocs theme.

## Hints

- This plugin depends of having any commits in the current git branch.
- An error will be raised/rendered if no git repository exists.
- For linked git commit hashes and filenames, the MkDocs config variable `repo_url` must be set and point to a Github or Gitlab repository.
- Relax warnings with `--no-strict` (via MkDocs [strict configuration](https://www.mkdocs.org/user-guide/configuration/#strict), [cli](https://www.mkdocs.org/user-guide/cli/)), e.g. if a expected file is not in the git working tree.
- Log level: Request debug information for this plugin via MkDocs `--verbose` command line flag.

## Latest changes demo

### Code

<pre><code># docs_dir/file.md

&#123;&#123; latest_changes &#125;&#125;
</code></pre>

### Rendered

{{ latest_changes }}
