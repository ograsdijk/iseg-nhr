from enum import Enum, auto
from typing import Dict, Tuple

import pyvisa

from .current import Current
from .register import (
    ChannelControlRegister,
    ChannelEventRegister,
    ChannelStatusRegister,
    get_set_bits,
)
from .voltage import Voltage


class Polarity(Enum):
    NEGATIVE = auto()
    POSITIVE = auto()


class Channel:
    def __init__(self, device: pyvisa.resources.SerialInstrument, channel: int):
        self.device = device
        self.channel = channel
        self.voltage = Voltage(self.device, self.channel)
        self.current = Current(self.device, self.channel)

    def _query(self, cmd: str) -> str:
        return self.device.query(f"{cmd} (@{self.channel})")

    def _write(self, cmd: str):
        ret = self.device.query(f"{cmd},(@{self.channel})")
        if ret != cmd:
            raise ValueError(
                f"channel {self.channel} error in command {cmd}, NHR returned {ret}"
            )

    @property
    def on_state(self) -> bool:
        return bool(int(self._query(":READ:VOLT:ON?")))

    def on(self):
        self._write(":VOLT ON")

    def off(self):
        self._write(":VOLT OFF")

    def emergency_off(self):
        self._write(":VOLT EMCY_OFF")

    @property
    def emergency(self) -> bool:
        return bool(int(self._query(":READ:VOLT:EMCY?")))

    def emergency_clear(self):
        self._write(":VOLT EMCY_CLR")

    def event_clear(self):
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
                f"channel {self.channel} expected polarity return to be 'n' or 'p', not"
                f" {polarity}"
            )

    @polarity.setter
    def polarity(self, polarity: Polarity):
        voltage = self.voltage.measured
        if voltage != 0:
            raise ValueError(
                f"channel {self.channel} can't reverse polarity with non-zero voltage"
                f" {voltage} V"
            )
        self._write(f":CONF:OUTP:POL {polarity.name[0].lower()}")

    @property
    def polarity_list(self) -> str:
        return self._query(":CONF:OUTP:POL:LIST?")

    @property
    def output_mode(self) -> int:
        return int(self._query(":CONF:OUTP:MODE?"))

    def output_mode_list(self) -> str:
        return self._query(":CONF:OUTP:MODE:LIST?")

    @property
    def inhibit(self) -> str:
        inhibit = int(self._query("CONF:INH:ACT?"))
        return self.inhibit_options[inhibit]

    @inhibit.setter
    def inhibit(self, value: int):
        if value not in self.inhibit_options.keys():
            raise ValueError(
                f"inhibit option {value} not available, choose from"
                f" {self.inhibit_options}"
            )
        self._write(f"CONF:INH:ACT {value}")

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
