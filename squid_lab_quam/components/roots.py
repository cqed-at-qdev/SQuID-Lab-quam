from dataclasses import field
from typing import ClassVar, Dict, Sequence

from qm import QuantumMachine
from qm.QuantumMachinesManager import QuantumMachinesManager
from quam.components.channels import InOutIQChannel, IQChannel
from quam.components.pulses import SquareReadoutPulse
from quam.core import QuamDict, QuamRoot, quam_dataclass

from squid_lab_quam.components.information import Information
from squid_lab_quam.components.network import OPXNetwork
from squid_lab_quam.components.octave import (
    OctaveDownConverterSQuID,
    OctaveSQuID,
    OctaveUpConverterSQuID,
)
from squid_lab_quam.components.pulse_sets import (
    PulseSetDragGaussian,
    PulseSetFlattopCosine,
)
from squid_lab_quam.components.qubits import ScQubit
from squid_lab_quam.components.resonators import ReadoutResonator
from squid_lab_quam.components.wiring import OPXWiring

__all__ = ["SQuIDRoot1"]


@quam_dataclass
class SQuIDRoot1(QuamRoot):
    """SQuID Lab QuAM root type 1 for superconducting qubits."""

    @classmethod
    def load(cls, *args, **kwargs) -> "SQuIDRoot1":
        return super().load(*args, **kwargs)

    wiring: OPXWiring = field(default_factory=OPXWiring)
    network: OPXNetwork = field(default_factory=OPXNetwork)
    information: Information = field(default_factory=Information)
    qubits: Dict[str, ScQubit] = field(default_factory=dict)
    shared_qubit_parameters: QuamDict = field(default_factory=dict)
    octaves: Dict[str, OctaveSQuID] = field(default_factory=dict)

    _qm: ClassVar[QuantumMachine] = None
    _qmm: ClassVar[QuantumMachinesManager] = None
    _config: ClassVar[dict] = None
    _initial_quam: ClassVar["SQuIDRoot1"] = None

    @property
    def octave(self):
        # Temporary fix, TODO: properly handle multiple octaves
        return next(iter(self.octaves.values())) if self.octaves else None

    @property
    def initial_quam(self) -> "SQuIDRoot1":
        if self._initial_quam is None:
            self._initial_quam = self.load(self.information.state_path)
        return self._initial_quam

    @property
    def config(self) -> dict:
        if self._config is None:
            self._config = self.generate_config()
        return self._config

    @property
    def qm(self) -> QuantumMachine:
        if self._qm is None:
            self._qm = self.qmm.open_qm(self.config)
        return self._qm

    @property
    def qmm(self) -> QuantumMachinesManager:
        if self._qmm is None:
            self._qmm = QuantumMachinesManager(
                host=self.network.host,
                cluster_name=self.network.cluster_name,
                octave=self.octave.get_octave_config() if self.octave else None,
            )
        return self._qmm

    def set_default_gate_shape(self, gate_shape: str) -> None:
        """Set the default gate shape for all qubits.

        Args:
            gate_shape: The default gate shape to set.
        """
        for qubit in self.qubits.values():
            qubit.set_default_gate_shape(gate_shape)

    def print_info(self) -> None:
        self.information.print_info()

    def close_qm(self) -> None:
        """Close the Quantum Machine."""
        if self.qm is not None:
            self.qm.close()

    def save(
        self,
        path=None,
        content_mapping: Dict[str, str] = None,
        include_defaults: bool = True,
        ignore: Sequence[str] = None,
    ) -> None:
        """Save the entire QuamRoot object to a file. This includes nested objects.

        Args:
            content_mapping: A dictionary of paths to save to and a list of attributes
                to save to that path. This can be used to save different parts of the
                QuamRoot object to different files.
            include_defaults: Whether to include attributes that have the default
                value.
            ignore: A list of attributes to ignore.
        """

        if path is None:
            if self.information.state_path is None:
                raise ValueError(
                    "The state_path in information must be set before saving."
                )
            path = self.information.state_path

        if content_mapping is None:
            content_mapping = {
                "wiring.json": "wiring",
                "network.json": "network",
                "information.json": "information",
            }

        super().save(
            path=path,
            content_mapping=content_mapping,
            include_defaults=include_defaults,
            ignore=ignore,
        )

    @classmethod
    def generate_empty_quam_single_feedline(
        n_qubits: int,
        wiring: OPXWiring,
        network: OPXNetwork,
        information: Information,
        resonator_frequencies_bare: Sequence[float] = None,
        resonator_frequencies_coupled: Sequence[float] = None,
        qubit_frequencies: Sequence[float] = None,
        drive_lo_frequencies: Sequence[float] = None,
        readout_lo_frequency: float = None,
        gate_length: int = 40,
        pi_pulse_amplitude: float = 0.4,
        readout_length: int = 1000,
        readout_amplitude: float = 0.1,
    ) -> "SQuIDRoot1":
        """Generate an empty QuAM object with a given number of qubits.

        Args:
            n_qubits (int): The number of qubits to generate.

        Returns:
            QuAM: An empty QuAM object.
        """

        machine = SQuIDRoot1(wiring=wiring, network=network, information=information)

        octaves = {
            "octave1": OctaveSQuID(
                ip=machine.network.octave_networks["octave1"].get_reference(
                    "octave_host"
                ),
                port=machine.network.octave_networks["octave1"].get_reference(
                    "octave_port"
                ),
            )
        }
        machine.octaves = octaves

        readout_up_converter = OctaveUpConverterSQuID(LO_frequency=readout_lo_frequency)
        octaves["octave1"].RF_outputs[1] = readout_up_converter

        readout_down_converter = OctaveDownConverterSQuID(
            LO_frequency=readout_up_converter.get_reference("LO_frequency"),
        )
        octaves["octave1"].RF_inputs[1] = readout_down_converter

        qubit_names = machine.wiring.drive_lines.keys()

        machine.shared_qubit_parameters = {
            "drag_gaussian_pulse_parameters": {
                "length": gate_length,
                "subtracted": True,
                "sigma_to_length_ratio": 0.2,
            },
        }

        for idx, qubit_name in enumerate(qubit_names):
            # Add driving frequency converter
            drive_up_converter = OctaveUpConverterSQuID(
                LO_frequency=drive_lo_frequencies
            )
            octaves["octave1"].RF_outputs[idx + 2] = drive_up_converter

            # Add qubit
            qubit = ScQubit(
                xy=IQChannel(
                    opx_output_I=f"#/wiring/drive_lines/{qubit_name}/port_I",
                    opx_output_Q=f"#/wiring/drive_lines/{qubit_name}/port_Q",
                    frequency_converter_up=drive_up_converter.get_reference(),
                    intermediate_frequency="#/inferred_intermediate_frequency",
                    RF_frequency=qubit_frequencies[idx],
                ),
                resonator=ReadoutResonator(
                    channel=InOutIQChannel(
                        opx_input_I=f"#/wiring/feed_lines/feedline/input_I",
                        opx_input_Q=f"#/wiring/feed_lines/feedline/input_Q",
                        opx_output_I=f"#/wiring/feed_lines/feedline/output_I",
                        opx_output_Q=f"#/wiring/feed_lines/feedline/output_Q",
                        frequency_converter_up=readout_up_converter.get_reference(),
                        frequency_converter_down=readout_down_converter.get_reference(),
                    ),
                    frequency_bare=resonator_frequencies_bare[idx],
                    frequency_q0=resonator_frequencies_coupled[idx],
                ),
                transition_frequencies=[qubit_frequencies[idx]],
            )

            qubit.pulse_sets = {
                "drag_gaussian": PulseSetDragGaussian(
                    amplitude_180=pi_pulse_amplitude,
                    amplitude_90=pi_pulse_amplitude / 2,
                    length=machine.shared_qubit_parameters[
                        "drag_gaussian_pulse_parameters"
                    ].get_reference("length"),
                    subtracted=machine.shared_qubit_parameters[
                        "drag_gaussian_pulse_parameters"
                    ].get_reference("subtracted"),
                    anharmonicity="#../../anharmonicity",
                    sigma_to_length_ratio=machine.shared_qubit_parameters[
                        "drag_gaussian_pulse_parameters"
                    ].get_reference("sigma_to_length_ratio"),
                ),
                "flattop_cosine": PulseSetFlattopCosine(
                    amplitude=0.4,
                    rise_fall_time=16,
                ),
            }

            machine.qubits[qubit_name] = qubit
            qubit.pulse_sets["drag_gaussian"].add_drive_pulses()
            qubit.pulse_sets["flattop_cosine"].add_drive_pulses()

            qubit.resonator.channel.operations["readout"] = SquareReadoutPulse(
                length=readout_length,
                amplitude=readout_amplitude,
                threshold=0.0,
                digital_marker="ON",
            )

        return machine
