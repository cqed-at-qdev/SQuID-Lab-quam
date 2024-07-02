from dataclasses import field
from typing import Dict, Tuple

from quam.core import QuamComponent, quam_dataclass


@quam_dataclass
class OPXSingleChannelWiring(QuamComponent):
    port: Tuple[str, int]  # tuple of (controller_name, port)


@quam_dataclass
class OPXIQChannelWiring(QuamComponent):
    port_I: Tuple[str, int]  # tuple of (controller_name, port)
    port_Q: Tuple[str, int]  # tuple of (controller_name, port)


@quam_dataclass
class OPXFeedLineWiring(QuamComponent):
    output_I: Tuple[str, int]  # tuple of (controller_name, port)
    output_Q: Tuple[str, int]  # tuple of (controller_name, port)
    input_I: Tuple[str, int]  # tuple of (controller_name, port)
    input_Q: Tuple[str, int]  # tuple of (controller_name, port)


@quam_dataclass
class OPXWiring(QuamComponent):
    drive_lines: Dict[str, OPXIQChannelWiring] = field(default_factory=dict)
    feed_lines: Dict[str, OPXFeedLineWiring] = field(default_factory=dict)
    flux_lines: Dict[str, OPXSingleChannelWiring] = field(default_factory=dict)
