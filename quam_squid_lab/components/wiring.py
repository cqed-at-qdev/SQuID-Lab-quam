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

    def default_octave_port(self):
        """Get the default input octave port for the IQ channel
        (1, 2) -> 1
        (3, 4) -> 2
        (5, 6) -> 3
        (7, 8) -> 4
        (9, 10) -> 5
        """

        return _default_octave_port(self.port_I, self.port_Q)


@quam_dataclass
class OPXFeedLineWiring(QuamComponent):
    output_I: Tuple[str, int]  # tuple of (controller_name, port)
    output_Q: Tuple[str, int]  # tuple of (controller_name, port)
    input_I: Tuple[str, int]  # tuple of (controller_name, port)
    input_Q: Tuple[str, int]  # tuple of (controller_name, port)

    def default_octave_port_in(self):
        """Get the default input octave port for the IQ channel
        (1, 2) -> 1
        (3, 4) -> 2
        (5, 6) -> 3
        (7, 8) -> 4
        (9, 10) -> 5
        """
        return _default_octave_port(self.output_I, self.output_Q)

    def default_octave_port_out(self):
        """Get the default output port of the octave
        (1, 2) -> 1"""
        return _default_octave_port(self.input_I, self.input_Q)


@quam_dataclass
class OPXWiring(QuamComponent):
    drive_lines: Dict[str, OPXIQChannelWiring] = field(default_factory=dict)
    feed_lines: Dict[str, OPXFeedLineWiring] = field(default_factory=dict)
    flux_lines: Dict[str, OPXSingleChannelWiring] = field(default_factory=dict)


def _default_octave_port(port_I: Tuple[str, int], port_Q: Tuple[str, int]) -> int:
    """Get the default octave port for the IQ channel:
    (1, 2) -> 1
    (3, 4) -> 2
    (5, 6) -> 3
    (7, 8) -> 4
    (9, 10) -> 5

    Raises:
        ValueError: If the IQ channel ports are not on the same controller
        ValueError: If the IQ channel ports are not consecutive with port I on an odd-numbered port

    Returns:
        int: The default octave port
    """

    if port_I[0] != port_Q[0]:
        raise ValueError(
            f"IQ channel ports must be on the same controller to use default octave wiring, got {port_I[0]} and {port_Q[0]}"
        )

    if port_I[1] % 2 != 1 or port_Q[1] != port_I[1] + 1:
        raise ValueError(
            (
                f"IQ channel ports must be consecutive with port I on an odd-numbered port to use default octave wiring,"
                f"got {port_I[1]} and {port_Q[1]}"
            )
        )

    return port_Q[1] // 2
