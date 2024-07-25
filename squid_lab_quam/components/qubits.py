from dataclasses import field
from typing import Literal, Tuple, Union

from qm.octave.octave_mixer_calibration import MixerCalibrationResults
from qm.qua import align
from qm.qua._dsl_specific_type_hints import AmpValuesType
from qm.qua._expressions import QuaVariableType
from quam.components.channels import IQChannel
from quam.components.octave import OctaveUpConverter
from quam.core import QuamComponent, quam_dataclass

from squid_lab_quam.components.flux_line import FluxLine
from squid_lab_quam.components.information import QuamMetadata
from squid_lab_quam.components.pulse_sets import PulseSet
from squid_lab_quam.components.resonators import ReadoutResonator
from squid_lab_quam.quam_macros.qubit_macros import reset_qubit
from squid_lab_quam.utils.name_from_parent import key_from_parent_dict

__all__ = ["ScQubit", "FluxtunebleTransmon"]


@quam_dataclass
class ScQubit(QuamComponent):
    """
    SQuID Lab QuAM component for a superconducting qubit.

    Args:
        id (Union[int, str]): The qubit ID. If int, it is converted to a string.
        xy (IQChannel): The IQ channel for the qubit.
        resonator (ReadoutResonator): The readout resonator for the qubit.
        transition_frequencies (list[float]): The transition frequencies of the qubit in Hz.
        T1 (int): The qubit decay rate in seconds.
        T2ramsey (int): The dephasing time as measured by a Ramsey experiment in seconds.
        T2echo (int): The dephasing time as measured by an echo experiment in seconds.
        thermalization_time_factor (int): Factor to multiply the T1 time in cooldown qubit resets.
    """

    id: Union[int, str] = "#./id_from_parent_dict"

    xy: IQChannel = None
    resonator: ReadoutResonator = None

    transition_frequencies: list[float] = field(default_factory=lambda: [None, None])
    transition_frequencies__metadata: QuamMetadata = field(
        default_factory=lambda: QuamMetadata(
            unit="Hz",
            long_name="Transition frequencies",
            description="Transition frequencies of the qubit in the form [f01, f12, ...]",
        )
    )  # TODO: consider if list is convenient or if we should have separate fields

    T1: int = None
    T1__metadata: QuamMetadata = field(
        default_factory=lambda: QuamMetadata(
            unit="s", long_name="T1", description="Qubit decay rate"
        )
    )
    T2ramsey: int = None
    T2ramsey__metadata: QuamMetadata = field(
        default_factory=lambda: QuamMetadata(
            unit="s",
            long_name="T2 Ramsey",
            description="Dephasing time as measured by a Ramsey experiment",
        )
    )

    T2echo: int = None
    T2echo__metadata: QuamMetadata = field(
        default_factory=lambda: QuamMetadata(
            unit="s",
            long_name="T2 echo",
            description="Dephasing time as measured by an echo experiment",
        )
    )

    thermalization_time_factor: int = 5
    thermalization_time_factor__metadata: QuamMetadata = field(
        default_factory=lambda: QuamMetadata(
            unit="int",
            long_name="Thermalization time factor",
            description="Factor to multiply the T1 time in cooldown qubit resets. exp(-5) = 0.0067",
        )
    )

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

    def __matmul__(self, other):
        if not isinstance(other, ScQubit):
            raise ValueError(
                "Cannot create a qubit pair (q1 @ q2) with a non-qubit object, "
                f"where q1={self} and q2={other}"
            )

        if self is other:
            raise ValueError(
                "Cannot create a qubit pair with same qubit (q1 @ q1), where q1={self}"
            )

        for qubit_pair in self._root.qubit_pairs:
            if qubit_pair.qubit_control is self and qubit_pair.qubit_target is other:
                return qubit_pair

        raise ValueError(
            "Qubit pair not found: qubit_control={self.name}, "
            "qubit_target={other.name}"
        )

    def measure(
        self,
        pulse_name: str,
        amplitude_scale: Union[float, AmpValuesType] = None,
        qua_vars: Tuple[QuaVariableType, QuaVariableType] = None,
        stream=None,
    ):
        return self.resonator.measure(
            pulse_name=pulse_name,
            amplitude_scale=amplitude_scale,
            qua_vars=qua_vars,
            stream=stream,
        )

    def reset(
        self,
        reset_method: Literal[
            "active", "cooldown", None
        ] = "active",  # | Callable[Concatenate["Qubit", ...], None]
        readout_pulse: str = "flattop",
        max_tries: int = 10,
        threshold_g: float | None = None,
        relaxation_time: float | None = None,
        save: bool = True,
    ):
        """Reset a qubit. This function is called to reset the qubit after a measurement.

        Args:
            reset_method (Literal["active", "cooldown", None] | Callable[Concatenate[Qubit, ...], None], optional): The method to use to reset the qubit. Defaults to "active".
            readout_pulse (str, optional): Pulse shape to use for the readout pulse. Defaults to "flattop".
            max_tries (int, optional): The maximum number of tries to reset the qubit. Defaults to 10.
            threshold_g (float | None, optional): The threshold to use for the readout pulse. Defaults to thermalization_time_factor * T1.
            relaxation_time (float | None, optional): The time to wait for the resonator to relax. Defaults to None.
            save (bool, optional): Whether to save the number of pulses applied. Defaults to True.
        """
        if relaxation_time is None:
            relaxation_time = self.thermalization_time_factor * self.T1

        return reset_qubit(
            self,
            reset_method=reset_method,
            readout_pulse=readout_pulse,
            max_tries=max_tries,
            threshold_g=threshold_g,
            relaxation_time=relaxation_time,
            save=save,
        )

    def calibrate_drive_mixer(self) -> MixerCalibrationResults:
        if not isinstance(self.xy.frequency_converter_up, OctaveUpConverter):
            raise NotImplementedError(
                f"Error: Mixer calibration only implemented with an octave up converter."
            )
        self._root.qm.calibrate_element(self.xy.name)

    def calibrate_readout_mixer(self) -> MixerCalibrationResults:
        if not isinstance(
            self.resonator.channel.frequency_converter_up, OctaveUpConverter
        ):
            raise NotImplementedError(
                f"Error: Mixer calibration only implemented with an octave up converter."
            )
        self._root.qm.calibrate_element(self.resonator.channel.name)

    def align(self, *elements):
        """Align the qubit to other elements."""
        align(self.xy.name, *elements)

    def align_resonator(self, *elements):
        """Align the qubit to other elements and its resonator."""
        align(self.xy.name, self.resonator.channel.name, *elements)

    def wait(self, duration, *elements):
        """Wait for a duration."""
        self.align(*elements)
        self.xy.wait(duration)


@quam_dataclass
class FluxtunebleTransmon(ScQubit):
    """
    SQuID Lab QuAM component for a flux-tuneable transmon qubit.

    Args:
        id (Union[int, str]): The qubit ID. If int, it is converted to a string.
        xy (IQChannel): The IQ channel for the qubit.
        z (FluxLine): The flux channel for the qubit.
        resonator (ReadoutResonator): The readout resonator for the qubit.
        transition_frequencies (list[float]): The transition frequencies of the qubit in Hz.
        T1 (int): The qubit decay rate in seconds.
        T2ramsey (int): The dephasing time as measured by a Ramsey experiment in seconds.
        T2echo (int): The dephasing time as measured by an echo experiment in seconds.
        thermalization_time_factor (int): Factor to multiply the T1 time in cooldown qubit resets.

    """

    z: FluxLine = None

    "TODO: Add flux functions to FluxtunebleTransmon"
