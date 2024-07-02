from typing import Dict, Literal, Union

from qm.octave.qm_octave import QmOctave
from quam.components.channels import IQChannel
from quam.components.octave import Octave, OctaveDownConverter, OctaveUpConverter
from quam.core import quam_dataclass

from squid_lab_quam.utils import key_from_parent_dict


@quam_dataclass
class OctaveUpConverterSQuID(OctaveUpConverter):
    """Modified OctaveUpConverter which can set LO frequency and gain."""

    id: Union[int, str] = "#./id_from_parent_dict"

    @property
    def id_from_parent_dict(self) -> str:
        return str(key_from_parent_dict(self))

    @property
    def default_element(self) -> str:
        return f"__oct__{self.octave.name}_{self.id}_IQmixer"
        ## #TODO: maybe get from config instead or quam

    def find_opx_outputs(self) -> dict[Literal["I", "Q"], tuple[str, int]]:
        for component in self._root.iterate_components():
            if not isinstance(component, IQChannel):
                continue
            if component.frequency_converter_up == self:
                return {
                    "I": component.opx_output_I,
                    "Q": component.opx_output_Q,
                }

    def find_opx_outputs(self) -> dict[Literal["I", "Q"], tuple[str, int]]:
        opx_outputs = {"I": None, "Q": None}
        for component in self._root.iterate_components():
            for attr_value in component.get_attrs().values():
                if attr_value == self.get_reference():
                    for I_or_Q in ("I", "Q"):
                        if opx_outputs[I_or_Q] is None:
                            opx_outputs[I_or_Q] = getattr(
                                component, f"opx_output_{I_or_Q}"
                            )
                        elif opx_outputs[I_or_Q] != getattr(
                            component, f"opx_output_{I_or_Q}"
                        ):
                            raise ValueError(
                                f"Error: OctaveUpConverter {self.id} is connected to "
                                f"multiple OPX output {I_or_Q} ports."
                            )

        for I_or_Q in ("I", "Q"):
            if opx_outputs[I_or_Q] is None:
                raise ValueError(
                    f"Error: OctaveUpConverter {self.id} is not connected to any OPX output {I_or_Q} port."
                )
        return opx_outputs

    def set_lo_frequency(self, frequency: float) -> None:
        self.octave.qm_octave.set_lo_frequency(self.default_element, frequency)

    def set_gain(self, gain: float) -> None:
        self.octave.qm_octave.set_rf_output_gain(self.default_element, gain)

    def apply_to_config(self, config: Dict) -> None:
        """Add information about the frequency up-converter to the QUA config

        This method is called by the `QuamComponent.generate_config` method.

        Nothing is added to the config if the `OctaveUpConverter.channel` is not
        specified or if the `OctaveUpConverter.LO_frequency` is not specified.

        Args:
            config: A dictionary representing a QUA config file.

        Raises:
            ValueError: If the LO_frequency is not specified.
            KeyError: If the Octave is not in the config, or if config["octaves"] does
                not exist.
            KeyError: If the Octave already has an entry for the OctaveUpConverter.
        """
        if not isinstance(self.LO_frequency, (int, float)):
            raise ValueError(
                f"Error generating config for Octave upconverter id={self.id}: "
                "LO_frequency must be specified."
            )

        super(OctaveUpConverter, self).apply_to_config(config)

        if self.id in config["octaves"][self.octave.name]["RF_outputs"]:
            raise KeyError(
                f"Error generating config: "
                f'config["octaves"]["{self.octave.name}"]["RF_outputs"] '
                f'already has an entry for OctaveDownConverter with id "{self.id}"'
            )

        output_config = config["octaves"][self.octave.name]["RF_outputs"][self.id] = {
            "LO_frequency": self.LO_frequency,
            "LO_source": self.LO_source,
            "gain": self.gain,
            "output_mode": self.output_mode,
            "input_attenuators": self.input_attenuators,
        }

        opx_output_I, opx_output_Q = self.find_opx_outputs().values()

        output_config["I_connection"] = tuple(opx_output_I)
        output_config["Q_connection"] = tuple(opx_output_Q)


@quam_dataclass
class OctaveDownConverterSQuID(OctaveDownConverter):
    """Modified OctaveUpConverter which can set LO frequency and gain and doesn't need a channel or id."""

    id: Union[int, str] = "#./id_from_parent_dict"

    @property
    def id_from_parent_dict(self) -> str:
        return str(key_from_parent_dict(self))

    def find_opx_inputs(self) -> dict[Literal["I", "Q"], tuple[str, int]]:
        opx_inputs = {"I": None, "Q": None}
        for component in self._root.iterate_components():
            for attr_value in component.get_attrs().values():
                if attr_value == self.get_reference():
                    for I_or_Q in ("I", "Q"):
                        if opx_inputs[I_or_Q] is None:
                            opx_inputs[I_or_Q] = getattr(
                                component, f"opx_input_{I_or_Q}"
                            )
                        elif opx_inputs[I_or_Q] != getattr(
                            component, f"opx_input_{I_or_Q}"
                        ):
                            raise ValueError(
                                f"Error: OctaveUpConverter {self.id} is connected to "
                                f"multiple OPX input {I_or_Q} ports."
                            )

        for I_or_Q in ("I", "Q"):
            if opx_inputs[I_or_Q] is None:
                raise ValueError(
                    f"Error: OctaveUpConverter {self.id} is not connected to any OPX input {I_or_Q} port."
                )
        return opx_inputs

    def apply_to_config(self, config: Dict) -> None:
        """Add information about the frequency down-converter to the QUA config

        This method is called by the `QuamComponent.generate_config` method.

        Nothing is added to the config if the `OctaveDownConverter.channel` is not
        specified or if the `OctaveDownConverter.LO_frequency` is not specified.

        Args:
            config: A dictionary representing a QUA config file.

        Raises:
            ValueError: If the LO_frequency is not specified.
            KeyError: If the Octave is not in the config, or if config["octaves"] does
                not exist.
            KeyError: If the Octave already has an entry for the OctaveDownConverter.
            ValueError: If the IF_output_I and IF_output_Q are already assigned to
                other ports.
        """
        if not isinstance(self.LO_frequency, (int, float)):
            raise ValueError(
                f"Error generating config for Octave upconverter id={self.id}: "
                "LO_frequency must be specified."
            )

        super(OctaveDownConverter, self).apply_to_config(config)

        if self.id in config["octaves"][self.octave.name]["RF_inputs"]:
            raise KeyError(
                f"Error generating config: "
                f'config["octaves"]["{self.octave.name}"]["RF_inputs"] '
                f'already has an entry for OctaveDownConverter with id "{self.id}"'
            )

        config["octaves"][self.octave.name]["RF_inputs"][self.id] = {
            "RF_source": "RF_in",
            "LO_frequency": self.LO_frequency,
            "LO_source": self.LO_source,
            "IF_mode_I": self.IF_mode_I,
            "IF_mode_Q": self.IF_mode_Q,
        }

        IF_channels = [self.IF_output_I, self.IF_output_Q]
        opx_channels = self.find_opx_inputs().values()

        IF_config = config["octaves"][self.octave.name]["IF_outputs"]
        for k, (IF_ch, opx_ch) in enumerate(zip(IF_channels, opx_channels), start=1):
            label = f"IF_out{IF_ch}"
            IF_config.setdefault(label, {"port": tuple(opx_ch), "name": f"out{k}"})
            if IF_config[label]["port"] != tuple(opx_ch):
                raise ValueError(
                    f"Error generating config for Octave downconverter id={self.id}: "
                    f"Unable to assign {label} to  port {opx_ch} because it is already "
                    f"assigned to port {IF_config[label]['port']} "
                )


@quam_dataclass
class OctaveSQuID(Octave):
    """Modified Octave class with a qm property."""

    name: str = "#./name_from_parent_dict"

    @property
    def name_from_parent_dict(self) -> str:
        return str(key_from_parent_dict(self))

    @property
    def qm_octave(self) -> QmOctave:
        return self._root.qm.octave

    def initialize_frequency_converters(self):
        """Initialize the Octave frequency converters with default connectivity.

        This method initializes the Octave with default connectivity, i.e. it connects
        the Octave to a single OPX. It creates an `OctaveUpConverter` for each RF output
        and an `OctaveDownConverter` for each RF input. The `OctaveUpConverter` objects
        are added to `Octave.RF_outputs` and the `OctaveDownConverter` objects are added
        to `Octave.RF_inputs`.

        Raises:
            ValueError: If the Octave already has RF_outputs or RF_inputs.

        """
        if self.RF_outputs:
            raise ValueError(
                "Error initializing Octave with default connectivity. "
                "octave.RF_outputs is not empty"
            )
        if self.RF_inputs:
            raise ValueError(
                "Error initializing Octave with default connectivity. "
                "octave.IF_outputs is not empty"
            )

        for idx in range(1, 6):
            self.RF_outputs[idx] = OctaveUpConverterSQuID(
                id=idx,
            )

        for idx in range(1, 3):
            self.RF_inputs[idx] = OctaveDownConverterSQuID(id=idx)
