# mkdocs-git-latest-changes-plugin

## Setup

Install the plugin:

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

This plugin depends of having any commits in the current branch.

### Log level

Request debug information for this plugin via MkDocs `--verbose` command line flag.
