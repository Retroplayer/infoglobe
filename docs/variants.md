# Product, color, and revision identification

Survey date: 2026-10-19. Target supplied by owner: **OL3000.2**. No photographs or measurements of the owner's unit have been supplied. Photographs below show other specimens.

## Findings

There are genuine **blue and purple translucent dome variants, an orange translucent dome variant, and a multicolor-display version with a dark/smoked-looking dome**. Enclosure color and emitted LED color must be recorded separately. A purple dome is not evidence of RGB LEDs. The `.2` model suffix is not a sufficient color identifier.

| Variant / identifier | Evidence inspected | What it establishes | What it does not establish |
| --- | --- | --- | --- |
| Blue dome, blue display; OL3000 family | LED Museum hands-on review; Morris's OL3000.2 report; blue retail packaging | Blue light comes from blue LEDs, in addition to the blue-tinted dome | Universal PCB revision or identical electronics across all blue units |
| **OL3000LB** | [Listing and factory-box photographs](https://www.ebay.com/itm/287604928947) | Box side marked OL3000LB, blue product artwork; barcode **850138000379**; copyright 2003 | Meaning of every letter in the suffix; the label of the packed unit was not visible |
| **OL3000LP**, purple dome | [Listing with box, operating unit, and underside label](https://www.ebay.com/itm/206510295821) | Box marked OL3000LP; purple enclosure; warm/pink-looking text in photographs; underside model **OL3000.2** | Exact LED wavelength; whether all LP units use identical LEDs or firmware |
| Purple dome, **OL3000.2** | [Independent purple-unit listing](https://www.ebay.com/itm/860045249168) | Clear underside model label OL3000.2 and purple dome in the same photo set | This specimen's LED color: it is photographed unpowered |
| Orange dome | [Operating photographs](https://www.ebay.com/itm/257326223130), plus an owner report in the HAnix repair comments | Orange enclosure and warm amber/orange-looking displayed text; an owner separately reports an original orange-display unit | Retail suffix, underside model, exact LED color, original adapter identity |
| **OL3000MC**, multicolor | [Factory packaging](https://www.ebay.com/itm/168641682196) and [operating red/blue/green photos with matching MC box](https://www.ebay.com/itm/257624473526) | Box explicitly marked OL3000MC and “Messages in Multi Colors”; three photographed display colors; dark dome and dark base; one box copyright 2005 | Arbitrary RGB mixing, simultaneous per-character colors, color command bytes, or compatibility with monochrome firmware |
| Older 9 V backup-battery version | Morris explicitly distinguishes it from his three-AAA OL3000.2 | At least one additional reported hardware generation, with different button labels | A verified older model suffix, date, color, or PCB number |
| InfoGlobe Plus **OL3020** | [Replacement-dome listing](https://www.ebay.com/itm/254362927202), owner report of globe + handset, and retail search results | A related cordless-phone product, separate from the standalone OL3000 | Shared rotor, power, or protocol compatibility |
| **OL3021 / OL3022** | Combined manual search result; [OL3022 manual text](https://manualzz.com/doc/63015679/olympia-ol3022-infoglobe-owner%E2%80%99s-manual); FCC exhibit index | Related wireless caller-ID family; OL3022 text describes pairing/security-code transfer with a base/cradle | They are cosmetic OL3000 variants or share the OL3000.2 base electronics |

The `LB` and `LP` association with blue and purple is supported by the packaging photographs. Do not extrapolate an orange `LO` designation: targeted searching did not establish it. Searches for `.1` and `.3` also did not establish actual labeled specimens. A Scribd search result titled “OL3200.2, Question Mark” is an unverified uploader title, not a confirmed model. Likewise, `OL3200` inside a telephone registration number is not proof of the consumer model.

## Photographic evidence

### Purple: retail suffix and underside model coexist

[OL3000LP box](evidence/ol3000lp-box.jpg), [purple operating display](evidence/purple-operating-display.jpg), and a separate specimen's [OL3000.2 label](evidence/purple-ol3000-2-label.jpg) establish why we must keep retail SKU and underside model in different fields.

The clear label reads:

- MODEL NO. **OL3000.2**
- Registration **US: DDKND01BOL3200NNN**
- USOC jack **RJ11C**; REN **0.1B**
- ETL listed **117235**; made in China

This is a **telephone Part 68 registration identifier**, not an RF FCC ID. It should not be entered into an RF filing search as though it identified a transmitter. The label also says “U.S. PATENT PENDING,” but gives no patent number.

### Multicolor: actual red, green, and blue output

[MC factory box](evidence/ol3000mc-box.jpg), [red output](evidence/multicolor-red.jpg), [green output](evidence/multicolor-green.jpg), and [blue output](evidence/multicolor-blue.jpg) are separate photographs from sourced listings. They support three selectable display colors, not a claim of full-color graphics.

In the [HAnix repair thread](https://hanixdiy.blogspot.com/2011/08/fixing-infoglobe.html), Ian S reports a three-color unit on 2012-12-01. The author replies that its rotor head is larger because it has **three sets of LEDs**, and says color information travels over the IR link. Treat the circuit description as an experienced author's report, pending direct multicolor-board photographs and signal captures. The inspected monochrome protocol documentation does not define color selection bytes.

### Orange: enclosure confirmed; model mapping open

[Operating orange unit](evidence/orange-operating-display.jpg). Do not infer the semiconductor color from the seller's “ORANGE” title alone: both the dome and camera exposure affect appearance. The 2017-12-08 HAnix owner comment independently distinguishes an earlier orange-LED unit from a later blue one, but supplies no model label.

### Seller metadata can be wrong

[Listing 376853965202](https://www.ebay.co.uk/itm/376853965202) is titled “Purple OL-3000.2” but shows a blue-looking dome with bright blue text. A product's “Color” item field may describe the dome, base, light, or simply a catalog default. In another listing, OL3000MC factory packaging appears despite the generic item field saying OL3000 and Blue. Photos of labels and boxes take precedence over item fields. Marketplace stock numbers such as “#2176 uu” are seller inventory numbers.

## What this means for reverse engineering

1. Record the owner's underside model and dome color independently, then record its operating LED color(s), backup battery type, controls, PCB assembly/revision markings, and component markings.
2. Treat Morris's OL3000.2 monochrome work as a strong starting point, not proof that every OL3000.2 SKU is electrically identical.
3. Multicolor needs an explicit protocol investigation. Preserve and capture each original color mode before replacing the base transmitter. Monochrome code has no established color-control implementation.
4. Keep the standalone, Plus/cordless, and wireless-display products separate. Their manuals and regulatory files can otherwise create misleading feature and circuit conclusions.
5. LED replacements, such as a repair commenter replacing blue LEDs with “ice blue,” are aftermarket modifications, not evidence of a factory variant.

## Remaining catalog gaps

- Orange retail suffix and clear orange-unit label; multicolor underside label and PCB photographs.
- Complete list of factory colors, regions, and retail suffixes; no factory color catalog has been located.
- Mapping from each SKU to base/rotor PCB revisions and firmware.
- Exact monochrome LED part numbers/wavelengths and multicolor LED population/driver arrangement.

The evidence establishes multiple variants; it does not establish that these are every variant ever sold. See [source register](sources.md) and [image provenance manifest](evidence/manifest.json).
