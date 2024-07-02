from dataclasses import dataclass, field
from typing import Any, Type, Union

from quam.components.channels import Channel
from quam.components.pulses import Pulse
from quam.core import QuamComponent, QuamDict, quam_dataclass

from squid_lab_quam.components.pulses import DragGaussianPulse
from squid_lab_quam.utils import key_from_parent_dict


@quam_dataclass
class PulseSet(QuamComponent):
    """QuAM component for a set of pulses."""

    PulseClass: Union[Type[Pulse], str]
    amplitude_90: float
    amplitude_180: float
    axis_angle_x: float = 0
    axis_angle_y: float = 90
    pulse_name: str = "#./_id_from_parent_dict"
    common_pulse_parameters: dict = field(default_factory=dict)
    channel: Channel = "#../../xy"

    @property
    def _common_pulse_parameters_references(self) -> dict:
        return {
            key: f"{self.common_pulse_parameters.get_reference()}/{key}"
            for key in self.common_pulse_parameters.keys()
        }

    @property
    def _id_from_parent_dict(self) -> str:
        return str(key_from_parent_dict(self))

    @property
    def Pulse(self) -> Type[Pulse]:
        if isinstance(self.PulseClass, str):
            module = self.PulseClass.rsplit(".", 1)[0]
            cls = self.PulseClass.rsplit(".", 1)[1]
            return getattr(__import__(module), cls)
        return self.PulseClass

    @property
    def amplitude_m90(self):
        return -self.amplitude_90

    def _add_drive_pulses(self):

        parameters_references = {
            key: f"{self.get_reference()}/{key}"
            for key in [
                "amplitude_90",
                "amplitude_180",
                "amplitude_m90",
                "axis_angle_x",
                "axis_angle_y",
            ]
        }

        self.channel.operations[f"x180_{self.pulse_name}"] = self.Pulse(
            amplitude=parameters_references["amplitude_180"],
            axis_angle=parameters_references["axis_angle_x"],
            **self._common_pulse_parameters_references,
        )
        self.channel.operations[f"x90_{self.pulse_name}"] = self.Pulse(
            amplitude=parameters_references["amplitude_90"],
            axis_angle=parameters_references["axis_angle_x"],
            **self._common_pulse_parameters_references,
        )
        self.channel.operations[f"-x90_{self.pulse_name}"] = self.Pulse(
            amplitude=parameters_references["amplitude_m90"],
            axis_angle=parameters_references["axis_angle_x"],
            **self._common_pulse_parameters_references,
        )
        self.channel.operations[f"y180_{self.pulse_name}"] = self.Pulse(
            amplitude=parameters_references["amplitude_180"],
            axis_angle=parameters_references["axis_angle_y"],
            **self._common_pulse_parameters_references,
        )
        self.channel.operations[f"y90_{self.pulse_name}"] = self.Pulse(
            amplitude=parameters_references["amplitude_90"],
            axis_angle=parameters_references["axis_angle_y"],
            **self._common_pulse_parameters_references,
        )
        self.channel.operations[f"-y90_{self.pulse_name}"] = self.Pulse(
            amplitude=parameters_references["amplitude_m90"],
            axis_angle=parameters_references["axis_angle_y"],
            **self._common_pulse_parameters_references,
        )


@quam_dataclass
class PulseSet(QuamComponent):
    """QuAM component for a set of pulses."""

    PulseClass: Union[Type[Pulse], str]
    pulse_name: str = "#./_id_from_parent_dict"
    channel: Channel = "#../../xy"

    gates: list[str] = None

    individual_pulse_parameters: QuamDict = field(default_factory=dict)
    common_pulse_parameters: QuamDict = field(default_factory=dict)

    @property
    def _common_pulse_parameters_references(self) -> dict:
        return {
            key: f"{self.common_pulse_parameters.get_reference()}/{key}"
            for key in self.common_pulse_parameters.keys()
        }

    @property
    def _id_from_parent_dict(self) -> str:
        return str(key_from_parent_dict(self))

    @property
    def Pulse(self) -> Type[Pulse]:
        """Get the pulse class. If the PulseClass is a string, import the class from the module described by the string first."""
        if isinstance(self.PulseClass, str):
            module = self.PulseClass.rsplit(".", 1)[0]
            cls = self.PulseClass.rsplit(".", 1)[1]
            return getattr(__import__(module), cls)
        return self.PulseClass

    def _dict_values_as_references(self, dictionary: dict) -> dict:
        """Return a dictionary with the values of the input dictionary as quam references."""
        return {key: self.get_reference(key) for key in dictionary.keys()}

    def _add_drive_pulses(self):
        """Populate the channel of the pulse set with the drive pulses.
        Only used when generating quam structures."""

        for pulse in self.gates:
            parameters = (
                self.individual_pulse_parameters[pulse]
                | self._common_pulse_parameters_references
            )
            parameters_referenced = self._dict_values_as_references(parameters)

            self.channel.operations[f"{pulse}_{self.pulse_name}"] = self.Pulse(
                **parameters_referenced
            )

    def set_as_default_gate_shape(self) -> None:
        """Set this pulse set as the default pulse shape for the channel."""

        for gate in self.gates:
            self.channel.operations[gate] = f"#./{gate}_{self.pulse_name}"


@quam_dataclass
class PulseSetDragGaussian(PulseSet):

    gates: list[str] = field(init=False, default_factory=list)
    PulseClass: Union[Type[Pulse], str] = field(init=False, default=DragGaussianPulse)

    # amplitude_90: float
    # amplitude_180: float
    # phase_x: float = 0
    # phase_y: float = 90

    def __init__(self, new_value):
        super().__init__()
        self.common_pulse_parameters["test"] = new_value

    def __post_init__(self):
        self.gates = ["x90", "x180", "y90", "y180", "-x90", "-y90"]

    @property
    def amplitude_m90(self):
        return -self.amplitude_90


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
