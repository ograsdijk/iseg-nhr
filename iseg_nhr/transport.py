from typing import Protocol

import serial


class DeviceTransport(Protocol):
    def query(self, cmd: str) -> str: ...

    def read(self) -> str: ...

    def close(self): ...


def remove_suffix(value: str, suffix: str) -> str:
    return value.removesuffix(suffix)


class SerialTransport:
    def __init__(
        self,
        port: str,
        baud_rate: int = 9600,
        data_bits: int = serial.EIGHTBITS,
        stop_bits: float = serial.STOPBITS_ONE,
        parity: str = serial.PARITY_NONE,
        timeout: float = 1.0,
        write_timeout: float = 1.0,
        termination: str = "\r\n",
        encoding: str = "ascii",
        clear_input_before_write: bool = True,
    ):
        self._serial = serial.Serial(
            port=port,
            baudrate=baud_rate,
            bytesize=data_bits,
            stopbits=stop_bits,
            parity=parity,
            timeout=timeout,
            write_timeout=write_timeout,
        )
        self._termination = termination
        self._encoding = encoding
        self._clear_input_before_write = clear_input_before_write

    def query(self, cmd: str) -> str:
        if self._clear_input_before_write:
            self._serial.reset_input_buffer()
        self._serial.write(f"{cmd}{self._termination}".encode(self._encoding))
        return self.read()

    def read(self) -> str:
        line = self._serial.readline()
        if not line:
            raise TimeoutError("timed out waiting for NHR response")
        return self._strip_termination(line.decode(self._encoding))

    def close(self):
        self._serial.close()

    def _strip_termination(self, value: str) -> str:
        if value.endswith(self._termination):
            return value[: -len(self._termination)]
        return value.rstrip("\r\n")
