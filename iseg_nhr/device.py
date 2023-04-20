from __future__ import annotations

from typing import Tuple, cast, Sequence

import pyvisa
from pyvisa import constants

from .channel import Channel
from .register import ControlRegister, EventRegister, StatusRegister, get_set_bits
from .supply import Supply

def _create_channel(module: NHR, channel_id: int):
    def channel_property(self: NHR) -> Channel:
        return getattr(self, f"_channel{channel_id}")
    return channel_property

class NHR:
    def __init__(
        self,
        resource_name: str,
        baud_rate: int = 9600,
        data_bits: int = 8,
        stop_bits: constants.StopBits = constants.StopBits.one,
        parity: constants.Parity = constants.Parity.none,
    ):
        rm = pyvisa.ResourceManager()
        self._device = cast(
            pyvisa.resources.SerialInstrument,
            rm.open_resource(
                resource_name=resource_name,
                baud_rate=baud_rate,
                data_bits=data_bits,
                stop_bits=stop_bits,
                parity=parity,
                write_termination="\r\n",
                read_termination="\r\n"
            ),
        )

        
        self._channels = self.number_channels
        for ch in range(self._channels):
            setattr(self, f"_channel{ch}", Channel(self._device, ch))
            setattr(NHR, f"channel{ch}", property(_create_channel(self, ch)))

        self._supply = Supply(self._device)

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

    def on(self, channels: Sequence[int]):
        for ch in channels:
            if ch >= self._channels:
                raise ValueError("channel index exceeds module channel number")
            channel = cast(Channel, getattr(self, f"channel{ch}"))
            channel.on()

    def off(self, channels: Sequence[int]):
        for ch in channels:
            if ch >= self._channels:
                raise ValueError("channel index exceeds module channel number")
            channel = cast(Channel, getattr(self, f"channel{ch}"))
            channel.off()

    @property
    def voltages(self) -> Tuple[float]:
        voltages = []
        for ch in range(self._channels):
            channel = cast(Channel, getattr(self, f"channel{ch}"))
            voltages.append(channel.voltage.measured)
        return tuple(voltages)

    @property
    def currents(self) -> Tuple[float]:
        currents = []
        for ch in range(self._channels):
            channel = cast(Channel, getattr(self, f"channel{ch}"))
            currents.append(channel.current.measured)
        return tuple(currents)

    @property
    def setpoints(self) -> Tuple[float]:
        voltages = []
        for ch in range(self._channels):
            channel = cast(Channel, getattr(self, f"channel{ch}"))
            voltages.append(channel.voltage.setpoint)
        return tuple(voltages)
