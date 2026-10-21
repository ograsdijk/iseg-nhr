from typing import Callable, TypeVar

from .ramp import Ramp
from .transport import (
    DeviceTransport,
    remove_suffix,
    synchronized,
    synchronized_transport,
)

_T = TypeVar("_T")


class Voltage:
    """
    Channel voltage
    """

    def __init__(self, device: DeviceTransport, channel: int):
        self._device = synchronized_transport(device)
        self._channel = channel
        self._ramp = Ramp(self._device, channel, "VOLT")

    @synchronized
    def _query(self, cmd: str) -> str:
        ret = self._device.query(f"{cmd} (@{self._channel})")
        if ret != f"{cmd} (@{self._channel})":
            raise ValueError(
                f"channel {self._channel} voltage error in command {cmd}, NHR returned"
                f" {ret}"
            )
        return self._device.read()

    def _query_type_conv_unit(
        self,
        cmd: str,
        value_type: Callable[[str], _T],
        unit: str = "V",
    ) -> _T:
        return value_type(remove_suffix(self._query(cmd), unit))

    @synchronized
    def _write(self, cmd: str):
        self._device.write_command(f"{cmd},(@{self._channel})")

    @property
    def ramp(self) -> Ramp:
        return self._ramp

    @property
    def measured(self) -> float:
        """
        Measured output voltage

        Returns:
            float: voltage [V]
        """
        return self._query_type_conv_unit(":MEAS:VOLT?", value_type=float)

    @property
    def setpoint(self) -> float:
        """
        Output voltage setpoint

        Returns:
            float: voltage [V]
        """
        return self._query_type_conv_unit(":READ:VOLT?", value_type=float)

    @setpoint.setter
    def setpoint(self, setpoint: float):
        """
        Output voltage setpoint

        Args:
            setpoint (float): voltage [V]
        """
        self._write(f":VOLT {setpoint}")

    @property
    def limit(self) -> float:
        """
        Output voltage limit

        Returns:
            float: voltage [V]
        """
        return self._query_type_conv_unit(":READ:VOLT:LIM?", value_type=float)

    @property
    def maximum(self) -> float:
        """
        Maximum output voltage

        Returns:
            float: voltage [V]
        """
        return self._query_type_conv_unit(":READ:VOLT:NOM?", value_type=float)

    @property
    def mode(self) -> float:
        """
        Configured channel voltage mode with polarity sign [V]

        Returns:
            str: configured channel voltage mode with polarity sign [V]
        """
        return self._query_type_conv_unit(":READ:VOLT:MODE?", value_type=float)

    @property
    def mode_list(self) -> str:
        """
        Available channel voltage modes

        Returns:
            str: _description_
        """
        return self._query(":READ:VOLT:MODE:LIST?")

    @property
    def bounds(self) -> float:
        """
        Output voltage bounds [V]

        Returns:
            float: voltage [V]
        """
        return self._query_type_conv_unit(":READ:VOLT:BOU?", value_type=float)

    @bounds.setter
    def bounds(self, value: float):
        """
        Output voltage bounds [V]

        Args:
            value (float): voltage [V]
        """
        self._write(f":VOLT:BOU {value}")
