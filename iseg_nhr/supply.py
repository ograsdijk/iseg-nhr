import pyvisa


class Supply:
    """
    Module supply voltages
    """
    def __init__(self, device: pyvisa.resources.SerialInstrument):
        self.device = device

    def _query(self, cmd: str) -> str:
        return self.device.query(f"{cmd}?")

    def _write(self, cmd: str):
        self.device.query(f"{cmd})")

    @property
    def p24v(self) -> float:
        """
        +24V module supply voltage

        Returns:
            float: voltage [V]
        """
        return float(self._query(":READ:SUP:P24V"))

    @property
    def n24v(self) -> float:
        """
        -24V module supply voltage

        Returns:
            float: voltage [V]
        """
        return float(self._query(":READ:SUP:N24V"))

    @property
    def p5v(self) -> float:
        """
        +5V module supply voltage

        Returns:
            float: voltage [V]
        """
        return float(self._query(":READ:SUP:P5V"))

    @property
    def p3v(self) -> float:
        """
        +3V module supply voltage

        Returns:
            float: voltage [V]
        """
        return float(self._query(":READ:SUP:P3V"))

    @property
    def p12v(self) -> float:
        """
        +12V module supply voltage

        Returns:
            float: voltage [V]
        """
        return float(self._query(":READ:SUP:P12V"))

    @property
    def n12v(self) -> float:
        """
        -12V module supply voltage

        Returns:
            float: voltage [V]
        """
        return float(self._query(":READ:SUP:N12V"))
