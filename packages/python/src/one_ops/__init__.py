"""1ops by OceanSoft.io."""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("1ops")
except PackageNotFoundError:  # running from a source checkout
    __version__ = "0.0.0+source"
