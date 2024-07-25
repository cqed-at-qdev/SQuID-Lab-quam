import pytest

from squid_lab_quam.components.qubits import ScQubit
from squid_lab_quam.components.resonators import ReadoutResonator
from squid_lab_quam.components.roots import SQuIDRoot1
from squid_lab_quam.utils.name_from_parent import (
    get_name_from_parent,
    index_from_parent_list,
    key_from_parent_dict,
    name_from_parent_component,
)


class TestKeyFromParentDict:
    quam = SQuIDRoot1()
    qubit = quam.qubits["q1"] = ScQubit()

    def test_key_from_parent_dict(self):
        assert key_from_parent_dict(self.qubit) == "q1"

    def test_added_exstra_qubit(self):
        qubit2 = self.quam.qubits["q2"] = ScQubit()
        assert key_from_parent_dict(qubit2) == "q2"
        assert key_from_parent_dict(self.qubit) == "q1"

    def test_key_from_parent_dict_raises(self):
        with pytest.raises(ValueError):
            key_from_parent_dict(self.quam)  # type: ignore


class TestIndexFromParentList:
    quam = SQuIDRoot1()
    quam.qubit_list = []
    qubit = ScQubit()
    quam.qubit_list.append(qubit)

    def test_index_from_parent_list(self):
        assert index_from_parent_list(self.qubit) == 0

    def test_added_exstra_qubit(self):
        qubit2 = ScQubit()
        self.quam.qubit_list.append(qubit2)
        assert index_from_parent_list(qubit2) == 1
        assert index_from_parent_list(self.qubit) == 0

    def test_added_exstra_qubit_infront(self):
        qubit2 = ScQubit()
        self.quam.qubit_list.insert(0, qubit2)
        assert index_from_parent_list(qubit2) == 0
        assert index_from_parent_list(self.qubit) == 1

    def test_index_from_parent_list_raises(self):
        with pytest.raises(ValueError):
            index_from_parent_list(self.quam)  # type: ignore


class TestNameFromComponent:
    quam = SQuIDRoot1()
    qubit = quam.qubits["q1"] = ScQubit()
    resonator = qubit.resonator = ReadoutResonator(channel="Dummy")  # type: ignore

    def test_name_from_parent_component_resonator(self):
        assert name_from_parent_component(self.resonator) == "resonator"

    def test_name_from_parent_component_new_attribute(self):
        resonator2 = self.qubit.new_resonator = ReadoutResonator(channel="Dummy")  # type: ignore
        assert name_from_parent_component(resonator2) == "new_resonator"

    def test_name_from_parent_component_qubit(self):
        with pytest.raises(ValueError):
            name_from_parent_component(self.qubit)


class TestGetNameFromParent:
    quam = SQuIDRoot1()
    qubit = quam.qubits["q1"] = ScQubit()
    resonator = qubit.resonator = ReadoutResonator(channel="Dummy")  # type: ignore
    quam.qubit_list = []
    qubit_in_list = ScQubit()
    quam.qubit_list.append(qubit_in_list)

    def test_get_name_from_parent_resonator(self):
        assert get_name_from_parent(self.resonator) == "resonator"

    def test_get_name_from_parent_new_attribute(self):
        resonator2 = self.qubit.new_resonator = ReadoutResonator(channel="Dummy")  # type: ignore
        assert get_name_from_parent(resonator2) == "new_resonator"

    def test_get_name_from_parent_qubit(self):
        assert get_name_from_parent(self.qubit) == "q1"

    def test_get_name_from_parent_qubit_in_list(self):
        assert get_name_from_parent(self.qubit_in_list) == "0"

    def test_get_name_from_parent_raises(self):
        with pytest.raises(ValueError):
            get_name_from_parent(self.quam)  # type: ignore
