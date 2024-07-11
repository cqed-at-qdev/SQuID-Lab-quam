from abc import abstractmethod
from dataclasses import field
from typing import ClassVar, Iterable, List, Tuple, Type, Union

import qm.qua as qua
from quam.components.channels import Channel
from quam.components.pulses import Pulse
from quam.core import QuamComponent, quam_dataclass

from squid_lab_quam.components.information import QuamMetadata
from squid_lab_quam.utils import key_from_parent_dict


@quam_dataclass
class PulseSet(QuamComponent):
    """Base QuAM component for a pulse set."""

    PulseClass: str
    gates: Iterable[str]
    pulse_name: str = "#./_name_from_parent_dict"
    channel: Channel = "#../../xy"

    @property
    def _name_from_parent_dict(self) -> str:
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
        """Return a dictionary with the individual pulse parameters for each gate.
        See PulseSetDragGaussian for an example."""
        pass

    @property
    @abstractmethod
    def shared_pulse_parameters(self) -> dict:
        """Return a dictionary with the shared pulse parameters for all gates.
        See PulseSetDragGaussian for an example."""
        pass

    def add_drive_pulses(self):
        """Populate the channel of the pulse set with the drive pulses.
        Only used when generating quam structures."""

        for gate_name in self.individual_pulse_parameters.keys():
            if gate_name not in self.gates:
                raise ValueError(
                    f"individual_pulse_parameters gate {gate_name} is not in the list of gates {self.gates}."
                )

        for pulse in self.gates:
            parameters = (
                self.individual_pulse_parameters[pulse] | self.shared_pulse_parameters
            )

            self.channel.operations[f"{pulse}_{self.pulse_name}"] = self.Pulse(
                **parameters
            )

    def set_as_default_gate_shape(self) -> None:
        """Set this pulse set as the default pulse shape for the channel."""

        for gate in self.gates:
            if gate not in self.channel.operations:
                self.add_drive_pulses()
            self.channel.operations[gate] = f"#./{gate}_{self.pulse_name}"


@quam_dataclass
class PulseSetDragGaussian(PulseSet):

    PulseClass: ClassVar[str] = "squid_lab_quam.components.pulses.DragGaussianPulse"
    gates: ClassVar[Iterable[str]] = ("x90", "x180", "y90", "y180", "-x90", "-y90")

    amplitude_90: float
    amplitude_90__metadata: QuamMetadata = field(
        default_factory=lambda: QuamMetadata(
            unit="V",
            long_name="π/2-pulse peak amplitude",
            description="Amplitude of the π/2 pulse.",
        )
    )

    amplitude_180: float
    amplitude_180__metadata: QuamMetadata = field(
        default_factory=lambda: QuamMetadata(
            unit="V",
            long_name="π-pulse peak amplitude",
            description="Amplitude of the π pulse.",
        )
    )

    length: float
    length__metadata: QuamMetadata = field(
        default_factory=lambda: QuamMetadata(
            unit="ns",
            long_name="Pulse length",
            description="Length of the window containing the pulse.",
        )
    )

    sigma: float
    sigma__metadata: QuamMetadata = field(
        default_factory=lambda: QuamMetadata(
            unit="ns",
            long_name="Pulse sigma",
            description="Width of the Gaussian waveform pulse.",
        )
    )

    phase_x: float = 0
    phase_x__metadata: QuamMetadata = field(
        default_factory=lambda: QuamMetadata(
            unit="degree",
            long_name="X-axis phase",
            description="Phase of the pulse in the X-axis.",
        )
    )

    phase_y: float = 90
    phase_y__metadata: QuamMetadata = field(
        default_factory=lambda: QuamMetadata(
            unit="degree",
            long_name="Y-axis phase",
            description="Phase of the pulse in the Y-axis.",
        )
    )

    anharmonicity: float
    anharmonicity__metadata: QuamMetadata = field(
        default_factory=lambda: QuamMetadata(
            unit="Hz",
            long_name="Waveform anharmonicity",
            description="Anharmonicity used in the calculation of the DRAG waveform.",
        )
    )

    detuning: float = 0
    detuning__metadata: QuamMetadata = field(
        default_factory=lambda: QuamMetadata(
            unit="Hz",
            long_name="Detuning",
            description="Detuning of the pulse from the channel RF frequency.",
        )
    )

    alpha: float = 0
    alpha__metadata: QuamMetadata = field(
        default_factory=lambda: QuamMetadata(
            long_name="DRAG coefficient",
            description="Coefficient for the derivative of the pulse.",
        )
    )

    subtracted: bool = True
    subtracted__metadata: QuamMetadata = field(
        default_factory=lambda: QuamMetadata(
            long_name="Subtracted",
            description="Whether the pulse is shifted such that the end points are 0",
        )
    )

    digital_marker: Union[str, List[Tuple[int, int]]] = None

    @property
    def amplitude_m90(self):
        return -self.amplitude_90

    @property
    def individual_pulse_parameters(self):
        return {
            "x90": {
                "amplitude": self.get_reference("amplitude_90"),
                "axis_angle": self.get_reference("phase_x"),
            },
            "x180": {
                "amplitude": self.get_reference("amplitude_180"),
                "axis_angle": self.get_reference("phase_x"),
            },
            "y90": {
                "amplitude": self.get_reference("amplitude_90"),
                "axis_angle": self.get_reference("phase_y"),
            },
            "-x90": {
                "amplitude": self.get_reference("amplitude_m90"),
                "axis_angle": self.get_reference("phase_x"),
            },
            "-y90": {
                "amplitude": self.get_reference("amplitude_m90"),
                "axis_angle": self.get_reference("phase_y"),
            },
            "y180": {
                "amplitude": self.get_reference("amplitude_180"),
                "axis_angle": self.get_reference("phase_y"),
            },
        }

    @property
    def shared_pulse_parameters(self):
        return {
            parameter: self.get_reference(parameter)
            for parameter in (
                "length",
                "sigma",
                "anharmonicity",
                "alpha",
                "detuning",
                "subtracted",
                "digital_marker",
            )
        }


@quam_dataclass
class PulseSetFlattopCosine(PulseSet):
    # TODO: Currently this flattop pulse has incorrect shape, i.e., 2 points at peak

    PulseClass: ClassVar[str] = "squid_lab_quam.components.pulses.FlatTopCosinePulse"
    gates: ClassVar[Iterable[str]] = ("rise", "fall")

    amplitude: float
    amplitude__metadata: QuamMetadata = field(
        default_factory=lambda: QuamMetadata(
            unit="V",
            long_name="Pulse amplitude",
            description="Peak amplitude of the pulse.",
        )
    )

    rise_fall_time: int
    rise_fall_time__metadata: QuamMetadata = field(
        default_factory=lambda: QuamMetadata(
            unit="ns",
            long_name="Rise and fall time",
            description="Time taken for the pulse to rise and fall, each the rise and fall parts are each of this duration.",
        )
    )

    @property
    def negative_amplitude(self) -> float:
        return -self.amplitude

    @property
    def individual_pulse_parameters(self) -> dict:
        return {
            "rise": {
                "return_part": "rise",
                "amplitude": self.get_reference("amplitude"),
            },
            "fall": {
                "return_part": "rise",  # rise here, because we implement fall with a negative rise + sticky element
                "amplitude": self.get_reference("negative_amplitude"),
            },
            # TODO: we should use a reversed negative fall, instead of negative rise. For cosine pulse, this this is not a problem, but for other pulses it might be.
        }

    @property
    def shared_pulse_parameters(self) -> dict:
        return {
            "length": self.get_reference("rise_fall_time"),
        }

    def play_flattop(self, plateau_duration: int) -> None:
        """Synethesize a flattop pulse with a given plateau duration.
        Note: only works if the element is sticky."""
        # TODO: add support for amplitude scaling
        # TODO: make this function more general, so it can be used for other pulse shapes as well
        self.channel.play(f"rise_{self.pulse_name}")
        self.channel.wait(plateau_duration)
        self.channel.play(f"fall_{self.pulse_name}")
