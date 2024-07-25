import pytest

from squid_lab_quam.components.information import Information


def test_information_initialization():
    # Test if Information class can be initialized without errors
    try:
        info = Information()
        assert isinstance(
            info, Information
        ), "Information instance is not created successfully"
    except Exception as e:
        pytest.fail(f"Failed to initialize Information class: {e}")


def test_information_attributes():
    # Test if the Information class has the expected attributes after initialization
    info = Information()

    attrs = [
        "user_name",
        "user_ku_tag",
        "device_name",
        "fridge_name",
        "project_name",
        "state_path",
        "data_path",
        "calibration_db_path",
    ]

    for attr in attrs:
        assert hasattr(info, attr), f"Information class does not have attribute {attr}"
