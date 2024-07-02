from dataclasses import field
from typing import Union

from quam.components.channels import IQChannel
from quam.core import QuamComponent, quam_dataclass

from squid_lab_quam.components.pulse_sets import PulseSet
from squid_lab_quam.components.resonators import ReadoutResonator
from squid_lab_quam.utils import key_from_parent_dict


@quam_dataclass
class Transmon(QuamComponent):
    """
    Example QuAM component for a transmon qubit.

    Args:
        thermalization_time (int): An integer.
        T1 (str): A string.
    """

    id: Union[int, str] = "#./id_from_parent_dict"

    xy: IQChannel = None
    resonator: ReadoutResonator = None

    transition_frequencies: list[float] = field(default_factory=lambda: [None, None])

    T1: int = None
    T2ramsey: int = None
    T2echo: int = None
    thermalization_time_factor: int = 5  # exp(-5) = 0.0067
    pulse_sets: dict[str, PulseSet] = field(default_factory=dict)

    def __post_init__(self):
        if self.transition_frequencies is None:
            self.transition_frequencies = [None, None]

    @property
    def id_from_parent_dict(self) -> str:
        return str(key_from_parent_dict(self))

    @property
    def thermalization_time(self):
        if self.T1 is None:
            raise ValueError(
                f"Error: T1 not specified for qubit {self.id}. Please provide a value to enable thermalization time."
            )
        return self.thermalization_time_factor * self.T1

    @property
    def f_01(self):
        """The 0-1 (g-e) transition frequency in Hz"""
        return self.transition_frequencies[0]

    @f_01.setter
    def f_01(self, value):
        self.transition_frequencies[0] = value

    @property
    def f_12(self):
        """The 1-2 (e-f) transition frequency in Hz"""
        return self.transition_frequencies[1]

    @f_12.setter
    def f_12(self, value):
        self.transition_frequencies[1] = value

    @property
    def anharmonicity(self):
        return (
            self.f_12 - self.f_01
            if self.f_12 is not None and self.f_01 is not None
            else None
        )

    @property
    def name(self):
        return self.id if isinstance(self.id, str) else f"q{self.id}"

    def set_default_gate_shape(self, gate_shape: str) -> None:
        if gate_shape not in self.pulse_sets:
            raise ValueError(
                f"Error: Pulse set {gate_shape} not defined for qubit {self.name}. Defined pulse sets are {self.pulse_sets.keys()}"
            )

        self.pulse_sets[gate_shape].set_as_default_gate_shape()
