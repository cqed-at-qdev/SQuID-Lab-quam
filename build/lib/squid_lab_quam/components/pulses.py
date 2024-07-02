from quam.components.pulses import DragPulse
from quam.core import quam_dataclass

__all__ = ["DragGaussianPulse"]


@quam_dataclass
class DragGaussianPulse(DragPulse):
    """Rename of DragPulse to DragGaussianPulse."""  # TODO: also rename alpha to drag_coefficient

    pass
