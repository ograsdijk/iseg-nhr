from functools import wraps
from threading import RLock
from typing import Callable, Protocol, TypeVar

import serial

_T = TypeVar("_T")


class DeviceTransport(Protocol):
    def query(self, cmd: str) -> str: ...

    def read(self) -> str: ...

    def close(self): ...


class SynchronizedTransport:
    """One transaction lock shared by a module and all of its channel helpers."""

    def __init__(self, device: DeviceTransport):
        self._device = device
        self.lock = RLock()

    def query(self, cmd: str) -> str:
        with self.lock:
            return self._device.query(cmd)

    def read(self) -> str:
        with self.lock:
            return self._device.read()

    def write_command(self, cmd: str) -> None:
        """Wait for command processing, not merely the character echo."""
        with self.lock:
            command = f"{cmd};*OPC?"
            echo = self._device.query(command)
            if echo != command:
                raise ValueError(f"error in command {command}, NHR returned {echo}")
            response = self._device.read()
            if response != "1":
                raise ValueError(f"unexpected operation-complete response: {response}")

    def close(self):
        with self.lock:
            self._device.close()


def synchronized_transport(device: DeviceTransport) -> SynchronizedTransport:
    if isinstance(device, SynchronizedTransport):
        return device
    return SynchronizedTransport(device)


def synchronized(method: Callable[..., _T]) -> Callable[..., _T]:
    @wraps(method)
    def wrapper(self, *args, **kwargs) -> _T:
        with self._device.lock:
            return method(self, *args, **kwargs)

    return wrapper


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
        if not termination or not termination.endswith("\n"):
            raise ValueError("termination must be nonempty and end with a newline")
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
        if not line.endswith(self._termination.encode(self._encoding)):
            raise TimeoutError("incomplete NHR response (missing line terminator)")
        return self._strip_termination(line.decode(self._encoding))

    def close(self):
        self._serial.close()

    def _strip_termination(self, value: str) -> str:
        if value.endswith(self._termination):
            return value[: -len(self._termination)]
        return value.rstrip("\r\n")
