# Rotor protocol: published knowledge and remaining gaps

Updated 2026-10-19 after a second, protocol-focused search. Scope: the published monochrome OL3000.2 interface. These are literature/code findings, not measurements of our unit. Multicolor compatibility is not established.

## What we can reuse

There is enough existing work to avoid rediscovering the basic transport, normal text framing, transition framing, and many transition meanings. Start with Morris's protocol account, Bodini's explicit MSB-first description, Kong's standalone demo, and greenmikey's timing investigation. Compare against captures from the target rather than treating any one implementation as a complete specification.

The important additions from deeper review are **a partial transition dictionary in gist comments, five surviving labeled timing captures on Pastebin, a separately identified original-base capture, and specific implementation inconsistencies**.

## Transport and ordinary packets

| Property | Published baseline | Evidence |
| --- | --- | --- |
| Carrier | Approximately 38 kHz infrared | Morris, HAnix, multiple implementations |
| Bit cell | Nominal 1000 microseconds | Same sources; do not copy a software compensation constant as device timing |
| Logical zero | Carrier emitted throughout bit cell | Same sources |
| Logical one | No carrier throughout bit cell | Same sources |
| Byte order | Most-significant bit first | Explicit HAnix statement; Kong, Pi and working ESP8266 implementation |
| Rate | 1000 bits/s, nominal 8 ms/byte | Derived from bit cells, not a UART configuration |
| Normal text | One command byte followed by character bytes | Morris and modern implementations |
| Transition text | `00 00`, text bytes, effect byte | Morris; working Kong code; independent author report in issue 465 |
| End/separation | Silence; `FF` represents eight silent bit cells | Morris; exact receiver timeout not independently measured |
| Text capacity | Reported 35 rotor text bytes; 30 through original user interface | Distinct interfaces; do not conflate limits |

Example bytes, **derived from the published format, not captured from our hardware**:

```text
Scroll HI:                  04 48 49
Stationary HI:              01 48 49
HI with decimal effect 12:  00 00 48 49 0C
Toggle existing scrolling:  06
```

Do not insert arbitrary delays between bytes. Runs of zeros are consecutive carrier cells; runs of ones are consecutive silence cells. There is no published requirement for a new pulse edge at every bit boundary. This distinction matters for decoding demodulator traces.

No verified checksum, per-byte UART start/stop framing, acknowledgement, or firmware-upload mechanism has been found. That is a statement about available evidence, not proof that undocumented modes do not exist.

## Commands and flashing uncertainty

Morris lists commands `00` through `06`: transition buffering, immediate display, flashing, inherited scroll state, immediate scrolling, flashing overwrite, and scroll toggle. His short list and later detailed flashing section disagree about the descriptions of `02` and `05`.

The detailed section supplies two candidate forms worth preserving rather than reinventing:

```text
02 POSITION FLASHING_TEXT
05 TEXT START_POSITION END_POSITION MESSAGE_LENGTH
```

These are transcriptions of the later prose, **not resolved/validated command definitions**. The source also discusses a first normal packet followed by a flashing overlay packet, waiting for transitions to finish before sending the overlay, 36-position wraparound, and using `00` for a blank within flashing text instead of ordinary ASCII space `20`. Its position examples contain an apparent repeated `01` typo. Do not silently repair that into a claimed specification.

Kong's archived website sketch has commented-out experiments labeled scrolling flashing `02` and flashing `05`, but they are not an independent, working implementation of either complete form. Modern source does not remove the need to resolve these few details on hardware.

## Transition dictionary already published

The [2022-11-28 gist comment by Andy Kong](https://gist.github.com/kongmunist/a8bdadbacda4bcb129cd183f2f0fffc5#gistcomment-4383041) describes effects. David Berdik adds [effect 20](https://gist.github.com/kongmunist/a8bdadbacda4bcb129cd183f2f0fffc5#gistcomment-4383077) and [effect 27](https://gist.github.com/kongmunist/a8bdadbacda4bcb129cd183f2f0fffc5#gistcomment-4383080).

**The comments use decimal IDs.** Morris uses hexadecimal `00`–`25`, which is the same 0–37 range. CW/CCW labels are the authors' observations; viewpoint was not formally defined.

| Decimal | Hex | Published description, paraphrased |
| --- | --- | --- |
| 0 | 00 | Incoming text flies counterclockwise, erasing previous text |
| 1 | 01 | Same, clockwise |
| 2 | 02 | Incoming text arrives in two halves like pincers |
| 3 | 03 | Pixels fade out and back in |
| 4 | 04 | Clockwise version of effect 5 |
| 5 | 05 | Counterclockwise erase/reveal sweep over stationary old text |
| 6 | 06 | Not described in the inspected comments |
| 7 | 07 | Old text flies counterclockwise, revealing stationary new text |
| 8 | 08 | Row-wise grow-down/grow-up |
| 9 | 09 | Horizontal shrink to center, then expansion |
| 10 | 0A | Alternating-line horizontal fill from top |
| 11 | 0B | Each letter phases out from horizontal center, new letter phases in from outside |
| 12 | 0C | Replace letters one at a time around the circle, counterclockwise |
| 13 | 0D | Effect 12, clockwise |
| 14 | 0E | Replace alternate letters around the circle, counterclockwise |
| 15 | 0F | Effect 14, clockwise |
| 16 | 10 | Old text moves down; new text moves up |
| 17 | 11 | Old text moves up; new text moves down |
| 18 | 12 | Letters replaced together, incoming letters from above |
| 19 | 13 | Corresponding replacement from below |
| 20 | 14 | Counterclockwise version of effect 21; Berdik's addition |
| 21 | 15 | Erase in a loop, then place back |
| 22 | 16 | Not described |
| 23 | 17 | Not described |
| 24 | 18 | Flies up from below, bounces/mirrors off top |
| 25 | 19 | Corresponding effect from above |
| 26 | 1A | Drop and replace from left to right |
| 27 | 1B | Effect 26, right to left; Berdik's addition |
| 28 | 1C | Drop and replace in random order |
| 29 | 1D | Not described |
| 30 | 1E | Pluck and replace from left to right |
| 31 | 1F | Not described |
| 32 | 20 | Not described |
| 33 | 21 | Pluck and replace in random order |
| 34 | 22 | Letter-by-letter fade from right |
| 35–37 | 23–25 | Variations of effect 34; individual distinctions not documented |

An effect-byte value and a first-byte command with the same numeric value have different meanings. In particular, effect 6 is not established by command `06`'s scroll-toggle behavior.

Morris reports aliases `80`–`A5` and blanking when effect bit 6 is set. No independent full sweep or trace set was located to verify all aliases.

## Existing captures: useful, but noisy

The author of [IRremoteESP8266 issue 465](https://github.com/crankyoldgit/IRremoteESP8266/issues/465) supplied [a Pastebin](https://pastebin.com/k7YiFnD9), still retrievable with a normal User-Agent during this review. The [2018-05-25 issue comment](https://github.com/crankyoldgit/IRremoteESP8266/issues/465#issuecomment-392227107) explicitly says the Pastebin came from the author's **custom ESP8266 implementation**, then adds a capture from the **original base**.

| Text | Claimed mode | Origin | Raw duration entries |
| --- | --- | --- | --- |
| `192.168.1.142` | Scrolling `04` | Custom transmitter | 64 |
| `Test` | Static `01` | Custom transmitter | 30 |
| `IRremoteESP8266` | Scrolling `04` | Custom transmitter | 110 |
| `A man a plan a canal Panama` | Scrolling `04` | Custom transmitter | 145 |
| `Olympia Infoglobe` | Static `01` | Custom transmitter | 96 |
| `CID LIST` | Static `01` | Original base, per author | 63 |

Retained [exact Pastebin text](protocol-evidence/greenmikey-2018-captures.txt) and [machine-readable durations/provenance](protocol-evidence/captures.json). All six array lengths match their declared counts. This is a data-integrity check, **not successful protocol decoding or validation of replay**.

The maintainer specifically questions 12–14 microsecond pulses and possible carrier mismatch/receiver saturation. The author later reports failing to obtain clean results. These traces must not become unquestioned golden tests. Their `UNKNOWN` hash values and detected bit counts are generic IR library output, not device command IDs or message lengths.

## Existing code and mistakes to avoid repeating

- [greenmikey's working deadline-based transmitter](https://github.com/crankyoldgit/IRremoteESP8266/issues/465#issuecomment-390790067) addresses drift by subtracting time already spent from the next bit's deadline. There is no need to rediscover that particular software-timing failure. A new implementation still needs correct handling of missed deadlines and timer wrap.
- The maintainer's earlier `sendGeneric` suggestion is explicitly untested and assigns carrier/silence to the opposite bit values. The working mark/space implementation uses zero = carrier. Inspect code rather than treating every reply as an authoritative recipe.
- Kong's [standalone demo revision 48f09ab1e5b818e08bd16b61469160455a590202](https://gist.github.com/kongmunist/a8bdadbacda4bcb129cd183f2f0fffc5/48f09ab1e5b818e08bd16b61469160455a590202) emits `04` for ordinary scrolling. The older [website sketch at commit 000871daa9fde37f66d4aee28f3085b019a8a3f8](https://github.com/kongmunist/InfoglobeWebsite-public/blob/000871daa9fde37f66d4aee28f3085b019a8a3f8/arduinostuff/infoglobetry5/infoglobetry5.ino) comments that it emits `04` but actually calls `bitRead(5, 7-i)`. That inconsistency is not proof that `05` is a second normal-scroll command.
- MayNc10's LSB-first bit indexing remains an outlier against explicit MSB-first documentation and multiple other implementations.
- The reported working Pi implementation's 36-character handling conflicts with Morris's rotor limit of 35 text bytes. Do not use host string chunk size as a hardware specification.
- The DavidBerdik core fork reports timing compatibility with ESP8266 Arduino core 3.0.2. Modern ESP-IDF projects use hardware PWM and a bit scheduler; neither library choice removes the need to measure actual output timing.

## Deep-search coverage and negative results

This pass followed primary-source links and comments rather than only repeating general web searches:

1. Targeted web searches for both “Infoglobe” and “Info Globe,” protocol/IR, flashing, ASM/Morris, MCU/controller, firmware, and multicolor/OL3000MC. Simple and quoted queries returned different results; some returned challenges or irrelevant namesakes.
2. GitHub repository search from the previous survey, then API code searches by language, ASM filename, OL3000MC, rotor, transitions, flashing, color, and OL3000. Many hits are unrelated namesakes; code indexing also misses known relevant repos, so a zero result is not proof of absence.
3. GitHub issue/PR searches: the only relevant returned issue was 465. The four relevant application repositories checked returned no forks. GitHub Gist search returned one relevant gist; all four comments were retrieved through the API.
4. All 15 issue-465 comments retrieved through the API, including the late capture posts and the final unsuccessful attempt to clean up reception. Followed its surviving Pastebin.
5. Wayback exact-URL search for Morris's ASM and a fetch of its indexed 2025 response. It is a tiny HTML redirect to `/lander`, **not assembly source**. Live URL returned 503; broader CDX requests failed/timed out. Authentic PIC assembly has not been recovered.
6. Rechecked existing application code beyond the transport routine, finding the archived sketch's command/comment mismatch and partial flashing experiments.
7. Visually inspected Wilke app note page 3: an eight-LED board and a packaged multi-pin rotor IC are visible, but markings are not readable. **Rotor-controller part number remains unidentified.**

No reliable published MC color-byte map, clean factory capture corpus, complete glyph/transition specification, or identified rotor firmware was located in this pass. These are bounded search results, not a claim that no such information exists anywhere.

## Where new investigation is justified

Reuse the documented transport, ordinary-message framing, known transition descriptions, and timing lessons. New capture work should focus on **the target revision's compatibility, `02`/`05` flashing fields, undocumented effects/glyphs, precise packet termination, and MC color selection if applicable**. Capture the original base before modifying it. There is no reason to reverse-engineer basic ASCII scrolling again.
