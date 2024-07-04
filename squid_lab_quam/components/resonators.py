from typing import Tuple, Union

from qm.qua._dsl import AmpValuesType, QuaVariableType
from quam.components.channels import InOutIQChannel
from quam.core import QuamComponent, quam_dataclass

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
    frequency_bare: float = None
    frequency_q0: float = None
    frequency_q1: float = None
    Q_int: float = None
    Q_ext: float = None

    @property
    def readout_frequency(self):
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
