import pytest


def test_import_package():
    try:
        import quam_squid_lab
    except ImportError:
        pytest.fail("Failed to import the package")
