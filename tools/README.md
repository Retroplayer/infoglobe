# Infoglobe IR capture and reverse-engineering tools

These tools capture the **original base's IR data transmission**, distinguish understood traffic from discoveries, and correlate unfamiliar packets with visible behavior. The implementation includes recorder firmware, a USB logger, offline/live decoding, recognition rules, filters, markers, comparisons, exports, and approximate timed replay through the existing transmitter.

## 1. Install the host tools

Download or clone this repository, open a terminal in its root, and install Python **3.10 or newer** and the host dependency:

```sh
git clone https://github.com/Retroplayer/infoglobe.git
cd infoglobe
python -m venv .venv
```

Activate the environment:

```sh
# Linux/macOS
source .venv/bin/activate
# Windows PowerShell
.venv\Scripts\Activate.ps1
```

Then:

```sh
python -m pip install -r tools/requirements.txt
python -m tools.infoglobe --help
```

Run commands below from the repository root. Do not open another serial terminal on the same port during capture.

## 2. Flash the recorder

Download [infoglobe_capture.uf2](../firmware/prebuilt/infoglobe_capture.uf2) with GitHub's **Download raw file** button. Put the RP2040 Zero into BOOT mode and copy the file to `RPI-RP2`.

This image samples **GP3** (receiver DAT) at **1 MHz**. Receiver output is interpreted as active LOW by default. The user handles the electrical interface and optical alignment. Aim at the original base's **data LED**, distinct from the rotation-reference emitter.

The recorder uses USB CDC with a binary stream; use the host tool below rather than a text terminal. Find its port using:

```sh
python -m serial.tools.list_ports
```

Typical names are `COM5`, `/dev/ttyACM0`, or `/dev/cu.usbmodem...`. Substitute your actual port in the examples.

The [transmitter image](../firmware/prebuilt/infoglobe_lab.uf2) is a separate image using GP2 for its SIG output. Use a second controller for simultaneous controlled transmission and capture, or swap firmware for separate experiment stages.

## 3. Capture the demo and hide understood traffic

```sh
mkdir captures
python -m tools.infoglobe capture --port COM5 --output captures/demo-01.igcap --view new --include-uncertain
```

`new` shows **unknown and partially understood** packets. `--include-uncertain` also shows timing/capture problems, separately labeled. Known packets remain in the file. For strictly unknown traffic, use `--view unknown` without `--include-uncertain`.

The program starts the recorder automatically. Start the original Infoglobe demonstration after capture begins and record at least two complete cycles. Record video if possible.

While capture runs, type these in the same terminal and press Enter:

```text
message appeared at three locations
/mark flashing overlay started
/view all
/view new
/view unknown
/status
/stop
```

Ordinary text is an observation marker. `/mark TEXT` is equivalent. Filters change only the view. Hidden-traffic counts indicate where omitted packets occurred. `/status` requests recorder state. `/stop` or Ctrl-C requests a clean stop and waits for queued data. A second Ctrl-C exits immediately and may leave a truncated recording. You can also pass `--duration 120` to stop automatically after 120 seconds.

Leave a little idle time after the last behavior of interest before stopping. A clean stop preserves completed sample blocks and DMA-transferred words in the final partial block; up to **287 final samples (287 microseconds)** can remain in the PIO FIFO/incomplete word. The END record declares this bound. Loss/overflow is reported separately and has no such duration guarantee.

Files created:

| File | Contents |
| --- | --- |
| `demo-01.igcap` | Original binary CDC stream, saved before decoding; all traffic. |
| `demo-01.igcap.analysis.json` | Events, measured timings, interpretations, rule versions, metadata, device markers and warnings. |
| `demo-01.igcap.notes.jsonl` | Host marker submission times in UTC and monotonic time. |

Existing output files are not overwritten. Use a new experiment name. If the device disconnects, the logger preserves the partial recording and reports the interruption. Reconnect/reset the recorder before starting a fresh capture after a disconnect or overflow. Capture exits with a nonzero status when problems were detected.

The marker in the binary stream contains a device receipt timestamp and an estimated sample index, with a declared **288-sample** uncertainty bound from FIFO/word quantization. Host submission and device receipt differ because of USB/control processing. Synchronize video using a shared visible event and marker; do not assume USB arrival time is acquisition time.

## 4. Validate with known patterns first

Use the transmitter firmware's serial commands, one at a time:

```text
bit 1000
polarity 1
raw 55 AA 55 AA
raw 00
raw 00 00 00 00
raw 55 FF AA
scroll HI
static HI
effect 0C HI
```

Check the captured raw timings against the transmitted patterns. Alternation tests edges; zero bytes test long uninterrupted carrier; the bounded `55 FF AA` pattern tests a silent byte. `FF` on its own cannot be distinguished from idle optically. Some validation patterns are deliberately not meaningful display commands, so their semantic classification need not be known.

Characterize any long-carrier suppression by the receiver before attributing distorted packets to an unknown protocol. This validation is an actual hardware experiment; it has not been performed by the automated tests.

## 5. Reanalyze and inspect context

```sh
python -m tools.infoglobe analyze captures/demo-01.igcap --view new --context 2 --include-uncertain --json captures/demo-01.analysis-v2.json
python -m tools.infoglobe analyze captures/demo-01.igcap --view all
python -m tools.infoglobe summary captures/demo-01.igcap
python -m tools.infoglobe summary captures/demo-01.igcap --exact
```

The default summary groups by classification, command family and effect; `--exact` groups identical byte sequences. Context expands packets before and after unfamiliar events, including hidden known commands. Device markers print with acquisition-relative times. Every event's JSON includes raw level/duration runs for detailed inspection. Sessions remain separate when several starts appear in one file.

Recognition classes:

- **known**: recognized structure, understood parameters/effect, and ordinary text bytes.
- **partial**: recognized family with unresolved structure, effect, glyphs or parameters. Commands `02`, `03`, and `05` remain partial; unidentified transition effects also remain partial.
- **unknown**: bytes decoded under the selected framing assumptions, with no recognized command structure.
- **uncertain**: timing, continuity, loss, or framing problems prevent reliable interpretation.

`known` initially means supported by the published research, **not confirmed on our unit**. Each event records its evidence and rule version. Recognition cannot prove that a command was accepted by the rotor.

Decoding options may be changed without altering the recording:

```sh
python -m tools.infoglobe analyze captures/demo-01.igcap --bit-us 1000 --gap-ms 30 --tolerance 0.20 --view all
python -m tools.infoglobe analyze captures/demo-01.igcap --leading-ones 1 --view all
python -m tools.infoglobe analyze captures/demo-01.igcap --active-high --view all
```

`--bit-us` is the initial timing estimate. The decoder estimates cell duration using adjacent opposite-level run pairs to reduce demodulator pulse-stretch bias. `--tolerance` is the maximum residual error in bit cells. Short pulses remain in the recording and decoder; there is no automatic glitch removal.

**Framing is provisional:** the default assumes the first detected carrier begins the first byte's bit 7, and appends only enough silent bits to finish the last byte. A command beginning with one or more silent bits needs `--leading-ones N` (0–7). Extra trailing `FF` bytes cannot be recovered from envelope silence alone. A long internal run of ones can resemble a packet gap; compare different `--gap-ms` values and inspect raw timings. These assumptions are recorded with each event. An unknown classification is a candidate discovery to validate by replay, not proof of a new opcode.

## 6. Add recognition rules for discoveries

Create a JSON file with exact-length byte patterns. Integers are **decimal JSON numbers**; `null` matches one byte. This is an illustrative hypothesis, **not a discovered command**:

```json
[
  {
    "id": "experiment-07",
    "pattern": [7, 16, null],
    "classification": "partial",
    "family": "experiment-07",
    "interpretation": "Candidate command 07 with parameter and payload",
    "reason": "Repeated in demo; meaning still being tested",
    "evidence": "demo-01 event 2; hypothesis, not confirmed"
  }
]
```

Then:

```sh
python -m tools.infoglobe analyze captures/demo-01.igcap --rules my-rules.json --view new --json captures/demo-01.rules-v1.json
```

The same `--rules` option works during live capture, summary and export. A single matching custom rule overrides the built-in interpretation. Conflicting matches are labeled partial. The complete custom rules are embedded in analysis settings, and each matched event has a content-derived rule version. Promote a rule to `known` only after reproducing its behavior and documenting parameter/state dependencies. Reanalysis leaves the original recording unchanged.

## 7. Export and replay

Inspect an unfamiliar event, including surrounding traffic:

```sh
python -m tools.infoglobe export captures/demo-01.igcap --event 3 --before 2 --after 1 --output captures/candidate-03.json
python -m tools.infoglobe replay captures/candidate-03.json --dry-run
```

`--event` is the event ID printed by analysis using the same decoder settings. Pass the same timing, alignment and custom-rule options to export. Context is limited to the selected session. Uncertain decodes require explicit `--allow-uncertain` for export and replay.

For actual replay, run the **transmitter firmware** on a controller with the 555 IR module. Prevent original-base data traffic from competing during the replay, and restore any required initial display state. Then:

```sh
python -m tools.infoglobe replay captures/candidate-03.json --port COM6
```

The tool disables repetition, selects normal polarity, sets bit timing, sends exact inferred bytes, waits for each `DONE`, and approximates recorded packet-start spacing. It stops on transmitter errors or excessive dispatch lateness and sends `stop` on exit. `--max-late-ms` defaults to 20; `--speed 0.5` doubles the spacing between packet starts without changing within-packet bit timing.

**Replay spacing is host-timed over CDC, not hardware scheduled.** Serial transit and the transmitter's command processing add latency beyond the reported host dispatch lateness. Sequences with less than 3 ms of usable inter-packet space are rejected. USB/OS overhead may require substantially more. Exact start/stop gaps and invisible trailing `FF` bytes are not guaranteed; the dry run exposes the inferred packets before transmission. Packet payloads must fit the transmitter's 256-byte limit and 100–10000 microsecond bit range.

First reproduce the captured behavior without changes. Then edit one field in the exported `events[].bytes` array at a time and compare results. Preserve the original export as evidence. The replay command uses that byte array; its old `hex` and interpretation fields do not automatically update after hand editing. Record initial state, modified bytes, packet timing, and visible behavior.

## 8. Exercise the tools without hardware

```sh
python -m tools.synthetic captures/synthetic.igcap
python -m tools.infoglobe analyze captures/synthetic.igcap --view new --context 1
python -m tools.infoglobe export captures/synthetic.igcap --event 3 --before 1 --after 1 --output captures/synthetic-replay.json
python -m tools.infoglobe replay captures/synthetic-replay.json --dry-run
python -m unittest discover -s tools/tests -v
```

The generated recording is explicitly synthetic, containing three known packets, one unknown opcode candidate, and one undocumented transition effect. It is not a capture of an actual Infoglobe. Tests exercise stream framing/CRC/recovery, timing distortion, DMA-boundary reconstruction, long runs, uncertain captures, nondestructive filtering, export, live logger behavior with a simulated serial connection, and transmitter handshakes.

The recorder cross-builds, and its assembled sampler has an independent PIO-emulator test. **Physical USB/DMA/receiver operation and actual demo decoding have not yet been verified on hardware.** The first real recording is the next validation step.

## Recorder implementation and wire format

The separately buildable target is `infoglobe_capture`; `infoglobe_lab` remains the transmitter. Both are generated by the [firmware build](../firmware/README.md#build). Set `-DINFOGLOBE_RX_PIN=N` at configure time to change receiver GPIO. The prebuilt receiver uses GP3.

PIO samples one input bit per clock at 1 MHz, shifting left and autopushing every 32 bits. Two chained DMA channels rotate through eight 4096-byte buffers. Full blocks contain 32768 samples (32.768 ms). Main-loop USB writes are nonblocking. Buffer exhaustion or a PIO RX stall halts acquisition and produces a LOSS record after the valid queued blocks. A new start creates a new session and sample index origin. Packed data needs about **125 kB/s**, or **7.5 MB/minute** before framing overhead; this first implementation preserves packed samples directly instead of compressing them on-device.

Every device-to-host record is little endian:

| Field | Size |
| --- | --- |
| Magic `IGCP` | 4 bytes |
| Version (1), type | 1 byte each |
| Flags (0) | 2 bytes |
| Sequence number | 4 bytes |
| Acquisition sample index | 8 bytes |
| Payload length | 4 bytes |
| Payload | Length above |
| CRC-32/IEEE of header plus payload | 4 bytes |

Types: 1 metadata JSON, 2 packed samples, 3 marker, 4 status JSON, 5 clean END JSON, 6 LOSS JSON. Samples are little-endian uint32 words with the earliest sample in bit 31. A marker payload is an eight-byte device receipt time in microseconds followed by UTF-8 observation text. Metadata declares sample rate, GPIO, polarity, format and session ID. CRC failure, sequence gaps, sample discontinuities and missing END/LOSS records are reported; decodes never join across such gaps.

Host-to-device controls are ASCII lines: `start`, `stop`, `status`, `mark TEXT`. They are intended to be sent by the host tool. Observation text is limited to 190 UTF-8 bytes by the logger. Control acknowledgements/status also use framed records, never unframed text mixed into samples.

Keep the original [project plan](../docs/ir-capture-plan.md) and [protocol evidence](../docs/protocol.md) alongside recordings when documenting discoveries.
