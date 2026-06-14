from __future__ import annotations

from typing import Optional, Sequence, Tuple

import serial

from .channel import Channel
from .register import ControlRegister, EventRegister, StatusRegister, get_set_bits
from .supply import Supply
from .transport import DeviceTransport, SerialTransport


class NHR:
    def __init__(
        self,
        port: Optional[str] = None,
        baud_rate: int = 9600,
        data_bits: int = serial.EIGHTBITS,
        stop_bits: float = serial.STOPBITS_ONE,
        parity: str = serial.PARITY_NONE,
        timeout: float = 1.0,
        write_timeout: float = 1.0,
        transport: DeviceTransport | None = None,
        resource_name: Optional[str] = None,
    ):
        if port is None:
            port = resource_name
        if transport is None and port is None:
            raise TypeError("missing required argument: 'port'")

        self._device = (
            transport
            if transport is not None
            else SerialTransport(
                port=port,
                baud_rate=baud_rate,
                data_bits=data_bits,
                stop_bits=stop_bits,
                parity=parity,
                timeout=timeout,
                write_timeout=write_timeout,
            )
        )

        self._channels = self.number_channels
        self._channel_instances = tuple(
            Channel(self._device, ch) for ch in range(self._channels)
        )

        self._supply = Supply(self._device)

    def close(self):
        self._device.close()

    def __enter__(self) -> NHR:
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

    def __getattr__(self, name: str):
        if name.startswith("channel"):
            channel_id = name.removeprefix("channel")
            if channel_id.isdecimal():
                index = int(channel_id)
                if index < self._channels:
                    return self._channel_instances[index]
        raise AttributeError(
            f"{type(self).__name__!r} object has no attribute {name!r}"
        )

    def _query(self, cmd: str) -> str:
        ret = self._device.query(cmd)
        if ret != cmd:
            raise ValueError(f"error in command {cmd}, NHR returned {ret}")
        return self._device.read()

    def _write(self, cmd: str):
        ret = self._device.query(cmd)
        if ret != cmd:
            raise ValueError(f"error in command {cmd}, NHR returned {ret}")

    @property
    def supply(self) -> Supply:
        return self._supply

    @property
    def identity(self) -> str:
        return self._query("*IDN?")

    def status_clear(self):
        self._write("*CLS")

    def reset(self):
        self._write("*RST")

    @property
    def operation_complete(self) -> bool:
        return bool(int(self._query("*OPC?")))

    @property
    def instruction_set(self) -> str:
        return self._query("*INSTR?")

    def lockout(self):
        """
        Disable local control of the module
        """
        self._write("*LLO")

    def local(self):
        """
        Activate local control of the module
        """
        self._write("*GTL")

    @property
    def control_register(self) -> Tuple[ControlRegister, ...]:
        control = int(self._query(":READ:MOD:CONT?"))
        set_bits = get_set_bits(control, 32)
        return tuple([ControlRegister(bit) for bit in set_bits])

    @property
    def status_register(self) -> Tuple[StatusRegister, ...]:
        status = int(self._query(":READ:MOD:STAT?"))
        set_bits = get_set_bits(status, 32)
        return tuple([StatusRegister(bit) for bit in set_bits])

    @property
    def event_register(self) -> Tuple[EventRegister, ...]:
        event = int(self._query(":READ:MOD:EV:STAT?"))
        set_bits = get_set_bits(event, 32)
        return tuple([EventRegister(bit) for bit in set_bits])

    def event_clear(self):
        """
        Clear the module event register
        """
        self._write(":CONF:EV CLEAR")

    @property
    def temperature(self) -> float:
        """
        Module temperature [C]

        Returns:
            float: temperature [C]
        """
        return float(self._query(":READ:MOD:TEMP?").strip("C"))

    @property
    def number_channels(self) -> int:
        """
        Number of channels of the module

        Returns:
            int: channels
        """
        return int(self._query(":READ:MOD:CHAN?"))

    @property
    def firmware_version(self) -> str:
        return self._query(":READ:FIRM:NAME?")

    @property
    def firmware_release(self) -> str:
        return self._query(":READ:FIRM:REL?")

    @property
    def config(self) -> str:
        config = int(self._query(":SYS:USER:CONF?"))
        if config == 0:
            return "normal mode"
        elif config == 1:
            return "configuration mode"
        else:
            raise ValueError(
                "config return not 0 (normal mode) or 1 (configuration mode)"
            )

    def config_save(self):
        self._write(":SYS:USER:CONF SAVE")

    def channel(self, channel: int) -> Channel:
        if channel < 0 or channel >= self._channels:
            raise ValueError("channel index exceeds module channel number")
        return self._channel_instances[channel]

    def on(self, channels: Sequence[int]):
        for ch in channels:
            channel = self.channel(ch)
            channel.on()

    def off(self, channels: Sequence[int]):
        for ch in channels:
            channel = self.channel(ch)
            channel.off()

    @property
    def voltages(self) -> Tuple[float, ...]:
        voltages = []
        for ch in range(self._channels):
            channel = self._channel_instances[ch]
            voltages.append(channel.voltage.measured)
        return tuple(voltages)

    @property
    def currents(self) -> Tuple[float, ...]:
        currents = []
        for ch in range(self._channels):
            channel = self._channel_instances[ch]
            currents.append(channel.current.measured)
        return tuple(currents)

    @property
    def setpoints(self) -> Tuple[float, ...]:
        voltages = []
        for ch in range(self._channels):
            channel = self._channel_instances[ch]
            voltages.append(channel.voltage.setpoint)
        return tuple(voltages)
