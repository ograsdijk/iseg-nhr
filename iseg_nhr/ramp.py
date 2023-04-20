from typing import Callable, Optional, TypeVar

import pyvisa

_T = TypeVar("_T")


class Ramp:
    def __init__(
        self,
        device: pyvisa.resources.SerialInstrument,
        channel: int,
        property_type: str,
    ):
        self._device = device
        self._channel = channel
        self.property_type = property_type

        if property_type == "VOL":
            self.unit = "V"
        elif property_type == "CURR":
            self.unit = "A"
        else:
            raise ValueError(
                f"valid property_type options are VOL and CURR, not {property_type}"
            )

    def _query(self, cmd: str) -> str:
        return self._device.query(f"{cmd} (@{self._channel})")

    def _query_type_conv_unit(
        self,
        cmd: str,
        value_type: Callable[[str], _T],
        unit: Optional[str] = None,
    ) -> _T:
        if unit is None:
            _unit = f"{self.unit}/s"
        else:
            _unit = unit

        return value_type(self._query(cmd).strip(_unit))

    def _write(self, cmd: str):
        ret = self._device.query(f"{cmd},(@{self._channel})")
        if ret != cmd:
            raise ValueError(
                f"channel {self._channel} {self.property_type} ramp error in command"
                f" {cmd}, NHR returned {ret}"
            )

    @property
    def speed(self) -> float:
        """
        Ramp speed in unit/s.

        Returns:
            float: ramp speed [unit/s]
        """
        return self._query_type_conv_unit(
            f":RAMP:{self.property_type}?", value_type=float
        )

    @speed.setter
    def speed(self, value: float):
        """
        Ramp speed in unit/s.

        Args:
            value (float): ramp speed [units/s]
        """
        self._write(f":RAMP:{self.property_type} {value}")

    @property
    def speed_up(self) -> float:
        """
        Upwards ramp speed in unit/s.

        Returns:
            float: upward ramp speed [unit/s]
        """
        return self._query_type_conv_unit(
            f":RAMP:{self.property_type}:UP?", value_type=float
        )

    @speed_up.setter
    def speed_up(self, value: float):
        """
        Upwards ramp speed in unit/s.

        Returns:
            float: upward ramp speed [unit/s]
        """
        self._write(f":RAMP:{self.property_type}:UP {value}")

    @property
    def speed_down(self) -> float:
        """
        Downwards ramp speed in unit/s.

        Returns:
            float: downward ramp speed [unit/s]
        """
        return self._query_type_conv_unit(
            f":RAMP:{self.property_type}:DOWN?", value_type=float
        )

    @speed_down.setter
    def speed_down(self, value: float):
        """
        Downwards ramp speed in unit/s.

        Returns:
            float: downward ramp speed [unit/s]
        """
        self._write(f":RAMP:{self.property_type} {value}:DOWN")

    @property
    def min(self) -> float:
        """
        Minimum ramp speed in unit/s.

        Returns:
            float: minimum ramp speed [unit/s]
        """
        return self._query_type_conv_unit(
            f":RAMP:{self.property_type}:MIN?", value_type=float
        )

    @property
    def max(self) -> float:
        """
        Maximum ramp speed in unit/s

        Returns:
            float: maximum ramp speed [units/s]
        """
        return self._query_type_conv_unit(
            f":RAMP:{self.property_type}:MAX?", value_type=float
        )
