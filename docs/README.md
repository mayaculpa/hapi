# Readme

This document describes how to build and contribute to HAPI's documentation.

We use Sphinx and reStructured Text for our documentation. Read the Docs is used for generating and hosting the documentation publicly. We use the [Read the Docs Sphinx Theme](https://docs.readthedocs.io/en/latest/theme.html) for local builds.

## Building documentation
1. Install `pip`
2. Run `pip install sphinx sphinx-autobuild sphinx_rtd_theme`
3. Within the `docs` directory run `sphinx-autobuild . _build`
  * This will automatically rebuild the docs when you make a change.
  * You can preview the changes at `http://localhost:8000/`. This is useful for checking formatting issues.

Read more: http://www.sphinx-doc.org/en/stable/install.html
