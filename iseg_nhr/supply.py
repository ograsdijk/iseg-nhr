import pyvisa
from typing import Callable, TypeVar

_T = TypeVar("_T")

class Supply:
    """
    Module supply voltages
    """
    def __init__(self, device: pyvisa.resources.SerialInstrument):
        self._device = device

    def _query(self, cmd: str) -> str:
        ret = self._device.query(cmd)
        if ret != cmd:
            raise ValueError(f"error in command {cmd}, NHR returned {ret}")
        return self._device.read()

    def _write(self, cmd: str):
        ret = self._device.query(f"{cmd})")
        if ret != cmd:
            raise ValueError(f"error in command {cmd}, NHR returned {ret}")

    def _query_type_conv_unit(
        self,
        cmd: str,
        value_type: Callable[[str], _T],
        unit: str = "V",
    ) -> _T:
        return value_type(self._query(cmd).strip(unit))

    @property
    def p24v(self) -> float:
        """
        +24V module supply voltage

        Returns:
            float: voltage [V]
        """
        return float(self._query_type_conv_unit(":READ:MOD:SUP:P24V?", value_type = float))

    @property
    def n24v(self) -> float:
        """
        -24V module supply voltage

        Returns:
            float: voltage [V]
        """
        return float(self._query_type_conv_unit(":READ:MOD:SUP:N24V?", value_type = float))

    @property
    def p5v(self) -> float:
        """
        +5V module supply voltage

        Returns:
            float: voltage [V]
        """
        return float(self._query_type_conv_unit(":READ:MOD:SUP:P5V?", value_type = float))

    @property
    def p3v(self) -> float:
        """
        +3V module supply voltage

        Returns:
            float: voltage [V]
        """
        return float(self._query_type_conv_unit(":READ:MOD:SUP:P3V?", value_type = float))

    @property
    def p12v(self) -> float:
        """
        +12V module supply voltage

        Returns:
            float: voltage [V]
        """
        return float(self._query_type_conv_unit(":READ:MOD:SUP:P12V?", value_type = float))

    @property
    def n12v(self) -> float:
        """
        -12V module supply voltage

        Returns:
            float: voltage [V]
        """
        return float(self._query_type_conv_unit(":READ:MOD:SUP:N12V?", value_type = float))
