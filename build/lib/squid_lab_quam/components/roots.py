from dataclasses import field
from typing import Dict, Sequence

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

    # TODO: hide these attributes in hinting
    _qm: QuantumMachine = None
    _qmm: QuantumMachinesManager = None
    _config: dict = None

    @property
    def initial_quam(self):
        if hasattr(self, "_initial_quam"):
            return self._initial_quam
        else:
            self._initial_quam = self.load(self.information.state_path)
            return self._initial_quam

    @property
    def config(self):
        if self._config is None:
            self._config = self.generate_config()
        return self._config

    @property
    def qm(self):
        if self._qm is None:
            self._qm = self.qmm.open_qm(self.config)
        return self._qm

    @property
    def qmm(self):
        if self._qmm is None:
            self._qmm = QuantumMachinesManager(
                host=self.network.host,
                cluster_name=self.network.cluster_name,
                octave=self.octave.get_octave_config() if self.octave else None,
            )
        return self._qmm

    def print_info(self):
        self.information.print_info()

    def close_qm(self):
        """Close the Quantum Machine."""
        if self.qm is not None:
            self.qm.close()

    def save(
        self,
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
        if self.information.state_path is None:
            raise ValueError("The state_path in information must be set before saving.")

        if ignore is None:
            ignore = ["_qm", "_config"]
        else:
            ignore = list(ignore) + ["_qm", "_config"]

        if content_mapping is None:
            content_mapping = {
                "wiring.json": "wiring",
                "network.json": "network",
                "information.json": "information",
            }

        super().save(
            path=self.information.state_path,
            content_mapping=content_mapping,
            include_defaults=include_defaults,
            ignore=ignore,
        )

    @classmethod
    def generate_empty_quam(n_qubits: int, n_feedlines: int = 1) -> "QuAM":
        """Generate an empty QuAM object with a given number of qubits.

        Args:
            n_qubits (int): The number of qubits to generate.

        Returns:
            QuAM: An empty QuAM object.
        """
        raise NotImplementedError
