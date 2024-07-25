from dataclasses import field
from typing import ClassVar, Dict, List, Optional, Sequence

from qm import QuantumMachine, QuantumMachinesManager
from qm.api.models.compiler import CompilerOptionArguments
from qm.jobs.running_qm_job import RunningQmJob
from qm.program import Program
from qm.simulate.interface import SimulationConfig
from quam.components.channels import InOutIQChannel, IQChannel
from quam.components.pulses import SquareReadoutPulse
from quam.core import QuamDict, QuamRoot, quam_dataclass

from quam_squid_lab.components.information import Information
from quam_squid_lab.components.network import OPXNetwork
from quam_squid_lab.components.octave import (
    OctaveDownConverterSQuID,
    OctaveSQuID,
    OctaveUpConverterSQuID,
)
from quam_squid_lab.components.pulse_sets import (
    PulseSetDragGaussian,
    PulseSetFlattopCosine,
)
from quam_squid_lab.components.qubits import ScQubit
from quam_squid_lab.components.resonators import ReadoutResonator
from quam_squid_lab.components.wiring import OPXWiring

__all__ = ["SQuIDRoot1"]


@quam_dataclass
class SQuIDRoot1(QuamRoot):
    """SQuID Lab QuAM root type 1 for superconducting qubits."""

    @classmethod
    def load(cls, *args, **kwargs) -> "SQuIDRoot1":
        return super().load(*args, **kwargs)

    information: Information = field(default_factory=Information)
    network: OPXNetwork = field(default_factory=OPXNetwork)
    wiring: OPXWiring = field(default_factory=OPXWiring)
    octaves: Dict[str, OctaveSQuID] = field(default_factory=dict)
    qubits: dict[str, ScQubit] = field(default_factory=dict)
    shared_qubit_parameters: dict = field(default_factory=dict)

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

    @property
    def resonators(self) -> dict[str, ReadoutResonator]:
        return {
            qubit_name: qubit.resonator for qubit_name, qubit in self.qubits.items()
        }

    def execute(
        self,
        program: Program,
        simulate: Optional[SimulationConfig] = None,
        compiler_options: Optional[CompilerOptionArguments] = None,
        strict: Optional[bool] = None,
        flags: Optional[List[str]] = None,
    ) -> RunningQmJob:
        """Executes a program and returns a job object to keep track of execution and get
        results.

        Note:

            Calling execute will halt any currently running program and clear the current
            queue. If you want to add a job to the queue, use .qm.queue.add()

        Args:
            program: A QUA ``program()`` object to execute
            simulate: Not documented by QM api
            compiler_options: Not documented by QM api
            strict: Not documented by QM api
            flags: Not documented by QM api

        Returns:
            A ``QmJob`` object (see QM Job API).
        """
        return self.qm.execute(
            program,
            simulate=simulate,
            compiler_options=compiler_options,
            strict=strict,
            flags=flags,
        )

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
        content_mapping: Optional[Dict[str, str]] = None,
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
        cls,
        wiring: OPXWiring,
        network: OPXNetwork,
        information: Information,
        resonator_frequencies_bare: Optional[dict[str, float]] = None,
        resonator_frequencies_coupled: Optional[dict[str, float]] = None,
        qubit_frequencies: Optional[dict[str, float]] = None,
        drive_lo_frequencies: Optional[dict[str, float]] = None,
        readout_lo_frequency: float = 6e9,
        gate_length: int = 40,
        pi_pulse_amplitude: float = 0.4,
        readout_length: int = 1000,
        readout_amplitude: float = 0.1,
    ) -> "SQuIDRoot1":
        """Generate an empty QuAM object from wiring, network and information.

        Args:

        Returns:
            QuAM: An empty QuAM object.
        """

        if len(wiring.feed_lines) != 1:
            raise ValueError(
                f"Single feedline wiring required for this method. Found {len(wiring.feed_lines)} feedlines, [{', '.join(wiring.feed_lines.keys())}]"
            )
        feedline = next(iter(wiring.feed_lines.values()))

        machine = SQuIDRoot1(wiring=wiring, network=network, information=information)

        # Set up octave
        octave = OctaveSQuID(
            ip=machine.network.octave_networks["octave1"].get_reference("octave_host"),
            port=machine.network.octave_networks["octave1"].get_reference(
                "octave_port"
            ),
            calibration_db_path=machine.information.get_reference(
                "calibration_db_path"
            ),
        )
        machine.octaves = {"octave1": octave}

        readout_up_converter = OctaveUpConverterSQuID(LO_frequency=readout_lo_frequency)
        octave.RF_outputs[feedline.default_octave_port_in()] = readout_up_converter

        readout_down_converter = OctaveDownConverterSQuID(
            LO_frequency=readout_up_converter.get_reference("LO_frequency"),
        )
        octave.RF_inputs[feedline.default_octave_port_out()] = readout_down_converter

        # Set up qubits
        qubit_names = machine.wiring.drive_lines.keys()

        if resonator_frequencies_bare is None:
            resonator_frequencies_bare = {
                qubit_name: readout_lo_frequency for qubit_name in qubit_names
            }

        if resonator_frequencies_coupled is None:
            resonator_frequencies_coupled = {
                qubit_name: readout_lo_frequency for qubit_name in qubit_names
            }

        if drive_lo_frequencies is None:
            drive_lo_frequencies = {
                qubit_name: readout_lo_frequency for qubit_name in qubit_names
            }

        if qubit_frequencies is None:
            qubit_frequencies = drive_lo_frequencies

        machine.shared_qubit_parameters = QuamDict(
            {
                "drag_gaussian_pulse_parameters": {
                    "length": gate_length,
                    "subtracted": True,
                    "sigma_to_length_ratio": 0.2,
                },
            }
        )

        for qubit_name in qubit_names:
            # Add driving frequency converter
            drive_up_converter = OctaveUpConverterSQuID(
                LO_frequency=drive_lo_frequencies[qubit_name]
            )
            octave.RF_outputs[wiring.drive_lines[qubit_name].default_octave_port()] = (
                drive_up_converter
            )

            # Add qubit
            qubit = ScQubit(
                xy=IQChannel(
                    opx_output_I=wiring.drive_lines[qubit_name].get_reference("port_I"),
                    opx_output_Q=wiring.drive_lines[qubit_name].get_reference("port_Q"),
                    frequency_converter_up=drive_up_converter.get_reference(),
                    intermediate_frequency="#./inferred_intermediate_frequency",
                    RF_frequency=qubit_frequencies[qubit_name],
                ),
                resonator=ReadoutResonator(
                    channel=InOutIQChannel(
                        opx_input_I=feedline.get_reference("input_I"),
                        opx_input_Q=feedline.get_reference("input_Q"),
                        opx_output_I=feedline.get_reference("output_I"),
                        opx_output_Q=feedline.get_reference("output_Q"),
                        frequency_converter_up=readout_up_converter.get_reference(),
                        frequency_converter_down=readout_down_converter.get_reference(),
                        intermediate_frequency="#./inferred_intermediate_frequency",
                        RF_frequency=resonator_frequencies_coupled[qubit_name],
                    ),
                    frequency_bare=resonator_frequencies_bare[qubit_name],
                    frequency_q0=resonator_frequencies_coupled[qubit_name],
                ),
                transition_frequencies=[qubit_frequencies[qubit_name]],
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
            )

        return machine
