# Olympia Infoglobe: public-information survey

Survey updated 2026-10-19. Target: OL3000.2. This records inspected public sources and distinguishes reported measurements, source-code behavior, and photographic observations from measurements of our unit. No physical unit has been inspected.

- [RB5X head/main-board interface](rb5x/head-interface.md): original schematics, flashing-light port bit, driver path and 555 gating.
- [Protocol reference and deeper search](protocol.md): published effect dictionary, surviving captures, source conflicts, and remaining unknowns.
- [Product/color/revision matrix](variants.md): blue, purple, orange, multicolor, retail suffixes, and related products.
- [Source register](sources.md): manuals, historical reverse engineering, repairs, code, related regulatory records, and inaccessible leads.
- [Evidence](evidence/README.md): retained reference photos, historical interface schematic, original URLs, and hashes.

The initial survey omitted significant color and product variants. This update supersedes that incomplete coverage. It is a broad public-information survey, not a claim that every surviving page, video, or hardware revision has been found.

## Target: OL3000.2

The user identified the target as **OL3000.2**. Andrew R. Morris's [Hacking the Infoglobe](https://web.archive.org/web/20110425234300/http://www.linux-hacker.net/InfoGlobe/) explicitly states: “Mine is Model no. OL3000.2.” This is a direct model-specific reverse-engineering source, now inspected.

Morris distinguishes an older version with a **9 V backup battery** and different button labels from his later **three-AAA backup** version. This establishes two reported hardware variants, but does not establish the older version's model number or explain the `.2` naming convention.

Model-specific observations reported by Morris (verify against our PCB before use):

- Rotary-transformer power transfer; no slip rings. Approximately 24 kHz drive, with reported 75 V primary and 25 V secondary pulses. These are historical measurements, not measurements of our unit.
- Separate optical rotation-index and modulated infrared data paths.
- Data carrier 38 kHz; zero = 1 ms carrier burst, one = 1 ms silence; strict 8 ms per byte.
- 35 text characters plus up to three control characters. There are 36 display positions, with one reserved for spacing; he reports that sending 36 text characters blanks the display.
- Commands `00`–`06` and 38 transition effects (`00`–`25` hexadecimal), with detailed framing examples in the source.
- Base data-LED driver **Q107**, series resistor **R116 (100 ohms)**, and base resistor **R117 (4.7 kilohms)**. He describes inhibiting the original transmitter with an optocoupler and adding a separate IR LED, preserving original operation when the added controller is disabled.
- Reported original adapter: 9 V, 300 mA, unregulated. The text alone does not establish connector polarity or all adapter requirements; read the actual adapter label before substitution.
- Original base transmissions occur approximately every 15 seconds. Competing transmissions can corrupt a message; any replacement must handle ownership of the link.

The source cautions that the telephone-line circuitry is not isolated and recommends an isolated interface. Inspect and measure with the phone line disconnected; preserve the dome interlock and keep clear of the spinning rotor. Transformer pulses are much higher than the adapter voltage.

## OL3000-family manual

[Wave Olympia Info Globe OL3000 manual](https://www.manualslib.com/manual/1076904/Wave-Olympia-Info-Globe-Ol3000.html), first edition September 2003, copyright Wave Industries Ltd. Inspected manual text documents 54 caller-ID records, messages up to 30 characters, six programmable alert messages, three AAA backup batteries, and a programmable on/off timer.

The manual's 30-character user-message limit and Morris's 35-character rotor-protocol limit describe different interfaces and need not conflict. The ManualsLib title does not explicitly identify `.2`; the same September 2003 edition is also hosted in an Internet Archive item explicitly titled OL3000.2 (see source register). Its daylight-saving rules use the first Sunday in April and last Sunday in October, so automatic DST should not be assumed correct for current US rules.

## Identification and variants

The available project documentation describes an early-2000s caller-ID display using a rotating LED arm to produce a persistence-of-vision display. It also supports manually entered messages. See [MayNc10's overview](https://github.com/MayNc10/infoglobe/blob/main/README.md).

**Cross-model revision compatibility remains unverified.** Morris explicitly identifies OL3000.2, but a complete mapping between product numbers, enclosure variants, PCB revisions, and protocol differences is still missing. Do not assume a modification applies to every Infoglobe.

For each unit, record separately:

- Complete underside label: model, product/part number, regulatory identifiers, serial/date codes, and electrical ratings.
- Original adapter label: output voltage, AC/DC, current, connector dimensions, and polarity where applicable.
- Enclosure appearance, display color, controls, and external connections.
- Base PCB and rotating PCB silkscreen numbers, revisions, component markings, and clear photographs of both sides.
- Original behavior and captures of base-to-rotor signalling before modifying anything.

Product model numbers, retail SKUs, adapter part numbers, and PCB assembly numbers should remain separate fields until evidence connects them.

## Inspected sources

### Raspberry Pi implementation

[alertjean/led_display](https://github.com/alertjean/led_display), especially [README](https://github.com/alertjean/led_display/blob/main/README.md) and [pi.py](https://github.com/alertjean/led_display/blob/main/pi.py).

The author reports using a wired-network Raspberry Pi Zero, removing most original base logic, retaining the circuitry for wireless power transfer to the rotating board, and driving an infrared LED from GPIO. Software uses pigpio waveforms and includes RSS headlines and an HTTP interface for messages.

Observed in source, not measured on hardware:

- A transmitted zero uses 38 cycles of 13 microseconds high and 13 microseconds low, followed by 13 microseconds low: 1001 microseconds total, approximately 38.46 kHz during the burst.
- A transmitted one is an equally long gap.
- `get_wave` transmits each byte most-significant bit first.
- `get_line_wave` emits `FF FF 04`, character bytes, and four `FF` bytes.
- Text layout uses 36-character chunks. This is implementation behavior, not proof of a universal display limit.

### ESP32 / ESP-IDF implementation

[MayNc10/infoglobe](https://github.com/MayNc10/infoglobe), especially [driver.c](https://github.com/MayNc10/infoglobe/blob/main/main/driver.c).

The README reports an ESP-WROOM development board. The C implementation uses ESP-IDF GPIO, LEDC, GPTimer, and FreeRTOS facilities. Separate Elixir/AtomVM material is also present.

Observed in source:

- Configured infrared carrier: 38 kHz; timer interval: 1 ms; GPIO: 13.
- A zero enables the carrier and a one disables it.
- Command enum values, in declaration order, are Load=0, Disp=1, DispFlash=2, SetScroll=3, DispScroll=4, OverwriteFlash=5, ToggleScroll=6. These names are the author's interpretation.
- Message limit is 35 bytes in this implementation.
- The bit-index macro sends each byte least-significant bit first, unlike the Pi implementation above. Resolve this discrepancy with original protocol documentation and captures before choosing a driver.
- Source includes thread-safety TODOs and unfinished command handling; treat it as reference material rather than validated firmware.

### Arduino / Internet messaging project

[kongmunist/InfoglobeWebsite-public](https://github.com/kongmunist/InfoglobeWebsite-public). The default branch is **public-version**; the earlier main/master archive failures were wrong branch assumptions, not inaccessible source. The correct archive and Arduino sketch were subsequently retrieved. All three hardware/software tutorials and the standalone demo gist were inspected.

The author describes an Internet-connected message queue and points to firmware under `arduinostuff/`. The README explicitly says the repository is archival, the website may not run as-is, and newer Arduino code is on the author's website. Do not deploy the archived web application unchanged.

## Additional sources

The following sources were inspected, with detailed coverage in the source register:

- [Andy Kong tutorial, hardware part 1](https://andykong.org/blog/infoglobetutorial1/)
- [Hardware part 2](https://andykong.org/blog/infoglobetutorial2/)
- [Software part 3](https://andykong.org/blog/infoglobetutorial3/)
- [Olympia Infoglobe Goes Back Online](https://hackaday.io/project/186497-olympia-infoglobe-goes-back-online)
- [Archived linux-hacker.net InfoGlobe documentation](https://web.archive.org/web/20110425234300/http://www.linux-hacker.net/InfoGlobe/)

Obtain original manuals and label photographs for each candidate product number. Prefer label/manual evidence to marketplace titles. Regulatory identifiers, if present, can help locate filings and internal photographs but must first be read from an actual label.

## Modification direction

The strongest common direction in the inspected projects is to retain the rotating display and its wireless power supply, then replace or intercept the base-to-rotor infrared command stream. This potentially avoids replacing the rotor controller. It does not establish compatibility with an unidentified revision.

Before soldering or selecting an adapter, identify the unit, preserve its original wiring and behavior, measure the supply and signal levels, and capture the infrared link. In particular, resolve bit order, framing, command meanings, character encoding, and message-length limits. Morris supplies model-specific ratings and component references above; these remain to be checked against the actual unit.

## Protocol baseline and conflicts

For the documented monochrome OL3000.2, the strongest agreement is **38 kHz carrier; burst = zero; silence = one; 1 ms bit cells; MSB first**. Stefano Bodini explicitly states MSB-first in HAnix part 3; Pi code, Andy Kong's demo, greenmikey's working ESP8266 code, and monkeyboyfr3sh's ESP-IDF transmitter implement MSB-first. The MayNc10 LSB-first code is therefore an outlier requiring investigation, rather than evidence for two equally established encodings.

Historical command summary below follows Morris. His later flashing-message discussion conflicts with his short command list about `02` and `05`; those two commands need direct capture/testing before their precise payloads can be considered settled.

| First byte (hex) | Reported behavior |
| --- | --- |
| `00` | Buffer/load for transitions; `00 00 TEXT EFFECT` enables an effect |
| `01` | Immediate non-scrolling message |
| `02` | Flashing operation; detailed semantics conflict within source |
| `03` | New message inherits previous scrolling state |
| `04` | Immediate scrolling message |
| `05` | Flashing/overwrite operation; detailed semantics conflict within source |
| `06` | Toggle scrolling of existing message |

Reported framing and characters:

- No UART-style per-byte start/stop bits are described. Packet begins with a control byte. `FF` is all silence and can delimit back-to-back packets; a quiet interval also ends a packet.
- Without effects: command followed by text. With effects: two zero bytes, text, effect byte. Claimed effects `00`–`25` hexadecimal (38 choices), repeated at `80`–`A5`; setting effect bit 6 reportedly blanks the display.
- 35 text bytes at the rotor interface; 30 user-entered characters through the original UI. Pi code's 36-character processing is not proof that the rotor accepts 36 text bytes.
- ASCII-like character set; unsupported symbols reported as `% & + ; @ [ \ ] ^ _` plus backtick and `{ | } ~`. Low codes `01`–`1A` reportedly contain accented/foreign characters; `80`/`81` are envelope-icon halves. A complete glyph dump has not been located.
- Flashing text has special space handling (`00` instead of `20`) according to Morris. Do not treat the whole payload as a normal NUL-terminated C string.
- There are no established color commands in the monochrome sources. No claim of checksum, ACK, error correction, or rotor firmware update support is made.

## Hardware architecture and reference circuits

Morris describes three mostly independent paths: motor drive, rotary-transformer power transfer, and optical signalling. The outer continuously lit IR index source provides a once-per-revolution reference; the inner modulated data LED illuminates a cavity under the rotor. Do not mistake index and data LEDs for each other.

His model-specific report gives a 5.6 V motor supply and a 10 V regulator feeding the rotary-transformer circuit. The primary is MOSFET-switched at approximately 24 kHz. Reported 75 V primary / 25 V secondary pulses and the guessed 5 V rotor rail are historical observations/estimates, not universal ratings. Verify the actual rotor regulator before choosing parts.

Motor regulation follow-up (2026-10-19): Morris explicitly states, “There is no speed regulation,” and describes the motor as brushless DC, supplied by regulated 5.6 V. His following explanation that the rotor measures index-pulse intervals is explicitly his inference (“I’m sure”), not a firmware disassembly or measured speed-sweep result. Andy Kong independently reports approximately 5.6 V on the motor supply with the rotor running, versus approximately 6–6.3 V with the safety switch off, and shows oscilloscope observations of startup dips and running noise. Together these support a replacement regulated motor-voltage supply without an added tachometer feedback loop. No actual RPM measurement or experimentally established compensation range was located in this follow-up; searches were partly limited by irrelevant search results and search-engine challenges.

Sources: [Morris teardown](https://web.archive.org/web/20110425234300/http://www.linux-hacker.net/InfoGlobe/), [Kong hardware integration](https://andykong.org/blog/infoglobetutorial2/).


Wilke Application Note 071 independently photographs **eight SMD LEDs on one vertical end board**, with an unpopulated board at the other end apparently serving as a counterbalance. Bodini also reports eight blue LEDs. This is stronger physical evidence than the LED Museum review's estimate of “at least 10” or its statement that both ends carry LEDs. Do not propagate the latter as an established LED count.

The two spring contacts visible after removing the rotor connect components that rotate together; they do not contradict wireless power transfer across the stationary/rotating boundary.

[Morris's schematic](evidence/morris-image003.jpg) is an **add-on controller/interface**, using a PIC16LF84, regulator, transistor drive, and an optocoupler path. It is not a factory base or rotor schematic. His [base photograph](evidence/morris-image005.jpg) identifies the modified region. No complete factory schematic, base firmware dump, rotor firmware dump, or complete semiconductor BOM has been located in the inspected sources.

## Public modification approaches

| Approach | Source | Tradeoff for this project |
| --- | --- | --- |
| Added IR LED + optoisolated suppression of Q107 | Morris | Can restore base transmissions; requires a second optical emitter and arbitration |
| Reuse original IR driver by removing R117 and routing both sides to an interface | HAnix parts 2–5 | Retains base and offers pass-through; published work includes circuit and MSP430 prototype details |
| Cut/reroute original data LED to ESP8266 | Andy Kong tutorials | Simpler message replacement, but original caller-ID/clock messages no longer reach rotor |
| Replace most base logic, retain wireless power circuit, drive new IR LED from Pi | alertjean | Larger change; Linux handles RSS/HTTP with pigpio timing |
| Electrically emulate five buttons with isolated relay contacts | Wilke Application Note 071 | Uses original firmware and message slots; slow character selection and UI-state dependence; no need to decode rotor protocol |

Wilke reports that buttons are dynamically scanned in a matrix, so directly assuming ground-referenced GPIO button inputs is inappropriate. The German-language unit has an OK button and a language menu; it is not evidence that its menu ordering matches the US specimen.

Andy Kong's integration tutorial observes startup dips and motor-supply noise, and uses filtering plus a protection diode. Do not copy its 5.6–6.3 V feed into an arbitrary ESP board without checking that board's input regulator and supply limits. This is a historical integration example, not a universal wiring prescription.

## Firmware references and limitations

In addition to the Pi and MayNc10 projects above:

- **Andy Kong demo gist:** Arduino + IRremoteESP8266; manually tuned `gapTime=988`; GPIO4/D2; scrolling and transition helper; MSB-first. The comments sometimes call emitted light a “1,” while the code emits it for a zero. The call `snprintf(infoglobeMsg, 35, customMsg.c_str())` treats user text as a format string and has room for only 34 characters plus NUL. Reuse protocol knowledge rather than copying it unchanged.
- **IRremoteESP8266 issue 465 (2018):** explains why toggling a GPIO after `enableIROut()` does not create the required carrier on ESP8266. The author's mark/space implementation accumulates timing error; deadline-based compensation produces reported working output. The maintainer notes timer wrap and capture/demodulator delays. Its initial `sendGeneric` suggestion is explicitly untested and reverses the mark/space polarity relative to the stated Infoglobe protocol; do not copy that example as a specification.
- **DavidBerdik's ESP8266 Arduino-core fork:** README says it is based on release **3.0.2** because later releases had serious IR timing issues for that project. This is an author-reported compatibility constraint, not independently benchmarked here. It is a board-core fork, not a complete Infoglobe controller application.
- **monkeyboyfr3sh/InfoGlobeHack:** inspected application sources implement ESP-IDF LEDC + esp_timer transmission, MSB-first, configured carrier **38540 Hz**, timer period **1000 microseconds** despite a misleading `BIT_PERIOD_MS` name. Includes TCP, OTA, SNTP, display/animation handling, and Python UI modules. Per-bit `printf` calls in the timer callback deserve timing review. No build or hardware validation performed here.
- **Kong website repository:** source retrieval succeeded on `public-version`; archival warning remains relevant. Historical external APIs and embedded network assumptions need review before reuse.

## Repairs and diagnostic evidence

HAnix's 2011 repair documents progressive loss of display rows, visible deposits around the LEDs, and recovery after gentle cleaning. Its comments include solder reflow repairs, complete display loss, shaky text, changing colors, power-supply problems, and EEPROM-like failures. These reports suggest diagnostic branches; they do not prove that dust explains every missing row.

The iFixit thread documents both successful and unsuccessful power/battery removal resets, including an EEPROM error. One contributor says screws are hidden under feet, whereas Morris explicitly says none are. Treat disassembly details as revision-specific or unverified, not interchangeable instructions.

Preserve original settings before any memory-clear procedure. A motor that spins does not establish that the rotor supply, index path, or IR data path works. Conversely, a dead original base does not prove that the rotor is unusable.

## Questions public sources have not settled

1. Full factory color/SKU/PCB revision mapping, especially orange and MC labels.
2. Color-selection commands and payload layout for MC hardware; simultaneous color capability.
3. Remaining transition-effect descriptions, flashing-packet semantics, and full glyph table. A partial effect dictionary was recovered from gist comments; see protocol.md.
4. Factory component part numbers, firmware/dumps, programming interfaces, and complete schematics.
5. Electrical limits and precise timing tolerances across revisions. Andy Kong's approximately 3 microsecond tolerance is his experience with his implementation, not a guaranteed device rating.
6. Exact patent family. Labels say patent pending; the targeted search did not establish a matching patent, so unrelated persistence-of-vision patents are not attributed to this product.

## Suggested first investigation, after identifying the physical unit

Photograph labels, adapter, controls, base PCB, rotor PCB, and LED population. Record original behavior and supply rails. Passively capture the original data stream while changing one setting at a time: short text, long text, static/scroll, transition, and each color if available. Correlate electrical polarity with decoded MSB-first bytes. Preserve these captures before cutting traces or removing parts. The resulting unit record should decide which published modification applies.

## Search scope and access

Searched product colors, suffixes LB/LP/MC, older backup-battery reports, Plus/wireless models, manuals, repairs, patent leads, IR timing/protocol, Arduino, MSP430, Raspberry Pi, ESP8266, ESP32, and GitHub repositories. Inspected the GitHub repository search's two result pages for `infoglobe`, rejecting unrelated country/news/statistics projects. Followed links from primary technical sources and relevant comment threads.

DuckDuckGo returned usable results for many simple queries and challenges for some others. Google returned interstitials; Bing returned unrelated results and was not used as evidence. YouTube pages were proxy-blocked: video titles are discovery leads, not watched/verified evidence. Andy Kong's pages became readable with a normal User-Agent; all three tutorials were then inspected. FCC filing index was readable but its linked manual PDF returned 403. These are per-request observations, not a claim that the entire network is blocked.

No full factory catalog or exhaustive public archive has been obtained. All named gaps remain explicit rather than being filled by guessed part numbers or inferred compatibility.
