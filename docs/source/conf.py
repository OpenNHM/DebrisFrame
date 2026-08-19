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
    "sphinx.ext.autosectionlabel",
    "sphinxcontrib.bibtex",
]

bibtex_bibfiles = ["references_all.bib"]

intersphinx_mapping = {
    "python": ("https://docs.python.org/3/", None),
    "sphinx": ("https://www.sphinx-doc.org/en/master/", None),
}
intersphinx_disabled_domains = ["std"]

templates_path = ["_templates"]

# make referencing unique if the same section heading exists doubly
autosectionlabel_prefix_document = True
autosectionlabel_maxdepth = 4

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

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ["_static"]


# -- Options for LaTeX output ---------------------------------------------
latex_logo = "_static/logo.png"

# -- Options for EPUB output
epub_show_urls = "footnote"

# -- Options for referencing -------------------------------------------
numfig = True
math_numfig = True
math_eqref_format = "Eq.{number}"


def setup(app):
    app.add_css_file("css/custom.css")