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

## Demo & Docs

<https://tombreit.github.io/mkdocs-git-latest-changes-plugin/>

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

## Usage

Use `{{ latest_changes }}` in your Markdown page(s) where the latest git changes should be inserted as a table.

### Configuration

<https://tombreit.github.io/mkdocs-git-latest-changes-plugin/#configuration>

## Development

```bash
pip install -e .[dev]
```
