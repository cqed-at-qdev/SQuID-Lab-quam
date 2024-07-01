from dataclasses import field
from typing import Dict

from quam.core import QuamComponent, quam_dataclass


@quam_dataclass
class OctaveNetwork(QuamComponent):
    octave_host: str = ""
    octave_port: int = 80


@quam_dataclass
class OPXNetwork(QuamComponent):
    host: str = ""
    cluster_name: str = ""
    octave_networks: Dict[str, OctaveNetwork] = field(default_factory=dict)
