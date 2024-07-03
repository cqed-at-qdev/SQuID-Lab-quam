from dataclasses import field
from typing import Type, Union, List, Tuple
from abc import abstractmethod

from quam.components.channels import Channel
from quam.components.pulses import Pulse
from quam.core import QuamComponent, quam_dataclass

from squid_lab_quam.components.pulses import DragGaussianPulse
from squid_lab_quam.utils import key_from_parent_dict


@quam_dataclass
class PulseSet(QuamComponent):
    """QuAM component for a set of pulses."""

    PulseClass: str
    pulse_name: str = "#./_id_from_parent_dict"
    channel: Channel = "#../../xy"

    gates: list[str] = None

    @property
    def _id_from_parent_dict(self) -> str:
        return str(key_from_parent_dict(self))

    @property
    def Pulse(self) -> Type[Pulse]:
        """Get the pulse class. If the PulseClass is a string, import the class from the module described by the string first."""
        if isinstance(self.PulseClass, str):
            module_name = self.PulseClass.rsplit(".", 1)[0]
            cls = self.PulseClass.rsplit(".", 1)[1]
            return getattr(
                __import__(module_name, fromlist=module_name.rsplit(".")), cls
            )
        return self.PulseClass

    @property
    @abstractmethod
    def individual_pulse_parameters(self) -> dict:
        """Return a dictionary with the individual pulse parameters for each gate."""
        pass

    @property
    @abstractmethod
    def shared_pulse_parameters(self) -> dict:
        """Return a dictionary with the shared pulse parameters for all gates."""
        pass

    def _dict_values_as_references(self, dictionary: dict) -> dict:
        """Return a dictionary with the values of the input dictionary as quam references."""
        return {key: self.get_reference(key) for key in dictionary.keys()}

    def _add_drive_pulses(self):
        """Populate the channel of the pulse set with the drive pulses.
        Only used when generating quam structures."""

        for pulse in self.gates:
            parameters = (
                self.individual_pulse_parameters[pulse] | self.shared_pulse_parameters
            )
            parameters_referenced = self._dict_values_as_references(parameters)

            self.channel.operations[f"{pulse}_{self.pulse_name}"] = self.Pulse(
                **parameters_referenced
            )

    def set_as_default_gate_shape(self) -> None:
        """Set this pulse set as the default pulse shape for the channel."""

        for gate in self.gates:
            if gate not in self.channel.operations:
                self._add_drive_pulses()
            self.channel.operations[gate] = f"#./{gate}_{self.pulse_name}"


@quam_dataclass
class PulseSetDragGaussian(PulseSet):

    PulseClass: str = "squid_lab_quam.components.pulses.DragGaussianPulse"
    gates: list[str] = field(
        init=False,
        default_factory=lambda: ["x90", "x180", "y90", "y180", "-x90", "-y90"],
    )

    amplitude_90: float
    amplitude_180: float
    phase_x: float = 0
    phase_y: float = 90
    length: float
    sigma: float
    anharmonicity: float
    detuning: float = 0
    alpha: float = 0
    subtracted: bool = True
    digital_marker: Union[str, List[Tuple[int, int]]] = None

    @property
    def amplitude_m90(self):
        return -self.amplitude_90

    @property
    def individual_pulse_parameters(self):
        return {
            "x90": {
                "amplitude": self.amplitude_90,
                "axis_angle": self.phase_x,
            },
            "x180": {
                "amplitude": self.amplitude_180,
                "axis_angle": self.phase_x,
            },
            "y90": {
                "amplitude": self.amplitude_90,
                "axis_angle": self.phase_y,
            },
            "-x90": {
                "amplitude": self.amplitude_m90,
                "axis_angle": self.phase_x,
            },
            "-y90": {
                "amplitude": self.amplitude_m90,
                "axis_angle": self.phase_y,
            },
            "y180": {
                "amplitude": self.amplitude_180,
                "axis_angle": self.phase_y,
            },
        }

    @property
    def shared_pulse_parameters(self):
        return {
            "length": self.length,
            "sigma": self.sigma,
            "anharmonicity": self.anharmonicity,
            "alpha": self.alpha,
            "detuning": self.detuning,
            "subtracted": self.subtracted,
            "digital_marker": self.digital_marker,
        }


class PulseSetFlattopCosine(PulseSet):

    gates: list[str] = field(init=False, default_factory=list)

    def __post_init__(self):
        self.gates = ["rise", "fall"]

    # @classmethod
    # def pulse_set_drag_gaussian(
    #     self,
    #     length: float,
    #     sigma: float,
    #     anharmonicity: float,
    #     amplitude_90: float,
    #     amplitude_180: float,
    #     phase_x: float = 0,
    #     phase_y: float = 90,
    #     alpha: float = 0,
    #     detuning: float = 0,
    #     subtracted: bool = False,
    # ):
    #     return self(
    #         PulseClass=DragGaussianPulse,
    #         gates=["x90", "x180", "y90", "y180", "-x90", "-y90"],
    #         individual_pulse_parameters={
    #             "x90": {
    #                 "amplitude": ...,
    #                 "axis_angle": ...,
    #             },
    #             "x180": {
    #                 "amplitude": ...,
    #                 "axis_angle": ...,
    #             },
    #             "y90": {
    #                 "amplitude": ...,
    #                 "axis_angle": ...,
    #             },
    #             "-x90": {
    #                 "amplitude": ...,
    #                 "axis_angle": ...,
    #             },
    #             "-y90": {
    #                 "amplitude": ...,
    #                 "axis_angle": ...,
    #             },
    #             "y180": {
    #                 "amplitude": ...,
    #                 "axis_angle": ...,
    #             },
    #         },
    #         common_pulse_parameters={
    #             "length": length,
    #             "sigma": sigma,
    #             "anharmonicity": anharmonicity,
    #             "alpha": alpha,
    #             "detuning": detuning,
    #             "subtracted": subtracted,
    #         },
    #     )


if __name__ == "__main__":
    pulse_set = PulseSetDragGaussian(
        amplitude_90=0,
        amplitude_180=0,
    )

    pulse_set


# @quam_dataclass
# class PulseSetXY18090(PulseSet):
#     """QuAM component for a set of XY 180 and 90 degree pulses."""

#     @property
#     def amplitude_m90(self):
#         return -self.amplitude_90


# PulseSetXY18090(
#     PulseClass=DragGaussianPulse,
#     individual_pulse_parameters={
#         "x90": {
#             "amplitude": ...,
#             "axis_angle": ...,
#         },
#         "x180": {},
#         "y90": {},
#         "-x90": {},
#         "-y90": {},
#         "y180": {},
#     },
#     common_pulse_parameters={
#         "duration": ...,
#         "sigma": ...,
#         "anharmonicity": ...,
#         "alpha": ...,
#     },
# )
