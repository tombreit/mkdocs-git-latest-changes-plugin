<!--
SPDX-FileCopyrightText: 2023 Thomas Breitner

SPDX-License-Identifier: MIT
-->

# mkdocs-git-latest-changes-plugin

MkDocs plugin that allows you to display a list of recently modified pages from the Git log

[![PyPI - Version](https://img.shields.io/pypi/v/mkdocs-git-latest-changes-plugin?color=rgb(17%2C%20148%2C%20223)&link=https%3A%2F%2Fpypi.org%2Fproject%2Fmkdocs-git-latest-changes-plugin%2F)](https://pypi.org/project/mkdocs-git-latest-changes-plugin/)
[![REUSE status](https://api.reuse.software/badge/github.com/tombreit/mkdocs-git-latest-changes-plugin)](https://api.reuse.software/info/github.com/tombreit/mkdocs-git-latest-changes-plugin)
[![Checked with mypy](https://www.mypy-lang.org/static/mypy_badge.svg)](https://mypy-lang.org/)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
![pre-commit enabled](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white)

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
