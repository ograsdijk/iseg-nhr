from typing import Callable, TypeVar

import pyvisa

from .ramp import Ramp

_T = TypeVar("_T")


class Current:
    """
    Channel current
    """

    def __init__(self, device: pyvisa.resources.SerialInstrument, channel: int):
        self._device = device
        self._channel = channel
        self._ramp = Ramp(self._device, channel, "CURR")

    def _query(self, cmd: str) -> str:
        ret = self._device.query(f"{cmd} (@{self._channel})")
        if ret != f"{cmd} (@{self._channel})":
            raise ValueError(
                f"channel {self._channel} current error in command {cmd}, NHR returned"
                f" {ret}"
            )
        return self._device.read()

    def _query_type_conv_unit(
        self,
        cmd: str,
        value_type: Callable[[str], _T],
        unit: str = "A",
    ) -> _T:
        return value_type(self._query(cmd).strip(unit))

    def _write(self, cmd: str):
        cmd = f"{cmd},(@{self._channel})"
        ret = self._device.query(cmd)
        if ret != cmd:
            raise ValueError(
                f"channel {self._channel} current error in command {cmd}, NHR returned"
                f" {ret}"
            )

    @property
    def ramp(self) -> Ramp:
        return self._ramp

    @property
    def measured(self) -> float:
        """
        Measured output current [A]

        Returns:
            float: current [A]
        """
        return self._query_type_conv_unit(":MEAS:CURR?", value_type=float)

    @property
    def limit(self) -> float:
        """
        Curren limit [A]

        Returns:
            float: current [A]
        """
        return self._query_type_conv_unit(":READ:CURR:LIM?", value_type=float)

    @property
    def maximum(self) -> float:
        """
        Maximum current [A]

        Returns:
            float: current [A]
        """
        return self._query_type_conv_unit(":READ:CURR:NOM?", value_type=float)

    @property
    def mode(self) -> float:
        """
        Configured current mode

        Returns:
            str: current mode [A]
        """
        return self._query_type_conv_unit(":READ:CURR:MODE?", value_type=float)

    @property
    def mode_list(self) -> str:
        """
        Available current modes [A]

        Returns:
            str: available current modes [A]
        """
        return self._query(":READ:CURR:MODE:LIST?")

    @property
    def bounds(self) -> float:
        """
        Current bounds [A]

        Returns:
            float: current bounds [A]
        """
        return self._query_type_conv_unit(":READ:CURR:BOU?", value_type=float)

    @bounds.setter
    def bounds(self, bounds: float):
        """
        Current bounds [A}]

        Args:
            bounds (float): current bounds
        """
        self._write(f":CURR:BOU {bounds}")
