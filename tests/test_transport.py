import pytest

from iseg_nhr import NHR
from iseg_nhr.transport import SerialTransport, remove_suffix


class FakeSerial:
    def __init__(self, responses):
        self.responses = [f"{response}\r\n".encode("ascii") for response in responses]
        self.writes = []
        self.closed = False
        self.reset_input_buffer_calls = 0

    def write(self, data):
        self.writes.append(data)

    def readline(self):
        if not self.responses:
            return b""
        return self.responses.pop(0)

    def close(self):
        self.closed = True

    def reset_input_buffer(self):
        self.reset_input_buffer_calls += 1


def make_transport(fake_serial):
    transport = SerialTransport.__new__(SerialTransport)
    transport._serial = fake_serial
    transport._termination = "\r\n"
    transport._encoding = "ascii"
    transport._clear_input_before_write = True
    return transport


def test_serial_transport_query_clears_input_writes_crlf_and_reads_echo():
    fake_serial = FakeSerial(["*IDN?"])
    transport = make_transport(fake_serial)

    assert transport.query("*IDN?") == "*IDN?"
    assert fake_serial.reset_input_buffer_calls == 1
    assert fake_serial.writes == [b"*IDN?\r\n"]


def test_serial_transport_read_raises_timeout_error():
    transport = make_transport(FakeSerial([]))

    with pytest.raises(TimeoutError, match="timed out"):
        transport.read()


def test_nhr_queries_echo_then_response():
    transport = make_transport(
        FakeSerial([":READ:MOD:CHAN?", "2", "*IDN?", "ISEG,NHR"])
    )
    nhr = NHR("COM1", transport=transport)

    assert nhr.identity == "ISEG,NHR"
    assert transport._serial.writes == [b":READ:MOD:CHAN?\r\n", b"*IDN?\r\n"]


def test_nhr_validates_echo():
    transport = make_transport(FakeSerial(["wrong", "2"]))

    with pytest.raises(ValueError, match="error in command"):
        NHR("COM1", transport=transport)


def test_channel_write_formats_channel_suffix():
    transport = make_transport(FakeSerial([":READ:MOD:CHAN?", "1", ":VOLT ON,(@0)"]))
    nhr = NHR("COM1", transport=transport)

    nhr.channel0.on()

    assert transport._serial.writes[-1] == b":VOLT ON,(@0)\r\n"


def test_nhr_accepts_resource_name_keyword():
    transport = make_transport(FakeSerial([":READ:MOD:CHAN?", "1"]))

    nhr = NHR(resource_name="COM1", transport=transport)

    assert nhr.channel0 is not None


def test_nhr_accepts_transport_without_port():
    transport = make_transport(FakeSerial([":READ:MOD:CHAN?", "1"]))

    nhr = NHR(transport=transport)

    assert nhr.channel0 is not None


def test_nhr_uses_falsey_injected_transport():
    class FalseyTransport:
        def __init__(self):
            self._transport = make_transport(FakeSerial([":READ:MOD:CHAN?", "1"]))

        def __bool__(self):
            return False

        def query(self, cmd):
            return self._transport.query(cmd)

        def read(self):
            return self._transport.read()

        def close(self):
            self._transport.close()

    transport = FalseyTransport()

    nhr = NHR("COM1", transport=transport)

    assert nhr.channel0 is not None


def test_voltage_bounds_queries_bounds_command_and_removes_only_suffix_unit():
    transport = make_transport(
        FakeSerial([":READ:MOD:CHAN?", "1", ":READ:VOLT:BOU? (@0)", "10V"])
    )
    nhr = NHR("COM1", transport=transport)

    assert nhr.channel0.voltage.bounds == pytest.approx(10.0)
    assert transport._serial.writes[-1] == b":READ:VOLT:BOU? (@0)\r\n"


def test_unit_parser_removes_only_suffix_unit():
    assert remove_suffix("1V0V", "V") == "1V0"


def test_supply_write_does_not_add_extra_parenthesis():
    transport = make_transport(FakeSerial([":READ:MOD:CHAN?", "1", ":TEST"]))
    nhr = NHR("COM1", transport=transport)

    nhr.supply._write(":TEST")

    assert transport._serial.writes[-1] == b":TEST\r\n"


def test_channel_properties_are_instance_safe():
    one_channel = NHR(
        "COM1", transport=make_transport(FakeSerial([":READ:MOD:CHAN?", "1"]))
    )
    two_channels = NHR(
        "COM2", transport=make_transport(FakeSerial([":READ:MOD:CHAN?", "2"]))
    )

    assert one_channel.channel(0) is one_channel.channel0
    assert one_channel.channel0 is not two_channels.channel0
    with pytest.raises(ValueError, match="channel index"):
        one_channel.channel(1)
    with pytest.raises(AttributeError):
        one_channel.channel1


def test_on_and_off_reject_negative_channel_ids():
    nhr = NHR("COM1", transport=make_transport(FakeSerial([":READ:MOD:CHAN?", "1"])))

    with pytest.raises(ValueError, match="channel index"):
        nhr.on([-1])
    with pytest.raises(ValueError, match="channel index"):
        nhr.off([-1])


def test_inhibit_commands_use_leading_colon():
    transport = make_transport(
        FakeSerial([":READ:MOD:CHAN?", "1", ":CONF:INH:ACT? (@0)", "1"])
    )
    nhr = NHR("COM1", transport=transport)

    assert nhr.channel0.inhibit == nhr.channel0.inhibit_options[1]

    transport._serial.responses.append(b":CONF:INH:ACT 2,(@0)\r\n")
    nhr.channel0.inhibit = 2

    assert transport._serial.writes[-2:] == [
        b":CONF:INH:ACT? (@0)\r\n",
        b":CONF:INH:ACT 2,(@0)\r\n",
    ]
