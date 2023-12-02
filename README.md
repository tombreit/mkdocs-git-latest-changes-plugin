<!--
SPDX-FileCopyrightText: 2023 Thomas Breitner

SPDX-License-Identifier: MIT
-->

# mkdocs-git-latest-changes-plugin

MkDocs plugin that allows you to display a list of recently modified pages from the Git log

[![REUSE status](https://api.reuse.software/badge/github.com/tombreit/mkdocs-git-latest-changes-plugin)](https://api.reuse.software/info/github.com/tombreit/mkdocs-git-latest-changes-plugin)
[![Checked with mypy](https://www.mypy-lang.org/static/mypy_badge.svg)](https://mypy-lang.org/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

## Setup

Install the plugin [PyPI package](https://pypi.org/project/mkdocs-git-latest-changes-plugin/):

```bash
pip install mkdocs-git-latest-changes-plugin
```

Configure `mkdocs.yml`:

```yaml
plugins:
  - git-latest-changes
```

## Demo

https://tombreit.github.io/mkdocs-git-latest-changes-plugin/

## Usage

Use `{{ latest_changes }}` in your Markdown page(s) where the latest git changes should be inserted as a table.

## Hints

- This plugin depends of having any commits in the current branch.
- For linked git commit hashes and filenames, the MkDocs config variable `repo_url` must be set and point to a Github or Gitlab repository.
- Relax warnings with `--no-strict` (via MkDocs [strict configuration](https://www.mkdocs.org/user-guide/configuration/#strict), [cli](https://www.mkdocs.org/user-guide/cli/)), e.g. if a expected file is not in the git working tree.
- Log level: Request debug information for this plugin via MkDocs `--verbose` command line flag.
