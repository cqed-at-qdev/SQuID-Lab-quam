from dataclasses import field
from typing import Any, Dict

from quam.core import QuamComponent, quam_dataclass

from squid_lab_quam.components.qubits import ScQubit
from squid_lab_quam.components.tunable_coupler import TunableCoupler

__all__ = ["QubitPair"]


@quam_dataclass
class QubitPair(QuamComponent):
    qubit_control: ScQubit
    qubit_target: ScQubit
    coupler: TunableCoupler = None

    extras: Dict[str, Any] = field(default_factory=dict)
