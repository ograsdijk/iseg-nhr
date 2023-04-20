from typing import Callable, Optional, TypeVar, cast

import pyvisa

_T = TypeVar("_T")


class Ramp:
    def __init__(
        self,
        device: pyvisa.resources.SerialInstrument,
        channel: int,
        property_type: str,
    ):
        self.device = device
        self.channel = channel
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
        return self.device.query(f"{cmd} (@{self.channel})")

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
        ret = self.device.query(f"{cmd},(@{self.channel})")
        if ret != cmd:
            raise ValueError(
                f"channel {self.channel} {self.property_type} ramp error in command"
                f" {cmd}, NHR returned {ret}"
            )

    @property
    def ramp_speed(self) -> float:
        """
        Ramp speed in unit/s.

        Returns:
            float: ramp speed [unit/s]
        """
        return self._query_type_conv_unit(
            f":RAMP:{self.property_type}?", value_type=float
        )

    @ramp_speed.setter
    def ramp_speed(self, value: float):
        """
        Ramp speed in unit/s.

        Args:
            value (float): ramp speed [units/s]
        """
        self._write(f":RAMP:{self.property_type} {value}")

    @property
    def ramp_speed_up(self) -> float:
        """
        Upwards ramp speed in unit/s.

        Returns:
            float: upward ramp speed [unit/s]
        """
        return self._query_type_conv_unit(
            f":RAMP:{self.property_type}:UP?", value_type=float
        )

    @ramp_speed_up.setter
    def ramp_speed_up(self, value: float):
        """
        Upwards ramp speed in unit/s.

        Returns:
            float: upward ramp speed [unit/s]
        """
        self._write(f":RAMP:{self.property_type}:UP {value}")

    @property
    def ramp_speed_down(self) -> float:
        """
        Downwards ramp speed in unit/s.

        Returns:
            float: downward ramp speed [unit/s]
        """
        return self._query_type_conv_unit(
            f":RAMP:{self.property_type}:DOWN?", value_type=float
        )

    @ramp_speed_down.setter
    def ramp_speed_down(self, value: float):
        """
        Downwards ramp speed in unit/s.

        Returns:
            float: downward ramp speed [unit/s]
        """
        self._write(f":RAMP:{self.property_type} {value}:DOWN")

    @property
    def ramp_min(self) -> float:
        """
        Minimum ramp speed in unit/s.

        Returns:
            float: minimum ramp speed [unit/s]
        """
        return self._query_type_conv_unit(
            f":RAMP:{self.property_type}:MIN?", value_type=float
        )

    @property
    def ramp_max(self) -> float:
        """
        Maximum ramp speed in unit/s

        Returns:
            float: maximum ramp speed [units/s]
        """
        return self._query_type_conv_unit(
            f":RAMP:{self.property_type}:MAX?", value_type=float
        )
