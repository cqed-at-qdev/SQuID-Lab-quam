try:
    import Labber
except ModuleNotFoundError:
    pass
from quam.components.hardware import LocalOscillator
from quam.core import QuamComponent, quam_dataclass

__all__ = ["LabberServer", "LabberInstrument", "RhodeSchwarzLocalOscillator"]


@quam_dataclass
class LabberServer(QuamComponent):
    """QuAM component for a Labber Server."""

    _client = None

    @property
    def client(self):
        """Return the Labber client object."""
        if self._client is None:
            self._client = Labber.connectToServer("localhost")
        return self._client

    def connect_instrument(self, name: str, ip: str, interface: str = "TCPIP"):
        """Connect to an instrument"""
        return self.client.connectToInstrument(
            name, dict(interface=interface, address=ip)
        )

    def set_value(self, instrument, parameter, value):
        """Set a value on an instrument"""
        instrument.setValue(parameter, value)


@quam_dataclass
class LabberInstrument(QuamComponent):
    """Base class QuAM component for instruments controlled via Labber api."""

    ip: str
    instrument_name: str
    labber_server: LabberServer = None
    _instrument = None

    @property
    def instrument(self):
        """Return the instrument object."""
        if self._instrument is None:
            self._instrument = self.labber_server.connect_instrument(
                self.instrument_name, self.ip
            )
        return self._instrument

    def set_value(self, parameter, value):
        """Set a value on the instrument."""
        self.instrument.setValue(parameter, value)


@quam_dataclass
class RhodeSchwarzLocalOscillator(LocalOscillator, LabberInstrument):
    """QuAM component for a Rhode & Schwarz local oscillator with Labber interface."""

    instrument_name: str = "Rohde&Schwarz RF Source"

    def initialize(self):
        """Initialize the power and frequency of local oscillator."""
        self.set_power(self.power)
        self.set_frequency(self.frequency)

    def set_power(self, power: float):
        """Set the power of the local oscillator."""
        self.set_value("Power", power)

    def set_frequency(self, frequency: float):
        """Set the frequency of the local oscillator."""
        self.set_value("Frequency", frequency)

    def set_output(self, state: bool):
        """Turn the local oscillator on or off."""
        self.set_value("Output", state)
