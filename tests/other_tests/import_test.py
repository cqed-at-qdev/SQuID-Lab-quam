import pytest


def test_import_package():
    try:
        import squid_lab_quam
    except ImportError:
        pytest.fail("Failed to import the package")
