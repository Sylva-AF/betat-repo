import pytest


@pytest.fixture(autouse=True)
def _reset_installer_cache():
    """BetatConfiguredMiddleware caches CommunityConfig existence at module
    level for production performance (see its docstring) — reset before and
    after every test so one test's CommunityConfig doesn't leak into the
    next within the same pytest process."""
    from betat_community.bundledui import middleware

    middleware._configured_cache = None
    yield
    middleware._configured_cache = None
