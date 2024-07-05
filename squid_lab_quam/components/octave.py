from typing import Dict, Literal, Union

from qm.octave.qm_octave import QmOctave
from quam.components.channels import IQChannel
from quam.components.octave import Octave, OctaveDownConverter, OctaveUpConverter
from quam.core import quam_dataclass

from squid_lab_quam.utils import key_from_parent_dict


@quam_dataclass
class OctaveUpConverterSQuID(OctaveUpConverter):
    """Modified OctaveUpConverter which can set LO frequency and gain.

    The OctaveUpConverter represents a frequency upconverter in the QM Octave. Usually
    an IQChannel is connected `OctaveUpconverter.channel`, in which case the two OPX
    outputs are connected to the I and Q inputs of the OctaveUpConverter.
    The OPX outputs are specified in the `OctaveUpConverter.channel` attribute.
    The channel is either an IQChannel or a SingleChannel.

    Args:
        id: The RF output id, must be between 1-5.
        LO_frequency: The local oscillator frequency in Hz, between 2 and 18 GHz.
        LO_source: The local oscillator source, "internal" (default) or "external".
        gain: The gain of the output, between -20 and 20 dB in steps of 0.5.
            Default is 0 dB.
        output_mode: Sets the fast switch's mode of the up converter module.
            Can be "always_on" / "always_off" / "triggered" / "triggered_reversed".
            The default is "always_on".
            - "always_on" - Output is always on
            - "always_off" - Output is always off
            - "triggered" - The output will play when rising edge is detected in the
              octave's digital port.
            - "triggered_reversed" - The output will play when falling edge is detected
              in the octave's digital port.
        input_attenuators: Whether the I and Q ports have a 10 dB attenuator before
            entering the mixer. Off by default.
    """

    id: Union[int, str] = "#./id_from_parent_dict"
    output_mode: Literal[
        "always_on", "always_off", "triggered", "triggered_reversed"
    ] = "always_on"

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

    # def find_opx_outputs(self) -> dict[Literal["I", "Q"], tuple[str, int]]:
    #     opx_outputs = {"I": None, "Q": None}
    #     for component in self._root.iterate_components():
    #         for attr_value in component.get_attrs().values():
    #             if attr_value == self.get_reference():
    #                 for I_or_Q in ("I", "Q"):
    #                     if opx_outputs[I_or_Q] is None:
    #                         opx_outputs[I_or_Q] = getattr(
    #                             component, f"opx_output_{I_or_Q}"
    #                         )
    #                     elif opx_outputs[I_or_Q] != getattr(
    #                         component, f"opx_output_{I_or_Q}"
    #                     ):
    #                         raise ValueError(
    #                             f"Error: OctaveUpConverter {self.id} is connected to "
    #                             f"multiple OPX output {I_or_Q} ports."
    #                         )

    #     for I_or_Q in ("I", "Q"):
    #         if opx_outputs[I_or_Q] is None:
    #             raise ValueError(
    #                 f"Error: OctaveUpConverter {self.id} is not connected to any OPX output {I_or_Q} port."
    #             )
    #     return opx_outputs

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
    """Modified OctaveUpConverter which can set LO frequency and gain and doesn't need a channel or id.

    The OctaveDownConverter represents a frequency downconverter in the QM Octave. The
    OctaveDownConverter is usually connected to an InOutIQChannel, in which case the
    two OPX inputs are connected to the IF outputs of the OctaveDownConverter. The
    OPX inputs are specified in the `OctaveDownConverter.channel` attribute. The
    channel is either an InOutIQChannel or an InOutSingleChannel.

    Args:
        id: The RF input id, must be between 1-2.
        LO_frequency: The local oscillator frequency in Hz, between 2 and 18 GHz.
        LO_source: The local oscillator source, "internal" or "external.
            For down converter 1 "internal" is the default,
            for down converter 2 "external" is the default.
        IF_mode_I: Sets the mode of the I port of the IF Down Converter module as can be
            seen in the octave block diagram (see Octave page in QUA documentation).
            Can be "direct" / "envelope" / "mixer" / "off". The default is "direct".
            - "direct" - The signal bypasses the IF module.
            - "envelope" - The signal passes through an envelope detector.
            - "mixer" - The signal passes through a low-frequency mixer.
            - "off" - the signal doesn't pass to the output port.
        IF_mode_Q: Sets the mode of the Q port of the IF Down Converter module.
        IF_output_I: The output port of the IF Down Converter module for the I port.
            Can be 1 or 2. The default is 1. This will be 2 if the IF outputs
            are connected to the opposite OPX inputs
        IF_output_Q: The output port of the IF Down Converter module for the Q port.
            Can be 1 or 2. The default is 2. This will be 1 if the IF outputs
            are connected to the opposite OPX inputs.
    """

    id: Literal[1, 2] = "#./id_from_parent_dict"

    @property
    def id_from_parent_dict(self) -> int:
        return int(key_from_parent_dict(self))

    def find_opx_inputs(self) -> dict[Literal["I", "Q"], tuple[str, int]]:
        for component in self._root.iterate_components():
            if not isinstance(component, IQChannel):
                continue
            if component.frequency_converter_down == self:
                return {
                    "I": component.opx_input_I,
                    "Q": component.opx_input_Q,
                }

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
    """Modified Octave class with a qm property.

    The QM Octave is a device that can be used to upconvert and downconvert signals. It
    has 5 RF outputs and 2 RF inputs. Each RF_output has an associated
    `OctaveUpConverter`, and similarly each RF_input has an `OctaveDownConverter`.

    In many cases the Octave is connected to a single OPX in the default configuration,
    i.e. OPX outputs are connected to the corresponding Octave I/Q input, and Octave IF
    outputs are connected to the corresponding OPX input. In this case you can configure
    the Octave with the correct `FrequencyConverter`s using
    `Octave.initialize_default_connectivity()`.

    Args:
        name: The name of the Octave. Must be unique
        ip: The IP address of the Octave. Used in `Octave.get_octave_config()`
        port: The port number of the Octave. Used in `Octave.get_octave_config()`
        calibration_db_path: The path to the calibration database. If not specified, the
            current working directory is used.
        RF_outputs: A dictionary of `OctaveUpConverter` objects. The keys are the
            output numbers (1-5).
        RF_inputs: A dictionary of `OctaveDownConverter` objects. The keys are the
            input numbers (1-2).
        loopbacks: A list of loopback connections, for example to connect a local
            oscillator. See the QUA Octave documentation for details.
    """

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
