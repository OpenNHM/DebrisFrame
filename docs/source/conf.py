# Configuration file for the Sphinx documentation builder.

# -- Project information

project = "DebrisFrame"
copyright = "2025, DebrisFrame Team"
author = "DebrisFrame Team"

release = "0.1"
version = "0.1.0"

# -- General configuration

extensions = [
    "sphinx.ext.duration",
    "sphinx.ext.doctest",
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.intersphinx",
]

intersphinx_mapping = {
    "python": ("https://docs.python.org/3/", None),
    "sphinx": ("https://www.sphinx-doc.org/en/master/", None),
}
intersphinx_disabled_domains = ["std"]

templates_path = ["_templates"]

# -- Options for HTML output

html_theme = "sphinx_rtd_theme"

html_theme_options = {
    "logo_only": True,
    "style_nav_header_background": "#343131",
    # 'display_version': False,
}
# The name of an image file (relative to this directory) to place at the top
# of the sidebar.
html_logo = "_static/logo.png"


# -- Options for LaTeX output ---------------------------------------------
latex_logo = "_static/logo.png"

# -- Options for EPUB output
epub_show_urls = "footnote"
