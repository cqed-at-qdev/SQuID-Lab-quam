from dataclasses import field
from typing import ClassVar, Dict, Sequence

from qm import QuantumMachine
from qm.qua import align
from qm.QuantumMachinesManager import QuantumMachinesManager
from quam.core import QuamRoot, quam_dataclass

from squid_lab_quam.components.information import Information
from squid_lab_quam.components.network import OPXNetwork
from squid_lab_quam.components.octave import OctaveSQuID
from squid_lab_quam.components.qubits import Transmon
from squid_lab_quam.components.wiring import OPXWiring

__all__ = ["QuAMSCQ1"]


@quam_dataclass
class QuAMSCQ1(QuamRoot):
    """SQuID Lab QuAM root type 1 for superconducting qubits."""

    @classmethod
    def load(cls, *args, **kwargs) -> "QuAMSCQ1":
        return super().load(*args, **kwargs)

    wiring: OPXWiring = field(default_factory=OPXWiring)
    network: OPXNetwork = field(default_factory=OPXNetwork)
    information: Information = field(default_factory=Information)
    qubits: Dict[str, Transmon] = field(default_factory=dict)
    shared_qubit_parameters: dict = field(default_factory=dict)
    octaves: Dict[str, OctaveSQuID] = field(default_factory=dict)

    _qm: ClassVar[QuantumMachine] = None
    _qmm: ClassVar[QuantumMachinesManager] = None
    _config: ClassVar[dict] = None
    _initial_quam: ClassVar["QuAMSCQ1"] = None

    @property
    def octave(self):
        # Temporary fix, TODO: properly handle multiple octaves
        return next(iter(self.octaves.values())) if self.octaves else None

    @property
    def initial_quam(self) -> "QuAMSCQ1":
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
    def generate_empty_quam(n_qubits: int, n_feedlines: int = 1) -> "QuAMSCQ1":
        """Generate an empty QuAM object with a given number of qubits.

        Args:
            n_qubits (int): The number of qubits to generate.

        Returns:
            QuAM: An empty QuAM object.
        """
        raise NotImplementedError
