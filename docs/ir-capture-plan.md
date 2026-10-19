# Infoglobe IR reverse-engineering recorder and analyzer

Status: agreed project goals and proposed implementation, 2026-10-19. **Capture firmware and the host analyzer described here are not implemented yet.** The existing [RP2040 transmitter firmware](../firmware/README.md) is built and available for replay and controlled experiments.

## Goal

Discover how the original Olympia OL3000.2 base commands the rotor's advanced display behavior, then reproduce that behavior with our replacement controller inside an RB5X robot dome.

The workflow is:

**Capture original transmissions → identify unfamiliar traffic → correlate with visible behavior → replay captured sequences → vary individual bytes → document confirmed meanings.**

We specifically want static messages, scrolling, multiple message locations, flashing, transitions, and any additional behaviors exposed by the original demonstration. Capturing IR or listing unknown opcodes alone does not complete this project. The result must be usable commands and sequences, with evidence of their effects.

## Hardware and responsibilities

- A 38 kHz demodulating IR receiver module, proposed HX-M121, aimed at the original base's **data** IR LED.
- An RP2040 Zero to capture the receiver output.
- USB CDC to transfer captures and accept recorder controls.
- A computer to store, decode, classify, filter, annotate, and compare recordings.
- The existing transmitter firmware and 555 carrier module for subsequent replay experiments.

The recorder observes the original base during capture; it does not replace its transmissions. The base also has an optical rotation-reference emitter, which is distinct from the data emitter.

The user handles electronics. Software must support a configurable receiver GPIO and explicit polarity. The pictured receiver is expected to be active LOW when carrier is detected, but its actual output must be checked using known transmissions. With that polarity, LOW corresponds to the protocol's logical zero.

This module exposes the carrier **envelope**, not individual carrier cycles. Envelope captures cannot establish the actual carrier frequency or duty cycle.

## Recorder firmware requirements

### Acquisition

Use PIO and DMA to sample the receiver output at a proposed **1 MHz**, giving nominal 1 microsecond resolution for nominal 1000 microsecond bit cells. Use a continuous, packed-bit sample stream, with rotating DMA buffers and explicit continuity tracking. CPU processing converts samples into level/duration records for USB transport.

Sampling must not pause at byte boundaries, packet boundaries, USB writes, or when the host view filters events. Run lengths must carry across DMA-buffer boundaries without splitting or losing transitions. Idle time must be represented through timestamps or heartbeat records, including a final open run when recording stops.

The firmware must:

- Record both levels and their durations, including short glitches and long uninterrupted levels.
- Preserve acquisition time independently of USB arrival time.
- Number blocks and report dropped samples, buffer overflow, or transport loss explicitly.
- Start a new continuity segment after loss; never decode across an unrecorded interval.
- Keep USB output from blocking acquisition.
- Report firmware version, configuration, sample rate, GPIO, polarity, and session identity.
- Support start, stop, status, and host observation markers.
- Expose counters for samples, transitions, overruns, and transmitted blocks.

There is no requirement to save every expanded 1 MHz sample to disk. Lossless run-length records preserve the sampled envelope and are much smaller for ordinary traffic. If noise defeats compression, report the capacity limit or loss rather than silently dropping transitions.

### Transport and recording format

Use versioned, length-framed binary records over CDC, with record type, sequence number, payload length, and integrity checking. Do not mix unframed diagnostic text into the capture stream. Timestamp transition records using acquisition sample indices; host markers must distinguish host submission time from the acquisition index at which the device receives them.

The host saves the received records and session metadata before analysis. Preserve the original recording unchanged; derived decodes, classifications, filters, and annotations live separately. Include enough framing to find the next valid block after a damaged block.

Exact wire encoding and control-command syntax will be defined with the implementation. No capture CLI commands in this document should be interpreted as existing firmware commands.

## Decoder requirements

Start from the [published protocol baseline](protocol.md):

- Approximately 38 kHz carrier, gated in nominal 1000 microsecond cells.
- Carrier present = zero; absent = one.
- Bytes are MSB first, without UART start/stop bits.
- Normal packets begin with a command byte.
- Transition packets use `00 00`, text bytes, and an effect byte.

These are initial decoding rules, not assumptions that every recording must satisfy.

Estimate bit timing from the recording and retain the measured durations and residual error. A roughly 3 ms level normally represents three consecutive equal bits, not a single symbol. Receiver turn-on/turn-off delays can shorten one level and lengthen the adjacent level; avoid treating that systematic distortion as a different bit rate.

Separate **transport decoding confidence** from **knowledge of command meaning**. A cleanly decoded unknown command is a useful discovery. A corrupted known packet is an acquisition problem, not evidence of a new opcode.

Do not permanently split packets using one hard-coded silence threshold. Silence carries data ones as well as separating packets. Leading or trailing `FF` bytes, silent trailing bits, packet alignment, and the absence of a published exact receiver timeout can make boundaries ambiguous. Retain alternative framing candidates or explicitly mark ambiguity instead of manufacturing certainty.

Allow offline changes to timing tolerances, polarity, glitch treatment, and framing rules without recapture. Default to retaining glitches; any filter must be reversible and identified in analysis metadata.

## Recognition and classification

Classification applies to complete packet structures and sequences, not just the first byte.

| Class | Meaning | Example |
| --- | --- | --- |
| Known | Recognized structure and understood command/effect/parameters | `04 48 49`: scroll `HI` |
| Partially known | Recognized family with unresolved structure, parameter, effect, or behavior | Transition framing with an undocumented effect |
| Unknown | Reliably decoded candidate packet that matches no documented structure | Unrecognized first opcode with otherwise clean framing |
| Uncertain capture | Timing, loss, or framing prevents reliable interpretation | A dropped buffer or competing byte alignments |

Examples of initial recognition rules:

- `01` plus suitable text: known static-message command.
- `04` plus suitable text: known scrolling-message command.
- `06` alone: known scroll toggle.
- `00 00 ... EFFECT`: transition family; known only when the payload and specific effect match documented rules.
- `02` and `05`: partially known because published flashing descriptions conflict.
- `03`: partially known until its inherited-state behavior is adequately established.
- Unexpected parameters, lengths, binary glyph values, or trailing fields must not be labeled understood solely because the opcode is familiar.

The expected length must be checked using a rule appropriate to that command. A text-length limit alone is not a universal packet specification. Unknown glyphs can make a payload partially known without making its opcode new.

Each event must explain its classification, citing the recognition rule and supporting evidence. Keep literature-supported rules distinct from rules confirmed on our hardware. Store the decoder/rule-set version with analysis results so later updates are traceable.

## Live filtering and behavior correlation

Provide these views:

- All traffic.
- Unknown plus partially known.
- Unknown only.
- Independent visibility of uncertain captures.

Filtering changes the view, **never acquisition or the stored recording**. Show timestamp, raw bytes, interpreted fields, classification, and reason for every visible event.

The practical purpose is to watch the demo while concentrating on behavior around unfamiliar traffic. Offer an observation marker with a text note, and a timeline that associates the event with surrounding transmissions and video time where available.

Known transmissions can still change the display while hidden. The filtered timeline must indicate intervening hidden traffic and provide a way to expand it. Selecting an unfamiliar event should reveal configurable context before and after it, including known packets, gaps, and preceding display state.

Do not assume one packet causes one visible effect. Some effects may require setup, a message load, a trigger, and subsequent updates. Preserve packet groups with their original order and delays. A transition might continue long after transmission ends.

Unknown/partially known events should be exportable with context for replay and annotation. Group repeated observations by both exact bytes and command structure, so changing message text does not bury a repeated unknown control pattern.

## Experiment instructions

### 1. Validate the receiver and capture path

Once capture firmware is available, use the existing transmitter to generate known patterns. Set nominal timing and normal polarity:

```text
bit 1000
polarity 1
raw 55 AA 55 AA
raw 00
raw 00 00 00 00
raw FF
scroll HI
static HI
effect 0C HI
```

Send each line separately, waiting for transmitter completion and its configured gap. These are **existing transmitter commands**, not recorder commands. If using a single RP2040, it cannot simultaneously run the separate transmitter and proposed recorder images; use a second transmitter controller or perform validation in separate stages.

Compare the captured levels and durations with the transmitted bits. The `55 AA` pattern exercises transitions; `00` exercises an 8 ms uninterrupted carrier burst; repeated `00` tests longer bursts. `FF` produces silence, so it cannot be distinguished from idle without an external timing reference or neighboring marked data. Verify silence duration using a bounded pattern such as `raw 55 FF AA`.

Remote-control receiver AGC may suppress long carrier bursts. If the long-zero tests are distorted, characterize the receiver before interpreting unfamiliar packets. Otherwise receiver behavior could be mistaken for new protocol behavior.

### 2. Record an unfiltered baseline

Run the original base and capture a known static or scrolling message. Check that the decoded text and command match the visible display and that there are no loss reports. Save receiver configuration and decoder settings with the session.

### 3. Record the original demo

Start recording before entering demo mode so setup commands are included. Record at least two complete cycles to distinguish repeatable traffic from incidental events. Keep all traffic in the recording, even if the live view hides known commands.

Record video of the display and add markers for distinctive behavior: static text, text in several locations, scroll start/stop, flashing, and transitions. Establish the offset between video time and capture time with a shared identifiable event; do not equate USB arrival time with acquisition time.

Switch the live view to unknown plus partially known. Observe the display around those events and annotate what changed. Expand neighboring known traffic whenever attribution is unclear.

### 4. Analyze and isolate candidate sequences

Compare repeated cycles, identify stable control bytes versus changing text, and inspect uncertain boundaries. Export each candidate with its preceding state-setting packets and original gaps. Write down the proposed interpretation and alternative explanations.

### 5. Replay, then modify

Use the existing transmitter's `raw` command to reproduce individual packets. Disable the original base's data transmission for replay, as in the transmitter integration plan. Reproduce necessary initial state, order, and delays; a raw packet alone may not recreate the effect.

The current transmitter supports up to 256 bytes per packet but **does not schedule multi-packet recordings**. Sequence replay with preserved gaps will require host-side replay support. Do not describe manual terminal entry as timing-accurate sequence replay.

First reproduce the captured effect unchanged. Then vary one opcode, parameter, position, glyph, or effect byte at a time. Keep a record of exact transmitted bytes, timing, initial display state, and observed result. Repeat successful tests and test different prior states to distinguish an absolute command from a state-dependent one.

### 6. Promote confirmed findings

Add recognition rules only to the extent supported by observations. Document command layout, parameter ranges, dependencies, example packets, and unresolved cases. Reanalyze earlier recordings with the updated rule set; previously unfamiliar traffic should become recognized without altering the source recordings.

## Acceptance criteria

The first useful implementation must demonstrate:

1. Known-pattern acquisition with expected polarity, bit order, timing, and long-burst behavior characterized.
2. Continuous capture across DMA boundaries and USB activity, with explicit detection of any loss.
3. Reliable decoding of known messages and honest handling of ambiguous framing.
4. Correct distinction among known, partially known, unknown, and uncertain events.
5. Live filtering that leaves recordings complete and retains access to hidden context.
6. A complete demo recording with behavior annotations and comparisons across repeated cycles.
7. Export of candidate packets/sequences suitable for replay, including timing and state context.
8. At least one previously unresolved behavior reproduced and documented through controlled experiments.

Automated tests should cover decoder timing distortion, consecutive equal bits, byte and DMA boundaries, corrupted/lost blocks, uncertain framing, rule matching, and nondestructive filtering. Physical receiver validation remains necessary because software tests cannot establish a module's optical/AGC behavior.

## Implementation sequence

1. Recorder firmware and versioned CDC transport, with a loss-detecting host logger.
2. Offline decoder and evidence-based recognition rules.
3. Live classifications, filters, markers, and context timeline.
4. Packet/sequence export and timed replay support.
5. Demo experiments and additions to the protocol documentation.

Keep the recorder and existing transmitter as separately buildable firmware targets initially. This avoids changing the working transmitter while the acquisition path is being established.
