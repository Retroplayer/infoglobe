# RB5X head output for the Infoglobe transmitter

Studied 2026-10-19. Goal: reuse the existing flashing-light channel to gate the 38 kHz 555 transmitter directly from the INS8073.

## Schematics obtained and examined

- [Original RB5X reference manual](schematics/original-reference-manual.pdf), electronics section dated 11/01/84. PDF page 78 is the CPU-board schematic, page 77 the motherboard/backplane interconnect, and page 80 the LED-board schematic. PDF page 64, printed C-10, supplies the memory map; page 62, C-8, identifies the internal I/O controller.
- [CPU-board schematic, upright](schematics/cpu-schematic.png), drawing **5X006**.
- [Motherboard/backplane interconnect, upright](schematics/motherboard-interconnect-schematic.png), drawing **5X005**. The RB5X terminology distinguishes the active CPU card from the passive motherboard/backplane; both were examined.
- [LED-board schematic](schematics/LedBoardScha.gif), board part **3001-05000**, also [alternate drawing](schematics/LedBoardSch.gif), from RB Robotics' [LED-board parts page](https://www.rbrobotics.com/Support/led_board_parts.htm).
- [Backplane connector-location drawing](schematics/back_plane.gif). Manual connector table identifies **J9/P9** as the 20-pin LED-card connection.
- [Later reference manual](schematics/reference-manual.pdf), including its `@#7801=#02` undercarriage IR-LED example. The programming guide separately states that LED 1 is the undercarriage IR emitter and LEDs 2–5 are the four individually programmable visible positions.

The Norland archive's motherboard and LED PDFs were also downloaded and examined. Those sheets are fabrication artwork (drill/soldermask/copper), not circuit schematics; the archive warns some tape lines are missing. Their URLs/hashes are recorded, but the large fabrication PDFs are kept in temporary research storage rather than this repository. Do not confuse those drawings with the CPU and interconnect schematics above.

## CPU control path

The INS8073 communicates with **U4, INS8255**, the PPI dedicated to the robot's internal I/O. Its register addresses are:

| Address, hexadecimal | Register |
| --- | --- |
| `7800` | Port A, bumper inputs |
| `7801` | Port B, sonar enable, lighting and horn |
| `7802` | Port C, motor and sensing functions |
| `7803` | Control register; documented normal setup `98` |

Port B's lighting outputs run through the CPU board's **U5, MC1413** Darlington driver. The relevant allocation read from the CPU schematic, cross-checked against the published undercarriage-LED example and four-visible-LED description, is:

| Port B bit | Mask | Function |
| --- | --- | --- |
| PB0 | `01` | Sonar control path |
| PB1 | `02` | LED 1, undercarriage IR emitter |
| PB2 | `04` | Individually controlled visible LED 2 |
| PB3 | `08` | Individually controlled visible LED 3 |
| PB4 | `10` | Individually controlled visible LED 4 |
| PB5 | `20` | Individually controlled visible LED 5 |
| **PB6** | **`40`** | **LED 6 / flashing-light channel to repurpose** |
| PB7 | `80` | Horn driver |

For the selected channel: **U4 PB6, pin 24 → U5 input pin 7 → U5 output pin 10 → LED6 net → CPU connector J7 pin 30**. The backplane carries the head connection through J9/P9. The low-resolution head/interconnect drawings use several different connector/pad numbering systems; a specific head solder-pad number is not assigned here without an unambiguous reading. J7 pin 30 is the CPU-card connector designation, not a claim that a 20-pin head connector has 30 positions.

The scan is low resolution. Preserve this distinction between port identity, IC pins, CPU connector numbering, and head pad numbering when checking the actual assembly.

## What makes the original lights flash

The head schematic and parts list show **four FCC92 flasher devices, U1–U4**, plus a separate **MC1413, U5**, diode D1 (1N4001), five 330-ohm resistors and 21 LEDs. Thus the flashing hardware is on the LED board; the CPU's output is an enable/feed for that function, not a mandatory software-generated periodic waveform.

The head and CPU both contain a component called U5/MC1413. They are different ICs. The selected PB6 path above refers to the **CPU-board U5**.

For the Infoglobe, take over the controllable channel **before the FCC92 flashing stage**. We want the INS8073's timed gating signal, not the FCC92's slow flash output. The original flashing branch can be disconnected/replaced as part of that conversion.

## Driving the supplied 555 module

The module's supplied specification says: 4.5–5.5 V power, SIG HIGH emits 38 kHz, SIG LOW stops it. That gives two practical tap choices:

### Reuse the existing driver output at the head

The MC1413 output is an **open-collector current sink**. Use the repurposed collector signal with a pull-up to the transmitter's 5 V supply after separating it from the original flasher load/feed. It is not a push-pull logic output.

| Infoglobe bit / state | PB6 written by CPU | Driver output / SIG |
| --- | --- | --- |
| `0`, carrier on | 0 | Released, pulled HIGH |
| `1`, carrier off | 1 | Sunk LOW |
| Idle | 1 | LOW, no carrier |

The driver's inversion means that the CPU bit follows the protocol bit in this arrangement. Do not connect the module to a node still being driven by a separate FCC92 oscillator.

### Tap before the CPU driver

PB6 at the PPI/MC1413 input is the noninverted logic signal. If using that point, SIG follows PB6: carrier-on requires PB6=1, so the software mapping is opposite to the collector-output option. This is an alternative, not a requirement to modify the CPU card when the existing head wire can be reused.

## Software implications

- Write the existing Port B latch at `#7801` with PB6 changing every 1 ms as needed. There is no need for a new PPI, extra carrier generator, or Arduino merely to send messages.
- Preserve all other Port B bits. Maintain a shadow byte and precompute versions with bit 6 clear/set; send those two values from the machine-code routine. Writing only `00` and `40` to the whole port would also alter the horn, sonar and other LEDs.
- The documented `#98` initialization is a mode-set write, not something to repeat per bit or per packet. Mode changes reset output state.
- Leave SIG low after the final bit. With the collector tap that means leave PB6 set while preserving the other bits.
- Existing code that writes whole-port lighting patterns, including flashing demos, must not overwrite PB6 during a transmission. Assign that bit to the display routine.

This establishes an appropriate existing control channel and its software/electrical mapping from public documentation. No physical RB5X wiring or transmitter test has been performed.

## Provenance

Original URLs, retained-file hashes, derived-image pages and the fabrication-artwork distinction are recorded in [schematics/sources.json](schematics/sources.json). These are third-party historical documents; rights remain with their owners. The later reference manual's prose/examples and the 1984 scanned circuit diagrams were kept distinct.
