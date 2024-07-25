from typing import Literal

import numpy as np
from quam.components.pulses import DragPulse, Pulse
from quam.core import quam_dataclass

__all__ = ["DragGaussianPulse"]


@quam_dataclass
class DragGaussianPulse(DragPulse):
    """Rename of DragPulse to DragGaussianPulse."""  # TODO: also rename alpha to drag_coefficient

    pass


@quam_dataclass
class FlatTopCosinePulse(Pulse):
    """Gaussian pulse with flat top QuAM component.

    Args:
        length (int): The total length of the pulse in samples.
        amplitude (float): The amplitude of the pulse in volts.
        axis_angle (float, optional): IQ axis angle of the output pulse in radians.
            If None (default), the pulse is meant for a single channel or the I port
                of an IQ channel
            If not None, the pulse is meant for an IQ channel (0 is X, pi/2 is Y).
        flat_length (int): The length of the pulse's flat top in samples.
            The rise and fall lengths are calculated from the total length and the
            flat length.
    """

    amplitude: float
    axis_angle: float = None
    flat_length: int = 0
    return_part: Literal["all", "fall", "rise"] = "all"

    @property
    def rise_fall_length(self):
        if self.return_part == "all":
            return (self.length - self.flat_length) // 2
        else:
            return self.length

    def waveform_function(self):
        from qualang_tools.config.waveform_tools import flattop_cosine_waveform

        waveform = flattop_cosine_waveform(
            amplitude=self.amplitude,
            flat_length=self.flat_length,
            rise_fall_length=self.rise_fall_length,
            return_part=self.return_part,
        )
        waveform = np.array(waveform)

        if self.axis_angle is not None:
            waveform = waveform * np.exp(1j * self.axis_angle)

        return waveform
