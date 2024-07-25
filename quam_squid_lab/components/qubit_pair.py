from dataclasses import field
from typing import Any, Dict

from quam.core import QuamComponent, quam_dataclass

from quam_squid_lab.components.qubits import ScQubit
from quam_squid_lab.components.tunable_coupler import TunableCoupler

__all__ = ["QubitPair"]


@quam_dataclass
class QubitPair(QuamComponent):
    qubit_control: ScQubit
    qubit_target: ScQubit
    coupler: TunableCoupler = None

    extras: Dict[str, Any] = field(default_factory=dict)
