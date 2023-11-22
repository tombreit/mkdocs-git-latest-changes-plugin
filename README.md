# mkdocs-git-latest-changes-plugin

MkDocs plugin that allows you to display a list of recently modified pages from the Git log

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
- Log level: Request debug information for this plugin via MkDocs `--verbose` command line flag.
