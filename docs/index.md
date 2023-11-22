# mkdocs-git-latest-changes-plugin

MkDocs plugin that allows you to display a list of recently modified pages from the Git log

- [Repository](https://github.com/tombreit/mkdocs-git-latest-changes-plugin)
- [Issues](https://github.com/tombreit/mkdocs-git-latest-changes-plugin/issues)

## Hints

- This plugin depends of having any commits in the current branch.
- For linked git commit hashes and filenames, the MkDocs config variable `repo_url` must be set and point to a Github or Gitlab repository.
- Log level: Request debug information for this plugin via MkDocs `--verbose` command line flag.

## Latest changes demo

### Code

    # docs_dir/file.md

    {{ latest changes }}

### Rendered

{{ latest_changes }}
