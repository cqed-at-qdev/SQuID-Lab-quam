import pytest
from quam.components.channels import IQChannel
from quam.components.hardware import Mixer

from quam_squid_lab.components.information import Information
from quam_squid_lab.components.network import OPXNetwork
from quam_squid_lab.components.qubits import ScQubit
from quam_squid_lab.components.roots import SQuIDRoot1


def test_SQuIDRoot1_initialization():
    # Test if SQuIDRoot1 class can be initialized without errors
    try:
        quam = SQuIDRoot1()
        assert isinstance(
            quam, SQuIDRoot1
        ), "SQuIDRoot1 instance is not created successfully"
    except Exception as e:
        pytest.fail(f"Failed to initialize SQuIDRoot1 class: {e}")


def test_update_config():
    # Test if the update_config method works as expected
    quam = SQuIDRoot1()

    inital_config = quam.config
    inital_config["test"] = "test"

    assert "test" in quam.config, "update_config method does not work as expected"
