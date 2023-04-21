# iseg-nhr
[![Python versions on PyPI](https://img.shields.io/pypi/pyversions/iseg-nhr.svg)](https://pypi.python.org/pypi/iseg-nhr/)
[![iseg-nhr version on PyPI](https://img.shields.io/pypi/v/iseg-nhr.svg "iseg-nhr on PyPI")](https://pypi.python.org/pypi/iseg-nhr/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

Python interface for an ISEG NHR high-voltage power supply

## Example
```Python
from iseg_nhr import NHR, Polarity

psu = NHR("COM3")

polarity = psu.channel0.voltage.polarity
print(polarity)

psu.channel0.voltage.setpoint = 1_000
psu.channel0.on()
print(psu.channel0.voltage.measured)
print(psu.channel0.current.measured)
```

## Implementation
The main NHR class has the following attributes and methods:  
`NHR`
* `channel{i}`  
  `Channel` class specifying all options for a specific channel
* `supply`  
  `Supply` class containing the supply voltages 
* `identity`  
  *IDN?; model, serial number etc.
* `status_clear()`  
  *CLS
* `reset`  
  *RST
* `operation_complete`  
  *OPC
* `instruction_set`  
  instruction set used by the module
* `lockout()`  
  Disable local control of the module
* `local()`  
  Enable local control of the module
* `control_register`  
  module control register 
* `status_register`  
  module status register
* `event_register`  
  module event register
* `event_clear()`  
  clear the module event register
* `temperature`  
  module temperature
* `number_channels`  
  number of module channels
* `firmware_version`  
  firmware version
* `firmware_release`  
  firmware release date
* `config`  
  config mode, either normal or configuration mode
* `config_save`  
  save current configuration
* `voltages`  
  return the measured voltage of each channel
* `currents`  
  return the measured current of each channel
* `setpoints`  
  return the setpoint voltage of each channel
* `on([0,1])`  
  turn on channels 0 and 1
* `off([0,1])`  
  turn off channels 0 and 1

`Channel`
* `voltage`  
  `Voltage` class
* `current`  
  `Current` class
* `on_state`  
  boolean for on state of channel
* `on()`  
  turn channel on
* `off()`  
  turn channel off
* `emergency_off()`  
  turn channel off immidiately, ignoring ramp settings
* `emergency`  
  boolean for channel emergency
* `emergency_clear`  
  clear channel emergency
* `event_clear()`  
  clear channel events
* `control_register`  
  channel control register
* `status_register`  
  channel status register
* `event_register`  
  channel event register
* `polarity`  
  channel polarity
* `polarity_list`  
  list of channel polarity options
* `output_mode`  
  channel output mode
* `output_mode_list`  
  channel output mode options
* `inhibit`  
  channel inhibit setting
* `inhibit_options`  
  channel inhibit options

`Voltage`
* `ramp`  
  `Ramp` class
* `measured`  
  measured output voltage
* `setpoint`  
  voltage setpoint
* `limit`  
  voltage limit
* `maximum`  
  nominal output voltage
* `maximum`  
  voltage mode with polarity sign
* `mode_list`  
  voltage mode options
* `bounds`  
  output voltage bounds

`Current` has the same attributes and methods, excluding the setpoint

`Ramp`
* `speed`  
  ramp speed in unit/s
* `speed_up`  
  upward ramp speed in unit/s
* `speed_down`  
  downward ramp speed in unit/s
* `speed_min`  
  minimum ramp speed in unit/s
* `speed_max`
  maximum ramp speed in unit/s