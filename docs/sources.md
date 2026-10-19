# Public-source register

Access/review date: **2026-10-19**. This register distinguishes inspected evidence from discovery leads. “Inspected code” means read, not built or tested on a globe. “Photographs inspected” means visually reviewed images, not just seller alt text or catalog fields. Archived dates and publication dates are not manufacturing dates.

## Product documentation and contemporary review

| ID | Source | Review and relevance |
| --- | --- | --- |
| M1 | [OL3000.2 manual, Internet Archive item](https://archive.org/details/OlympiaInfoGlobeOl3000.2Manual), [full OCR](https://archive.org/stream/OlympiaInfoGlobeOl3000.2Manual/OlympiaInfoGlobeOl3000.2Manual_djvu.txt) | OCR inspected. September 2003 edition; 30-character user messages, six slots, 54 caller-ID records, three AAA batteries, timer and old US DST rules. Item metadata is user supplied; typography/identifiers should be checked against scan images if exact transcription matters. |
| M2 | [Wave Olympia OL3000 manual](https://www.manualslib.com/manual/1076904/Wave-Olympia-Info-Globe-Ol3000.html) | Manual text inspected. Same September 2003 edition; useful independent hosting, not an independent hardware revision. |
| M3 | [Olympia Info Globe owner's manual](https://www.manualslib.com/manual/1234974/Olympia-Info-Globe.html), [features page](https://www.manualslib.com/manual/1234974/Olympia-Info-Globe.html?page=2#manual) | Text inspected. Again 54 records and AAA backup. Different host page count does not establish a distinct model. |
| M4 | [LED Museum hands-on review](https://www.ledmuseum.candlepower.us/fifteen/olympia.htm) | Full text inspected; purchase dated 2004-05-19, last update 2010-10-16. Describes blue LEDs and blue dome, 9 V DC 300 mA adapter, three AAA backup, message retention and DST behavior. Includes spectrographic analysis image and videos. LED-count/rotor-end description conflicts with stronger teardown evidence; no precise spectral peak transcribed here. |

## Historical engineering and repairs

| ID | Source | Review and relevance |
| --- | --- | --- |
| H1 | Andrew R. Morris, [Hacking the Infoglobe](https://web.archive.org/web/20110425234300/http://www.linux-hacker.net/InfoGlobe/) | Full article inspected. Explicitly OL3000.2, distinguishes older 9 V backup version, describes power/motor/index/data, commands, transitions, glyph exceptions, injection and arbitration. Its flashing-command descriptions contain inconsistencies. |
| H2 | [Morris archived figure 1](https://web.archive.org/web/20110724203544im_/http://www.linux-hacker.net/InfoGlobe/Hacking%20the%20Infoglobe-1_files/image003.jpg) | Schematic visually inspected and retained. Add-on PIC16LF84 message generator and interface, not factory circuit. Companion product/base images also retrieved. See evidence manifest. |
| H3 | Stefano Bodini / TheFwGuy, [Hacking an Infoglobe, part 1](https://hanixdiy.blogspot.com/2010/10/hacking-infoglobe-part-1.html) | Full article text inspected via search/label page. Disassembly and MSP430 project context. |
| H4 | [Part 2](https://hanixdiy.blogspot.com/2010/10/hacking-infoglobe-part-2.html) | Text and image links inspected via series page. Reuses original IR driver; removes R117, routes base and transistor signals, adds power and connector. Includes an actual report of pad damage during resistor removal. |
| H5 | [Part 3](https://hanixdiy.blogspot.com/2010/10/hacking-infoglobe-part-3.html) | Full text/code inspected. Explicit MSB-first encoding, protocol summary, MSP430 carrier/timer prototype. Much of protocol repeats Morris and is not an independent measurement of every command. |
| H6 | [Part 4](https://hanixdiy.blogspot.com/2010/10/hacking-infoglobe-part-4.html) | Full text inspected. MSP430F2012, message state machine, serial input, suppression and diode mixing, optoisolated PC connection. States full firmware was available by request; public completeness not established. |
| H7 | [Part 5](https://hanixdiy.blogspot.com/2010/10/hacking-infoglobe-part-5.html) | Full text inspected. Permanent prototype, point-to-point wiring, connector layout and temperature-sensor feature. |
| H8 | [Apache log messages on the Infoglobe](https://hanixdiy.blogspot.com/2011/03/apache-log-messages-on-infoglobe.html) | Text inspected. Demonstrates external PC-originated information through the interface; historical integration example. |
| H9 | [Fixing an Infoglobe](https://hanixdiy.blogspot.com/2011/08/fixing-infoglobe.html) | Main article and returned comments inspected. Eight blue LEDs, progressive missing rows and cleaning repair. Comments document three-color hardware, orange versus blue, Infoglobe Plus, solder repairs, power and data failures, and aftermarket LED replacement. Comment claims have lower confidence than photos/measurements. |
| H10 | Gunther Zielosko, Wilke BASIC-Tiger Application Note 071 rev. 1.0, [Die magische Kugel – InfoGlobe von Olympia](https://wilke.de/fileadmin/templates/Bilder/success/pdf_komplett/Applikationsbericht_071_WilkeTechnology.pdf) | All ten pages' extracted German text inspected. Photos identify an eight-LED end board and unpopulated counterpart; five-button matrix automation via relays, add-on circuit, power pickup, 30-character/six-slot programming. Refers to GLOBE01.TIG, GLOBE02.TIG and GLOBE02.TST; their availability was not verified. Local temporary PDF SHA-256 can be regenerated from URL; not a factory service manual. |
| H11 | [Arduino forum: Hacking the Info Globe](https://forum.arduino.cc/t/hacking-the-info-globe/73719) | All returned posts inspected. 2011 reports of partial success, code/timing problems, damage after wrong adapter polarity; links to Wilke app note and historical PIC code. Partial-success sketch is not a validated implementation. |
| H12 | [iFixit display-failure discussion](https://www.ifixit.com/Answers/View/43403/How+do+I+get+a+display+on+my+olympia+infoglobe) | Four returned answers/comments inspected. Reset successes/failures, EEPROM error, switches/solder/deposits. Contradictory screw-location advice retained as unresolved. |

## Modern firmware, projects, and timing discussions

| ID | Source | Review and relevance |
| --- | --- | --- |
| C1 | [alertjean/led_display](https://github.com/alertjean/led_display), [pi.py](https://github.com/alertjean/led_display/blob/main/pi.py) | README and transmitter code inspected, archive retrieved. Raspberry Pi Zero + pigpio, RSS/HTTP; 38.46 kHz-ish bursts, 1001 microsecond cells, MSB-first. |
| C2 | [MayNc10/infoglobe](https://github.com/MayNc10/infoglobe), [driver.c](https://github.com/MayNc10/infoglobe/blob/main/main/driver.c) | README, C transmitter inspected; archive retrieved. ESP-IDF LEDC + GPTimer, 38 kHz, 1 ms, LSB-first outlier. Elixir/AtomVM subtree discovered, not comprehensively reviewed. |
| C3 | Andy Kong, [project overview](https://andykong.org/projects/infoglobe/) | Full page text inspected. 2018 attempt, 2022 working project; original base-to-rotor link replaced by ESP8266. |
| C4 | [Tutorial 1: hardware prototyping](https://andykong.org/blog/infoglobetutorial1/) | Full text inspected, dated 2022-10-01. Dome, rotor, IR LED identification, resistor and controller connection. Instructions that bypass the dome switch are historical source material, not our recommended operating procedure. |
| C5 | [Tutorial 2: integration](https://andykong.org/blog/infoglobetutorial2/) | Full text inspected, dated 2022-10-15. Motor-line noise/startup behavior, diode/filtering, battery-compartment installation. Values apply to the author's build, not every ESP board. |
| C6 | [Tutorial 3: software](https://andykong.org/blog/infoglobetutorial3/), [demo gist](https://gist.github.com/kongmunist/a8bdadbacda4bcb129cd183f2f0fffc5) | Text and linked Arduino demo inspected. Gist raw revision **48f09ab1e5b818e08bd16b61469160455a590202**. Manual timing tuning, MSB-first, transition framing. Bugs/limitations noted in research.md. |
| C7 | [kongmunist/InfoglobeWebsite-public](https://github.com/kongmunist/InfoglobeWebsite-public/tree/public-version) | Correct branch `public-version` archive retrieved; Arduino sketch inspected. README says archival as of 2025-02-11, website may not run as-is, newer code elsewhere. Initial main/master 404s were resolved by inspecting the actual default branch. |
| C8 | [monkeyboyfr3sh/InfoGlobeHack](https://github.com/monkeyboyfr3sh/InfoGlobeHack), [IR task](https://github.com/monkeyboyfr3sh/InfoGlobeHack/blob/main/hello_world/main/src/ir_led_task.c) | Archive and application file inventory retrieved; transmitter inspected. ESP-IDF, LEDC/esp_timer, TCP/OTA/SNTP application and Python GUI modules. Third-party bundled libssh2 was not reviewed as Infoglobe-specific work. |
| C9 | [IRremoteESP8266 issue 465](https://github.com/crankyoldgit/IRremoteESP8266/issues/465) | Long technical thread inspected. Actual failed timings, carrier-generation diagnosis, working deadline-compensated implementation, cautions about overflow and measurement. Untested suggested code has polarity inconsistency. |
| C10 | [IRremoteESP8266 discussion 1895](https://github.com/crankyoldgit/IRremoteESP8266/discussions/1895) | Returned discussion text/code inspected. Hardware integration, original functionality bypass, local webserver/time/weather and timing issues; prompted Kong's tutorials. Some GitHub UI elements fail to load, so not evidence that every nested reply was retrieved. |
| C11 | [DavidBerdik/InfoGlobe-Controller-ESP8266-Library](https://github.com/DavidBerdik/InfoGlobe-Controller-ESP8266-Library) | README and repository identity inspected. Arduino ESP8266 core based on 3.0.2, author reports later core timing issues. Not a complete controller firmware. |
| C12 | [Olympia Infoglobe Goes Back Online](https://hackaday.io/project/186497-olympia-infoglobe-goes-back-online) | Full main-page text inspected. Same Andy Kong project, not independent confirmation of every hardware claim. |

GitHub repositories were inspected without running third-party code. Existing repository licenses must be checked before incorporating code. Links without commit IDs track moving branches; no claim that a future version matches the reviewed snapshot is made.

## Physical appearance, packaging, and labels

| ID | Listing / source | Specific evidence inspected |
| --- | --- | --- |
| P1 | [287604928947](https://www.ebay.com/itm/287604928947) | Factory blue-product box marked OL3000LB, barcode 850138000379, copyright 2003. Six gallery photos inspected. |
| P2 | [206510295821](https://www.ebay.com/itm/206510295821) | OL3000LP purple-product box, powered purple unit, OL3000.2 underside model, adapter MB132-090030. Twelve gallery photos inspected. Adapter shows DC 9 V 300 mA, center-positive symbol; a seller-associated accessory is not proof it was original. |
| P3 | [860045249168](https://www.ebay.com/itm/860045249168) | Purple dome and clearly readable OL3000.2 model/registration label. No powered display. Six unit photos inspected plus seller logo. |
| P4 | [257326223130](https://www.ebay.com/itm/257326223130) | Orange dome and warm text. Three unit photos inspected plus seller branding. No readable model-label photo in inspected set. |
| P5 | [168641682196](https://www.ebay.com/itm/168641682196) | Factory MC packaging explicitly says OL3000MC and Messages in Multi Colors; copyright 2005. Six gallery photos inspected. |
| P6 | [257624473526](https://www.ebay.com/itm/257624473526) | MC box and actual red, green, blue display states. Six product photos inspected plus seller branding. Generic listing item fields are misleading. |
| P7 | [376853965202](https://www.ebay.co.uk/itm/376853965202) | Title says purple, operating photos look blue. Five product photos inspected plus seller branding. Example of unreliable seller color classification. |
| P8 | [254362927202](https://www.ebay.com/itm/254362927202) | Page inspected, OL3020 Plus replacement dome/cordless-phone family reference. Dome photographs were discovered but not separately visually reviewed. |

Retained reference images and their original direct-image URLs are in [evidence/manifest.json](evidence/manifest.json). Retail listings can disappear; they establish observations about pictured specimens, not specifications for an entire production run. Asking prices, seller stock numbers, catalog category defaults, and “rare” claims are not engineering evidence.

## Related wireless products and regulatory records

| ID | Source | Status |
| --- | --- | --- |
| R1 | [OL3022 manual text](https://manualzz.com/doc/63015679/olympia-ol3022-infoglobe-owner%E2%80%99s-manual) | Manual transcription inspected; header first edition June 2005, copyright 2004. Wireless pairing/base-cradle description. Keep separate from standalone OL3000.2. AI-generated summary ignored in favor of manual body. |
| R2 | [OL3021 / OL3022 manual listing](https://www.manualslib.com/manual/3279612/Olympia-Ol3021.html) and [OL3022 listing](https://www.manualslib.com/manual/2649438/Olympia-Ol3022.html) | Search titles and pages retrieved; manual content not successfully extracted from those pages. Additional locating references, not fully reviewed manuals. |
| R3 | [RAQOL5800H exhibit index](https://fccid.io/RAQOL5800H) | Index inspected; Giant Telecom, 2003–2005 applications, handset/wireless-display descriptions, internal/external photos and manuals listed; schematics/block diagrams marked metadata-only. It is not the OL3000.2 Part 68 registration. |
| R4 | [Combined OL3021/OL3022 manual PDF](https://fccid.io/RAQOL5800H/User-Manual/User-Manual-495852.pdf) | Search result identifies title; direct PDF returned 403. Not inspected. Do not assume the index's other internal photos depict our target. |

## Historical coverage and uninspected video leads

- [Make: HOW TO – Hacking the Infoglobe](https://makezine.com/article/technology/how-to-hacking-the-infogl/), Phillip Torrone, 2006-11-05: inspected; points back to Morris, adds no independent protocol data.
- [Hackster: Olympia Info Globe Displays Internet Time](https://www.hackster.io/news/olympia-info-globe-displays-internet-time-dc249b3082ac), Jeremy Cook: inspected; summarizes Kong and mentions a prior 2018 demo. Claims about voice-message recording are not corroborated by the standalone OL3000 manual, which describes a message-waiting indication; do not adopt the voicemail-recorder claim.
- [Multicolor demonstration, I6PT1_avkN4](https://www.youtube.com/watch?v=I6PT1_avkN4): title discovered; video page proxy-blocked, **not watched**.
- [Purple unit/opening, RBDSDfO_Aok](https://www.youtube.com/watch?v=RBDSDfO_Aok), RollingTardis: title discovered; proxy-blocked, **not watched**.
- [Attempted repair, -tijeWFZ5EA](https://www.youtube.com/watch?v=-tijeWFZ5EA), [repair follow-up, pOV1wJ_UTLA](https://www.youtube.com/watch?v=pOV1wJ_UTLA): search titles/snippets discovered, **not watched**.
- [Pi news demo, _a1n5R9T6qw](https://www.youtube.com/watch?v=_a1n5R9T6qw), [Internet time demo, tzTHZgk0mKQ](https://www.youtube.com/watch?v=tzTHZgk0mKQ), [2018 timing demo, bu3tmA-2Q6M](https://www.youtube.com/watch?v=bu3tmA-2Q6M): linked by inspected sources, **not watched**.

## Open leads and absent artifacts

- Original Morris PIC assembly: an archived CDX index lists `Infoglobe_hack.asm`, but its sole indexed 2025 response is HTML rather than an established assembly payload. Authentic source has not been recovered. The Arduino thread links to it but does not supply a verified copy.
- Wilke's linked historical German manual `http://www.olympia-it.de/Download/BDAInfoGlobe.pdf`, flash animation, and GLOBE demo program distribution: links discovered, artifacts not recovered.
- No factory service schematic/BOM, firmware dump, MCU identification catalog, complete color protocol, or confirmed patent number was located. Public absence is not proven by a failed search.
- MC-specific user manual, exact LED types, original adapter mapping across all revisions, and orange retail suffix remain open.
- Search-result copies and retail aggregators were used to discover sources, not to promote their generated descriptions into specifications. No successful video playback, hardware experiment, or firmware build is claimed.

## Protocol-focused follow-up

See [protocol.md](protocol.md) for the second search's scope and findings. All four gist comments and all 15 issue-465 comments were retrieved through the GitHub API, avoiding incomplete HTML reply rendering.

- [Kong's transition dictionary](https://gist.github.com/kongmunist/a8bdadbacda4bcb129cd183f2f0fffc5#gistcomment-4383041), plus Berdik's additions for decimal effects 20 and 27. Partial dictionary retained in protocol.md; source comments retained with dates and links in protocol-evidence/transition-comments.json.
- [greenmikey's surviving timing data](https://pastebin.com/k7YiFnD9), [raw](https://pastebin.com/raw/k7YiFnD9): five labeled captures of the custom transmitter, not the original base. Retrieved with a normal User-Agent; a later request without it returned 403, so the successful cached response was preserved.
- [Original-base CID LIST capture and Pastebin provenance](https://github.com/crankyoldgit/IRremoteESP8266/issues/465#issuecomment-392227107), [maintainer's artifact warning](https://github.com/crankyoldgit/IRremoteESP8266/issues/465#issuecomment-392316621), and [author's final unsuccessful cleanup report](https://github.com/crankyoldgit/IRremoteESP8266/issues/465#issuecomment-398239702). These limit what the captures establish.
- [Exact indexed ASM archive response](https://web.archive.org/web/20251025070910id_/http://linux-hacker.net/InfoGlobe/Infoglobe_hack.asm): inspected; HTML redirect to `/lander`, not source code.
- GitHub code-search candidate `orospakr/peephole` was inspected and excluded: it is a D-Bus LCD service using an unrelated `ca.infoglobe` namespace, not an Olympia driver.

The first survey missed the gist's existing transition descriptions and issue 465's surviving capture link. The follow-up corrects those omissions; basic transport need not be rediscovered.
