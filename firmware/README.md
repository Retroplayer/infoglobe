# Infoglobe experiment controller — RP2040 Zero

USB serial control of an Olympia Infoglobe rotor through the external 555-based IR transmitter. Firmware controls **SIG only**, with no software carrier generation. Default output is **GP2**, idle LOW. HIGH enables the module's carrier.

For the separately built receiver image and host analyzer, see [IR capture tools](../tools/README.md).

## Flash and connect

Download the [prebuilt UF2](prebuilt/infoglobe_lab.uf2) using GitHub’s **Download raw file** button. This image uses GP2 for SIG. Its SHA-256 is recorded in [SHA256SUMS](prebuilt/SHA256SUMS). Local build output: `build/infoglobe_lab.uf2`. Hold BOOT while connecting USB (or use the board's BOOT/RESET buttons), then copy that UF2 to the `RPI-RP2` drive. After reboot, open its USB serial port in a terminal with local echo enabled. Select 115200 baud and LF or CRLF line endings; USB CDC does not use the selected baud rate for transmission timing. Type `help` to see commands. The firmware does not wait for a serial connection to start.

All commands are case-sensitive. Each command occupies one line. Byte arguments are **hexadecimal**, with optional `0x`; timing arguments are **decimal**. Text is literal: omit surrounding quotes, and do not use `\n`/`\xNN` escapes. A single space or tab separates the command/opcode from text; any additional spaces are included in the message. ASCII text is the simplest starting point; UTF-8 is transmitted as its original bytes, not converted into rotor glyphs.

## Commands

| Command | Operation |
| --- | --- |
| `static HELLO RB5X` | Send `01` followed by text. |
| `scroll HELLO RB5X` | Send `04` followed by text. |
| `toggle` | Send `06` to toggle scrolling of the current message. |
| `effect 0C HELLO` | Send `00 00`, text, then effect byte `0C` (decimal 12). |
| `cmd 03 HELLO` | Send any first opcode followed by text; no opcode whitelist. |
| `raw 02 01 48 49` | Send exactly these bytes. Supports arbitrary binary payloads and unknown commands. |
| `bit 1000` | Set bit-cell duration, 100–10000 microseconds. Default 1000. |
| `gap 20` | Set minimum trailing silence, 1–60000 milliseconds. Default 20. |
| `polarity 1` | Protocol zero = SIG HIGH; protocol one = SIG LOW. Default for this module. |
| `polarity 0` | Reverse the mapping during packets for experiments. Idle remains LOW. |
| `repeat 2000` | Repeat the most recent packet, waiting 2000 ms after its trailing gap. |
| `repeat 0` | Disable repetition. This is the default. |
| `stop` | Abort an active packet and disable repetition; return SIG LOW. |
| `status` | Show pin, timing, polarity, repetition, activity and last packet length. |
| `help` | Print command reference. |

Normal messages need only one transmission. `stop` stops our transmitter; it does not clear or stop effects already running on the rotor. Settings and the last packet are held in RAM and reset on power cycling.

Text helpers allow up to 35 **bytes** of text; empty text is allowed. `raw` allows 1–256 bytes, including `00`, `FF`, bytes above `7F`, and longer-than-normal experimental packets. Maximum input line: 1023 bytes. A malformed or oversized line is rejected in full rather than partially transmitted. Backspace is supported before overflow; after overflow, finish the line and retry.

The firmware prints the exact bytes before transmission:

```text
scroll HI
TX 3: 04 48 49
DONE
```

`DONE` means the local transmitter completed, not that the rotor acknowledged or understood it. No acknowledgement mechanism is implemented. Wait for `DONE` and the configured gap before sending another packet. A packet sent too early gets an error and must be retried. Commands that change settings are rejected during transmission; `help`, `status`, and `stop` remain available. Repetition always uses the last accepted packet and current settings, without queueing.

## Experiment examples

```text
static BASELINE
cmd 03 TEST
raw 02 01 48 49
raw 05 48 49 00 01 02
effect 06 TEST
effect 16 TEST
raw 81 00 7F 80 FF
```

Run these individually, observe the result, and record it with the reported bytes and `status`. The `02`/`05` forms above are candidates from contradictory published flashing descriptions, not verified commands. Effects `06` and `16` are examples missing descriptions in the collected transition notes. First-byte opcodes and effect bytes are separate namespaces. `effect` deliberately accepts all 256 values, including undocumented ones. See [protocol research](../docs/protocol.md) for known effects and remaining gaps.

For timing experiments:

```text
bit 950
scroll TIMING TEST
```

For periodic replay, first send the desired packet, wait for completion, then enter `repeat 2000`. Enter `stop` to end replay. Capture the USB terminal session to retain results. Serial output is nonblocking: if a host stops reading and its buffers fill, log output may be dropped to preserve transmission service.

## Timing implementation

The Pico SDK firmware uses PIO0 and one state machine. Each bit occupies 33 PIO clocks; a fractional clock divider sets the requested bit duration. Bits are MSB first, with no UART start/stop bits, extra byte gaps, checksum or appended terminator. Consecutive equal bits form continuous levels. After the final bit, PIO drives SIG LOW and raises its completion interrupt flag. The configured gap is additional silence; `raw` bytes such as `FF` are still transmitted as requested.

The CPU feeds the joined eight-word TX FIFO while continuing to service serial commands. A detected FIFO underrun aborts transmission, disables repetition, and reports an error. `stop` may truncate a packet deliberately; its result on the rotor depends on how much was already received.

## Build

Requires Raspberry Pi Pico SDK **2.2.0**, its TinyUSB submodule, an Arm bare-metal GCC toolchain, CMake and Ninja. Tested with Arm GNU **13.3.Rel1**. From the repository root, with those tools on PATH:

```sh
cmake -S firmware -B firmware/build -G Ninja \
  -DPICO_SDK_PATH=/path/to/pico-sdk \
  -DPICO_BOARD=waveshare_rp2040_zero
cmake --build firmware/build -j 4
```

To change SIG GPIO, add `-DINFOGLOBE_SIG_PIN=3` to the configure command. The prebuilt image uses GP2. The SDK downloads/builds its matching picotool automatically when needed to create UF2 output.

In this cloud workspace, `bash scripts/setup-cloud.sh` installs the pinned tools outside the checkout, builds the firmware and runs its tests. Subsequent builds need only:

```sh
/workspace/infoglobe-tools/bin/cmake --build firmware/build -j 4
bash scripts/test-firmware.sh
```

Validation includes an Arm cross-build, native parser/packet tests with AddressSanitizer and UndefinedBehaviorSanitizer, and independent emulation of the assembled PIO instructions for 16 packet-length/polarity combinations. The emulator checks exact bit count, MSB order, 33-cycle timing through FIFO-word boundaries and idle LOW. **Physical RP2040/Infoglobe operation has not yet been tested.**
