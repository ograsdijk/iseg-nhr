from concurrent.futures import ThreadPoolExecutor
from threading import Event

import pytest

from iseg_nhr import NHR, Polarity
from iseg_nhr.register import ChannelEventRegister, ChannelStatusRegister

from .test_transport import FakeSerial, make_transport


@pytest.mark.parametrize("partial", [b"12", b"12\r", b"12\n"])
def test_partial_measurement_is_rejected(partial):
    serial = FakeSerial([":READ:MOD:CHAN?", "1", ":MEAS:VOLT? (@0)"])
    nhr = NHR(transport=make_transport(serial))
    serial.responses.append(partial)
    with pytest.raises(TimeoutError, match="incomplete"):
        _ = nhr.channel0.voltage.measured


@pytest.mark.parametrize(
    "responses", [["wrong"], [":READ:MOD:CHAN?"], [":READ:MOD:CHAN?", "bad"]]
)
def test_owned_transport_closes_on_initialization_failure(monkeypatch, responses):
    serial = FakeSerial(responses)
    monkeypatch.setattr(
        "iseg_nhr.module.SerialTransport", lambda **_: make_transport(serial)
    )
    with pytest.raises((ValueError, TimeoutError)):
        NHR("COM_TEST")
    assert serial.closed


def test_failed_initialization_does_not_close_caller_owned_transport():
    serial = FakeSerial(["wrong"])
    with pytest.raises(ValueError):
        NHR(transport=make_transport(serial))
    assert not serial.closed


def test_cleanup_preserves_initialization_error(monkeypatch):
    class BrokenClose(FakeSerial):
        def close(self):
            raise OSError("close failed")

    serial = BrokenClose(["wrong"])
    monkeypatch.setattr(
        "iseg_nhr.module.SerialTransport", lambda **_: make_transport(serial)
    )
    with pytest.raises(ValueError, match="error in command"):
        NHR("COM_TEST")


@pytest.mark.parametrize(
    "operation",
    [
        lambda n: n.identity,
        lambda n: n.channel0.on_state,
        lambda n: n.channel0.voltage.measured,
        lambda n: n.channel0.current.measured,
        lambda n: n.channel0.voltage.ramp.speed,
        lambda n: n.supply.p24v,
        lambda n: n.channel0.on(),
    ],
)
def test_helpers_cannot_interleave_with_pending_module_reply(operation):
    class BlockingTransport:
        def __init__(self):
            self.command = None
            self.read_started = Event()
            self.release_read = Event()
            self.second_started = Event()
            self.second_wrote = Event()

        def query(self, cmd):
            if self.read_started.is_set():
                self.second_wrote.set()
            self.command = cmd
            return cmd

        def read(self):
            if self.command == ":READ:MOD:CHAN?":
                return "1"
            if self.command == "*IDN?" and not self.read_started.is_set():
                self.read_started.set()
                if not self.release_read.wait(3):
                    raise TimeoutError("test did not release reply")
                return "ISEG,NHR"
            return "1"

        def close(self):
            pass

    transport = BlockingTransport()
    nhr = NHR(transport=transport)

    def second():
        transport.second_started.set()
        return operation(nhr)

    with ThreadPoolExecutor(max_workers=2) as pool:
        first = pool.submit(lambda: nhr.identity)
        try:
            assert transport.read_started.wait(1)
            other = pool.submit(second)
            assert transport.second_started.wait(1)
            assert not transport.second_wrote.wait(0.05)
        finally:
            transport.release_read.set()
        assert first.result(timeout=1) == "ISEG,NHR"
        other.result(timeout=1)
    assert transport.second_wrote.is_set()


def polarity_device(on, voltage=None, maximum=None):
    replies = [":READ:MOD:CHAN?", "1", ":READ:VOLT:ON? (@0)", str(on)]
    if voltage is not None:
        replies += [
            ":MEAS:VOLT? (@0)",
            f"{voltage}V",
            ":READ:VOLT:NOM? (@0)",
            f"{maximum}V",
        ]
    serial = FakeSerial(replies)
    return NHR(transport=make_transport(serial)), serial


def test_polarity_change_rejects_enabled_channel_even_at_zero_voltage():
    nhr, serial = polarity_device(1)
    with pytest.raises(ValueError, match="must be off"):
        nhr.channel0.polarity = Polarity.NEGATIVE
    assert not any(b":CONF:OUTP:POL " in cmd for cmd in serial.writes)


@pytest.mark.parametrize(
    "voltage,maximum", [(4, 2000), (-4, 2000), (10, 2000), (float("nan"), 2000), (0, 0)]
)
def test_polarity_change_rejects_undischarged_or_invalid_readback(voltage, maximum):
    nhr, serial = polarity_device(0, voltage, maximum)
    with pytest.raises(ValueError, match="must discharge"):
        nhr.channel0.polarity = Polarity.NEGATIVE
    assert not any(b":CONF:OUTP:POL " in cmd for cmd in serial.writes)


@pytest.mark.parametrize("voltage", [0, 0.5, -0.5])
def test_polarity_change_allows_off_channel_below_manual_threshold(voltage):
    nhr, serial = polarity_device(0, voltage, 2000)
    serial.responses.extend([b":CONF:OUTP:POL n,(@0);*OPC?\r\n", b"1\r\n"])
    nhr.channel0.polarity = Polarity.NEGATIVE
    assert serial.writes[-1] == b":CONF:OUTP:POL n,(@0);*OPC?\r\n"


@pytest.mark.parametrize(
    "register,command,expected",
    [
        (
            "status_register",
            ":READ:CHAN:STAT?",
            (
                ChannelStatusRegister.IsFlashover,
                ChannelStatusRegister.IsFlashoverNumberExceeded,
            ),
        ),
        (
            "event_register",
            ":READ:CHAN:EV:STAT?",
            (
                ChannelEventRegister.Flashover,
                ChannelEventRegister.FlashoverNumberExceeded,
            ),
        ),
    ],
)
def test_documented_flashover_bits_decode(register, command, expected):
    serial = FakeSerial(
        [":READ:MOD:CHAN?", "1", f"{command} (@0)", str((1 << 26) | (1 << 27))]
    )
    nhr = NHR(transport=make_transport(serial))
    assert getattr(nhr.channel0, register) == expected


@pytest.mark.parametrize(
    "method,command",
    [
        ("emergency_off", ":VOLT EMCY OFF,(@0)"),
        ("emergency_clear", ":VOLT EMCY CLR,(@0)"),
        ("event_clear", ":EV CLEAR,(@0)"),
    ],
)
def test_channel_commands_follow_manual_and_wait_for_completion(method, command):
    serial = FakeSerial([":READ:MOD:CHAN?", "1", f"{command};*OPC?", "1"])
    nhr = NHR(transport=make_transport(serial))
    getattr(nhr.channel0, method)()
    assert serial.writes[-1] == f"{command};*OPC?\r\n".encode("ascii")
    assert not serial.responses


@pytest.mark.parametrize(
    "responses,error",
    [
        (["wrong"], ValueError),
        ([":VOLT ON,(@0);*OPC?"], TimeoutError),
        ([":VOLT ON,(@0);*OPC?", "0"], ValueError),
    ],
)
def test_writes_require_matching_echo_and_successful_completion(responses, error):
    serial = FakeSerial([":READ:MOD:CHAN?", "1", *responses])
    nhr = NHR(transport=make_transport(serial))
    with pytest.raises(error):
        nhr.channel0.on()


def test_current_measurement_is_in_amperes():
    serial = FakeSerial([":READ:MOD:CHAN?", "1", ":MEAS:CURR? (@0)", "1.23456E-6A"])
    nhr = NHR(transport=make_transport(serial))
    assert nhr.channel0.current.measured == pytest.approx(1.23456e-6)
