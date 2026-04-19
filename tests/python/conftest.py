"""
conftest.py — Pytest configuration for Lumara Python sidecar tests.
"""
import pytest


def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line("markers", "asyncio: mark test as async")
