# Protocol review (2026-10-21)

Reviewed the serial protocol, implemented command families, units, and register
maps against the official [SCPI programming guide v3.2](https://iseg-hv.com/download/SOFTWARE/isegSCPI/SCPI_Programmers_Guide_en.pdf)
and [NHR manual v2.7](https://iseg-hv.com/download/SYSTEMS/NIM/NHR/archive/iseg_manual_NHR_en_2.7.pdf).

- Guide section 3.1: 9600 baud, 8N1, ASCII, CRLF, echo handling, and complete
  transaction sequencing. Writes now append `;*OPC?` and consume completion.
- Guide section 6: emergency commands corrected to `:VOLT EMCY OFF` and
  `:VOLT EMCY CLR`. Channel addressing, event clearing, ramp queries and
  voltage/current units were checked. Current remains in A.
- Guide section 9: added missing flashover status/event bits 26 and 27.
- NHR section 5.5: polarity changes now require OFF and discharge below
  `0.002 * Vnom`, replacing the exact-zero check.

Completion acknowledges processing, not physical output state. The Set On flag
is a control flag; inspect status and measurements for output behavior.

Regression tests use simulated transports. Installed firmware, hardware options,
timing under real serial faults, and physical operation still require hardware
acceptance testing. No device commands were sent during this review.
