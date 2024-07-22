from typing import Callable, Literal

from qm.qua import QuaVariableType, align, assign, declare, fixed, wait, while_
from quam import QuamComponent

__all__ = ["reset_qubit", "active_reset", "cooldown_reset"]


def reset_qubit(
    qubit: QuamComponent,
    reset_method: Literal[
        "active", "cooldown", None
    ] = "active",  # | Callable[Concatenate[QuamComponent, ...], None]
    readout_pulse: str = "flattop",
    max_tries: int = 10,
    threshold_g: float | None = None,
    relaxation_time: float | None = None,
    save: bool = True,
    **kwargs,
):
    """Reset a qubit. This function is called to reset the qubit after a measurement.


    Args:
        qubit (Qubit): The qubit to reset.
        reset_method (Literal["active", "cooldown", None] | Callable[Concatenate[Qubit, ...], None], optional): The method to use to reset the qubit. Defaults to "active".
        readout_pulse (str, optional): Pulse shape to use for the readout pulse. Defaults to "flattop".
        max_tries (int, optional): The maximum number of tries to reset the qubit. Defaults to 10.
        threshold_g (float | None, optional): The threshold to use for the readout pulse. Defaults to None.
        relaxation_time (float | None, optional): The time to wait for the resonator to relax. Defaults to None.
        save (bool, optional): Whether to save the number of pulses applied. Defaults to True.

    """

    kwargs |= dict(
        readout_pulse=readout_pulse,
        max_tries=max_tries,
        threshold_g=threshold_g,
        relaxation_time=relaxation_time,
        save=save,
    )

    if isinstance(reset_method, Callable):
        return reset_method(qubit, **kwargs)

    elif reset_method == "active":
        return active_reset(qubit, **kwargs)

    elif reset_method == "cooldown":
        return cooldown_reset(qubit, cooldown_time=relaxation_time)


def active_reset(
    qubit: QuamComponent,
    readout_pulse: str = "flattop",
    max_tries: int = 10,
    threshold_g: float | None = None,
    relaxation_time: float | None = None,
    save: bool = True,
) -> QuaVariableType:
    """Reset a qubit by playing a pi pulse and then measuring it.

    Args:
        qubit (Qubit): The qubit to reset.
        readout_pulse (str, optional): Pulse shape to use for the readout pulse. Defaults to "flattop".
        max_tries (int, optional): The maximum number of tries to reset the qubit. Defaults to 10.
        threshold_g (float | None, optional): The threshold to use for the readout pulse. Defaults to None.
        relaxation_time (float | None, optional): The time to wait for the resonator to relax. Defaults to None.
        save (bool, optional): Whether to save the number of pulses applied. Defaults to True.

    Returns:
        QuaVariableType: The number of tries it took to reset the qubit.
    """
    if threshold_g is None:
        threshold_g = qubit.resonator.threshold_g

    if relaxation_time is None:
        relaxation_time = qubit.resonator.relaxation_time

    I_reset = declare(fixed)
    counter = declare(int)
    assign(counter, 0)

    align(qubit.name, qubit.resonator.name)
    with while_((I_reset > threshold_g) & (counter < max_tries)):
        # Measure the state of the resonator
        I_reset, _ = qubit.measure(readout_pulse, I_var=I_reset)
        align(qubit.name, qubit.resonator.name)

        # Wait for the resonator to deplete
        wait(relaxation_time, qubit.name)

        # Play a conditional pi-pulse to actively reset the qubit
        qubit.xy.play("x180", condition=(I_reset > threshold_g))

        # Update the counter for benchmarking purposes
        assign(counter, counter + 1)

    return counter


def cooldown_reset(qubit: QuamComponent, cooldown_time: float | None = None) -> None:
    """Reset a qubit by waiting for it to cooldown.

    Args:
        qubit (Qubit): The qubit to reset.
        cooldown_time (float | None, optional): The time to wait for the qubit to cool down. If None, the qubit's T1 time will be used. Defaults to None.
    """
    if cooldown_time is None:
        cooldown_time = qubit.resonator.t1 * 5

    align(qubit.name, qubit.resonator.name)
    wait(cooldown_time, qubit.name)
