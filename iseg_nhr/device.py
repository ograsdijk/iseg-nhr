from typing import Tuple, cast

import pyvisa
from pyvisa import constants

from .channel import Channel
from .register import ControlRegister, EventRegister, StatusRegister, get_set_bits
from .supply import Supply


class NHR:
    def __init__(
        self,
        resource_name: str,
        baud_rate: int = 9600,
        data_bits: int = 8,
        stop_bits: constants.StopBits = constants.StopBits.one,
        parity: constants.Parity = constants.Parity.none,
    ):
        self.rm = pyvisa.ResourceManager()
        self.dev = cast(
            pyvisa.resources.SerialInstrument,
            self.rm.open_resource(resource_name=resource_name),
        )
        self.channel1 = Channel(self.dev, 1)
        self.channel2 = Channel(self.dev, 2)
        self.channel3 = Channel(self.dev, 3)
        self.channel4 = Channel(self.dev, 4)
        self.supply = Supply(self.dev)

    def _query(self, cmd: str) -> str:
        return self.dev.query(cmd)

    def _write(self, cmd: str):
        ret = self.dev.query(cmd)
        if ret != cmd:
            raise ValueError(f"error in command {cmd}, NHR returned {ret}")

    @property
    def identity(self) -> str:
        return self._query("*IDN?")

    def clear_status(self):
        self._query("*CLS")

    def reset(self):
        self._query("*RST")

    @property
    def instruction_set(self) -> str:
        return self._query("*INSTR?")

    def lockout(self):
        self._query("*LLO")

    def local(self):
        self._query("*GTL")

    @property
    def operation_complete(self) -> bool:
        return bool(int(self._query("*OPC?")))

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
        self._write(":CONF:EV CLEAR")

    @property
    def temperature(self) -> float:
        return float(self._query(":READ:TEMP?"))

    @property
    def number_channels(self) -> int:
        return int(self._query(":READ:CHAN?"))

    @property
    def firmware_name(self) -> str:
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