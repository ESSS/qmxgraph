# -- Project information -----------------------------------------------------
project = ""
copyright = "2017, ESSS"
author = "ESSS"
version = ""
release = ""
source_suffix = ".rst"
html_theme = "sphinx_rtd_theme"
master_doc = "index"
language = None
pygments_style = "sphinx"
# html_static_path = ["_static"]  # Logo and other static files used on the docs.
html_sidebars = {"**": ["about.html", "navigation.html", "searchbox.html"]}
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
]

autodoc_default_flags = ['members']
autosummary_generate = True
import os
import sys
sys.path.insert(0, os.path.abspath('../qmxgraph'))
