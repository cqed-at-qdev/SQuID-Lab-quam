from dataclasses import field
from typing import Tuple, Union

from qm.qua._dsl_specific_type_hints import AmpValuesType
from qm.qua._expressions import QuaVariableType
from quam.components.channels import InOutIQChannel
from quam.core import QuamComponent, quam_dataclass

from squid_lab_quam.components.information import QuamMetadata

__all__ = ["ReadoutResonator"]


@quam_dataclass
class ReadoutResonator(QuamComponent):
    """QuAM component for a readout resonator

    Args:
        depletion_time (int): the resonator depletion time in ns.
        frequency_bare (int, float): the bare resonator frequency in Hz.
    """

    channel: InOutIQChannel
    depletion_time: int = None
    depletion_time__metadata: QuamMetadata = field(
        default_factory=lambda: QuamMetadata(
            unit="ns",
            long_name="Depletion time",
            description="The resonator depletion time",
        )
    )

    frequency_bare: float = None
    frequency_bare__metadata: QuamMetadata = field(
        default_factory=lambda: QuamMetadata(
            unit="Hz",
            long_name="Bare frequency",
            description="The bare resonator frequency, i.e., as measured at high power",
        )
    )

    frequency_q0: float = None
    frequency_q0__metadata: QuamMetadata = field(
        default_factory=lambda: QuamMetadata(
            unit="Hz",
            long_name="Q0 frequency",
            description="The dispersively shifted resonator frequency with the qubit in state |0⟩",
        )
    )

    frequency_q1: float = None
    frequency_q1__metadata: QuamMetadata = field(
        default_factory=lambda: QuamMetadata(
            unit="Hz",
            long_name="Q1 frequency",
            description="The dispersively shifted resonator frequency with the qubit in state |1⟩",
        )
    )

    Q_int: float = None
    Q_int__metadata: QuamMetadata = field(
        default_factory=lambda: QuamMetadata(
            long_name="Internal quality factor",
            description="The internal quality factor of the resonator",
        )
    )

    Q_ext: float = None
    Q_ext__metadata: QuamMetadata = field(
        default_factory=lambda: QuamMetadata(
            long_name="External quality factor",
            description="The external quality factor of the resonator",
        )
    )

    readout_frequency__metadata: QuamMetadata = field(
        default_factory=lambda: QuamMetadata(
            unit="Hz",
            long_name="Readout frequency",
            description="The readout frequency of the resonator",
        )
    )

    # def __post_init__(self):
    #     if self.channel.id is None:
    #         self.channel.id = "#../default_resonator_channel_id"

    # if self.channel.RF_frequency is None:
    #     self.channel.RF_frequency = self.frequency_bare

    # @property
    # def default_resonator_channel_id(self):
    #     return f"{self.parent.name}.resonator"

    @property
    def name(self) -> str:
        return f"{self.parent.name}.resonator"

    # @property
    # def name(self):
    #     return self.channel.name

    @property
    def readout_frequency(self) -> float:
        return self.channel.RF_frequency

    @readout_frequency.setter
    def readout_frequency(self, value):
        self.channel.RF_frequency = value

    def measure(
        self,
        pulse_name: str,
        amplitude_scale: Union[float, AmpValuesType] = None,
        qua_vars: Tuple[QuaVariableType, QuaVariableType] = None,
        stream=None,
    ):
        return self.channel.measure(
            pulse_name=pulse_name,
            amplitude_scale=amplitude_scale,
            qua_vars=qua_vars,
            stream=stream,
        )
