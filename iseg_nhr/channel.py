from enum import IntEnum
from math import isfinite
from typing import Dict, Tuple

from .current import Current
from .register import (
    ChannelControlRegister,
    ChannelEventRegister,
    ChannelStatusRegister,
    get_set_bits,
)
from .transport import DeviceTransport, synchronized, synchronized_transport
from .voltage import Voltage


class Polarity(IntEnum):
    NEGATIVE = -1
    POSITIVE = +1


class Channel:
    def __init__(self, device: DeviceTransport, channel: int):
        self._device = synchronized_transport(device)
        self._channel = channel
        self._voltage = Voltage(self._device, self._channel)
        self._current = Current(self._device, self._channel)

    @synchronized
    def _query(self, cmd: str) -> str:
        ret = self._device.query(f"{cmd} (@{self._channel})")
        if ret != f"{cmd} (@{self._channel})":
            raise ValueError(
                f"channel {self._channel} error in command {cmd}, NHR returned {ret}"
            )
        return self._device.read()

    @synchronized
    def _write(self, cmd: str):
        self._device.write_command(f"{cmd},(@{self._channel})")

    @property
    def voltage(self) -> Voltage:
        return self._voltage

    @property
    def current(self) -> Current:
        return self._current

    @property
    def on_state(self) -> bool:
        return bool(int(self._query(":READ:VOLT:ON?")))

    def on(self):
        self._write(":VOLT ON")

    def off(self):
        self._write(":VOLT OFF")

    def emergency_off(self):
        self._write(":VOLT EMCY OFF")

    @property
    def emergency(self) -> bool:
        """
        Channel emergency

        Returns:
            bool: channel emergency
        """
        return bool(int(self._query(":READ:VOLT:EMCY?")))

    def emergency_clear(self):
        """
        Clear channel emergency
        """
        self._write(":VOLT EMCY CLR")

    def event_clear(self):
        """
        Clear channel events
        """
        self._write(":EV CLEAR")

    @property
    def control_register(self) -> Tuple[ChannelControlRegister, ...]:
        control = int(self._query(":READ:CHAN:CONT?"))
        set_bits = get_set_bits(control, 32)
        return tuple([ChannelControlRegister(bit) for bit in set_bits])

    @property
    def status_register(self) -> Tuple[ChannelStatusRegister, ...]:
        status = int(self._query(":READ:CHAN:STAT?"))
        set_bits = get_set_bits(status, 32)
        return tuple([ChannelStatusRegister(bit) for bit in set_bits])

    @property
    def event_register(self) -> Tuple[ChannelEventRegister, ...]:
        event = int(self._query(":READ:CHAN:EV:STAT?"))
        set_bits = get_set_bits(event, 32)
        return tuple([ChannelEventRegister(bit) for bit in set_bits])

    @property
    def polarity(self) -> Polarity:
        polarity = self._query(":CONF:OUTP:POL?")
        if polarity == "n":
            return Polarity.NEGATIVE
        elif polarity == "p":
            return Polarity.POSITIVE
        else:
            raise ValueError(
                f"channel {self._channel} expected polarity return to be 'n' or 'p',"
                f" not {polarity}"
            )

    @polarity.setter
    @synchronized
    def polarity(self, polarity: Polarity):
        if not isinstance(polarity, Polarity):
            raise ValueError("polarity must be a Polarity member")
        if self.on_state:
            raise ValueError(f"channel {self._channel} must be off to reverse polarity")
        voltage = self.voltage.measured
        maximum = abs(self.voltage.maximum)
        if (
            not isfinite(voltage)
            or not isfinite(maximum)
            or maximum <= 0
            or abs(voltage) >= 0.002 * maximum
        ):
            raise ValueError(
                f"channel {self._channel} must discharge below 0.002 * nominal voltage"
                f" before reversing polarity ({voltage} V measured)"
            )
        self._write(f":CONF:OUTP:POL {polarity.name[0].lower()}")

    @property
    def polarity_list(self) -> str:
        return self._query(":CONF:OUTP:POL:LIST?")

    @property
    def output_mode(self) -> int:
        return int(self._query(":CONF:OUTP:MODE?"))

    @property
    def output_mode_list(self) -> str:
        return self._query(":CONF:OUTP:MODE:LIST?")

    @property
    def inhibit(self) -> str:
        inhibit = int(self._query(":CONF:INH:ACT?"))
        return self.inhibit_options[inhibit]

    @inhibit.setter
    def inhibit(self, value: int):
        if value not in self.inhibit_options.keys():
            raise ValueError(
                f"inhibit option {value} not available, choose from"
                f" {self.inhibit_options}"
            )
        self._write(f":CONF:INH:ACT {value}")

    @property
    def inhibit_options(self) -> Dict[int, str]:
        inhibit_options = {
            0: "no action, status flag External Inhibit will be set",
            1: "turn off the channel with ramp",
            2: "shut down the channel without ramp",
            3: "shut down the whoel module without ramp",
            4: "disable the External Inhibit function",
        }
        return inhibit_options
