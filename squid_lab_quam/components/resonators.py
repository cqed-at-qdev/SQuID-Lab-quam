from quam.components.channels import InOutIQChannel
from quam.core import quam_dataclass

__all__ = ["ReadoutResonator"]


@quam_dataclass
class ReadoutResonator(InOutIQChannel):
    """QuAM component for a readout resonator

    Args:
        depletion_time (int): the resonator depletion time in ns.
        frequency_bare (int, float): the bare resonator frequency in Hz.
    """

    depletion_time: int = None
    frequency_bare: float = None
    frequency_q0: float = None
    frequency_q1: float = None
    Q_int: float = None
    Q_ext: float = None

    @property
    def readout_frequency(self):
        return self.RF_frequency

    @readout_frequency.setter
    def readout_frequency(self, value):
        self.RF_frequency = value
