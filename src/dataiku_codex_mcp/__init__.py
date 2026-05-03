"""Dataiku DSS Copilot MCP server package."""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("dataiku-dss-copilot")
except PackageNotFoundError:
    __version__ = "0.0.0"

