from enum import Enum


def get_set_bits(value: int, nr_bits: int):
    return [i for i in range(nr_bits) if (value >> i) & 1]


class ChannelStatusRegister(Enum):
    IsPositive = 0
    IsArc = 1
    IsInputError = 2
    IsOn = 3
    IsVoltageRamp = 4
    IsEmergencyOff = 5
    IsConstantCurrent = 6
    IsConstantVoltage = 7
    IsLowCurrentRange = 8
    IsArcNumberExceeded = 9
    IsCurrentBounds = 10
    IsVoltageBounds = 11
    IsExternalInhibit = 12
    IsCurrentTrip = 13
    IsCurrentLimit = 14
    IsVoltageLimit = 15
    IsCurrentRamp = 16
    IsCurrentRampUp = 17
    IsCurrentRampDown = 18
    IsVoltageRampUp = 19
    IsVoltageRampDown = 20
    IsVoltageBoundUpper = 21
    IsVoltageBoundLower = 22


class ChannelEventRegister(Enum):
    Arc = 1
    InputError = 2
    OnToOff = 3
    EndOfVoltageRamp = 4
    EmergencyOff = 5
    ConstantCurrent = 6
    ConstantVoltage = 7
    ArcNumberExceeded = 9
    CurrentBounds = 10
    VoltageBounds = 11
    ExternalInhibit = 12
    CurrentTrip = 13
    CurrentLimit = 14
    VoltageLimit = 15
    EndOfCurrentRamp = 16
    CurrentRampUp = 17
    CurrentRampDown = 18
    VotageRampUp = 19
    VoltageRampDown = 20
    VotageBoundUpper = 21
    VoltageBoundLower = 22


class ChannelControlRegister(Enum):
    SetOn = 3
    SetEmergencyOff = 5


class ControlRegister(Enum):
    DoClear = 6
    SetBigEndian = 11
    SetFineAdjustment = 12
    SetKillEnable = 14
    DisableVoltageRampSpeedLimit = 16


class StatusRegister(Enum):
    IsFineAdjustment = 0
    IsHighVoltageOn = 3
    IsService = 4
    IsInputError = 6
    IsNoSumError = 8
    IsNoRamp = 9
    IsSafetyLoopGood = 10
    IsEventActive = 11
    IsModuleGood = 12
    IsSupplyGood = 13
    IsTemperatureGood = 14
    IsKillEnable = 15
    IsFastRampDown = 16
    IsVoltageRampSpeedLimited = 21


class EventRegister(Enum):
    Service = 4
    InputError = 6
    SafetyLoopNotGood = 10
    SupplyNotGood = 13
    TemperatureNotGood = 14
