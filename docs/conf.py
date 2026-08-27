import importlib.metadata

project = "carreralib"
copyright = "2015-2026 Thomas Kemmer"
release = importlib.metadata.version(project)
version = ".".join(release.split(".")[:2])

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.coverage",
    "sphinx.ext.doctest",
    "sphinx.ext.todo",
]
exclude_patterns = ["_build"]
master_doc = "index"
html_theme = "classic"
intersphinx_mapping = {"python": ("https://docs.python.org/3", None)}
