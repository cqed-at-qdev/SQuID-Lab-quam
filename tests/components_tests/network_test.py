from quam_squid_lab.components.network import OctaveNetwork, OPXNetwork


def test_defualt_OctaveNetwork():
    network = OctaveNetwork()
    assert network.octave_host == ""
    assert network.octave_port == 80
    assert network.controller == ""


def test_default_OPXNetwork():
    network = OPXNetwork()
    assert network.host == ""
    assert network.cluster_name == ""
    assert network.octave_networks == {}


def test_OctaveNetwork():
    network = OctaveNetwork(
        octave_host="octave_host", octave_port=8080, controller="controller"
    )
    assert network.octave_host == "octave_host"
    assert network.octave_port == 8080
    assert network.controller == "controller"


def test_OPXNetwork():
    network = OPXNetwork(
        host="host",
        cluster_name="cluster_name",
        octave_networks={"octave_network": OctaveNetwork()},
    )
    assert network.host == "host"
    assert network.cluster_name == "cluster_name"
    assert (
        network.octave_networks["octave_network"].to_dict() == OctaveNetwork().to_dict()
    )
