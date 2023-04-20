from typing import Callable, TypeVar

import pyvisa

from .ramp import Ramp

_T = TypeVar("_T")


class Voltage:
    """
    Channel voltage
    """

    def __init__(self, device: pyvisa.resources.SerialInstrument, channel: int):
        self.device = device
        self.channel = channel
        self.ramp = Ramp(self.device, channel, "VOL")

    def _query(self, cmd: str) -> str:
        return self.device.query(f"{cmd} (@{self.channel})")

    def _query_type_conv_unit(
        self,
        cmd: str,
        value_type: Callable[[str], _T],
        unit: str = "V",
    ) -> _T:
        return value_type(self._query(cmd).strip(unit))

    def _write(self, cmd: str):
        ret = self.device.query(f"{cmd},(@{self.channel})")
        if ret != cmd:
            raise ValueError(
                f"channel {self.channel} voltage error in command {cmd}, NHR returned"
                f" {ret}"
            )

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
        self._write(f":VOLT{setpoint}")

    @property
    def limit(self) -> float:
        """
        Output voltage limit

        Returns:
            float: voltage [V]
        """
        return self._query_type_conv_unit(":READ:VOLT:LIM?", value_type=float)

    @property
    def nominal(self) -> float:
        """
        Output voltage limit

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
        return self._query_type_conv_unit(":READ:VOLT:NOM?", value_type=float)

    @bounds.setter
    def bounds(self, value: float):
        """
        Output voltage bounds [V]

        Args:
            value (float): voltage [V]
        """
        self._write(f":VOLT:BOU {value}")
