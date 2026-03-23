import importlib.metadata

try:
    __version__ = importlib.metadata.version("roadbook")
except importlib.metadata.PackageNotFoundError:
    # Package is not installed
    __version__ = "unknown"
