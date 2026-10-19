"""Envelope reconstruction, provisional framing, and evidence-based rules."""
import hashlib
import json
import statistics
import struct
RULE_VERSION = 'ol3000-literature-1'
EFFECTS = {
    0:'incoming text counterclockwise',1:'incoming text clockwise',2:'pincers',
    3:'pixel fade',4:'clockwise sweep',5:'counterclockwise sweep',
    7:'old text counterclockwise',8:'row grow',9:'horizontal shrink/expand',
    10:'alternating-line fill',11:'letter phase',12:'replace letters counterclockwise',
    13:'replace letters clockwise',14:'alternate letters counterclockwise',
    15:'alternate letters clockwise',16:'old down/new up',17:'old up/new down',
    18:'letters from above',19:'letters from below',20:'counterclockwise loop',
    21:'loop erase/place',24:'bounce from below',25:'bounce from above',
    26:'drop left to right',27:'drop right to left',28:'random drop',
    30:'pluck left to right',33:'random pluck',34:'letter fade from right'}


def classify(data):
    result = dict(classification='unknown', reason='unrecognized command structure',
                  family='unknown', interpretation='', evidence='literature',
                  rule_version=RULE_VERSION)
    if not data:
        result.update(classification='uncertain', reason='no complete bytes')
        return result
    op, payload = data[0], data[1:]
    result['family'] = f'opcode-{op:02X}'
    if op in (1, 4):
        result['family'] = 'static' if op == 1 else 'scroll'
        result['interpretation'] = f"{result['family']} {payload.decode('ascii', errors='backslashreplace')!r}"
        if len(payload) <= 35 and all(32 <= b <= 126 for b in payload):
            result.update(classification='known', reason='documented text command and ordinary ASCII payload')
        else:
            result.update(classification='partial', reason='recognized text opcode; unusual length or glyph bytes')
    elif op == 6:
        result.update(family='toggle', interpretation='toggle existing scrolling',
                      classification='known' if len(data) == 1 else 'partial',
                      reason='documented single-byte toggle' if len(data) == 1 else 'toggle with unexplained extra bytes')
    elif op in (2, 3, 5):
        result.update(classification='partial', family=f'command-{op:02X}',
                      reason='conflicting flashing definitions' if op in (2, 5) else 'inherited scroll state needs validation')
    elif op == 0:
        result.update(classification='partial', family='transition', reason='transition opcode with unresolved framing')
        if len(data) >= 3 and data[1] == 0:
            text, effect = data[2:-1], data[-1]
            result.update(effect=effect, text=text.decode('ascii', errors='backslashreplace'))
            result['interpretation'] = f"effect {effect:02X}: {EFFECTS.get(effect, 'undocumented effect')} {result['text']!r}"
            if len(text) <= 35 and all(32 <= b <= 126 for b in text) and effect in EFFECTS:
                result.update(classification='known', reason='documented transition structure and described effect')
            else:
                result['reason'] = 'transition family; effect, glyphs, or payload length not fully understood'
    return result


class Decoder:
    def __init__(self, on_event, *, sample_rate=1000000, bit_us=1000,
                 gap_ms=20, tolerance=0.25, active_low=True, leading_ones=0, rules=None):
        if not (100 <= bit_us <= 10000 and gap_ms > 0 and 0 < tolerance < .5 and 0 <= leading_ones <= 7):
            raise ValueError('invalid timing, tolerance or alignment setting')
        self.on_event = on_event
        self.rules = rules or []
        self.rate = sample_rate
        self.nominal = bit_us
        self.gap = gap_ms * sample_rate / 1000
        self.tolerance = tolerance
        self.carrier = 0 if active_low else 1
        self.leading = leading_ones
        self.next_sample = None
        self.level = None
        self.run_start = 0
        self.runs = []
        self.event_id = 0
        self.taint = None

    def reset(self, reason):
        self.finish(reason)
        self.taint = reason
        self.next_sample = None
        self.level = None
        self.runs = []

    def _run(self, level, start, duration):
        if not duration:
            return
        if level != self.carrier and duration >= self.gap:
            if self.runs:
                self.flush(self.taint)
            self.taint = None
            return
        if self.runs or level == self.carrier:
            self.runs.append((level, start, duration))
            if len(self.runs) >= 8192:
                self.flush('analysis limit: 8192 runs without a packet delimiter')
                self.taint = 'continuation after analysis limit; waiting for delimiter' 

    def samples(self, start, payload):
        if len(payload) % 4:
            raise ValueError('sample payload is not a whole number of 32-bit words')
        if self.next_sample is not None and start != self.next_sample:
            self.reset(f'sample discontinuity: expected {self.next_sample}, got {start}')
        at = start
        # Split each word into constant-level spans without expanding individual samples.
        for (word,) in struct.iter_unpack('<I', payload):
            remaining = 32
            while remaining:
                level = (word >> 31) & 1
                different = (~word & 0xffffffff) if level else word
                n = min(remaining, 32 - different.bit_length())
                if level != self.level:
                    if self.level is not None:
                        self._run(self.level, self.run_start, at-self.run_start)
                    self.level, self.run_start = level, at
                at += n
                remaining -= n
                word = (word << n) & 0xffffffff
        self.next_sample = at
        if self.level != self.carrier and at-self.run_start >= self.gap and self.runs:
            self.flush(self.taint)
            self.taint = None

    def finish(self, reason='recording ended before packet delimiter'):
        if self.level is not None and self.next_sample is not None:
            self._run(self.level, self.run_start, self.next_sample-self.run_start)
        if self.runs:
            self.flush(reason or self.taint)
        self.level = None

    def flush(self, forced_reason=None):
        runs, self.runs = self.runs, []
        if not runs:
            return
        durations = [n*1e6/self.rate for _, _, n in runs]
        # Adjacent opposite-level pairs reduce systematic demodulator edge-delay bias.
        pairs = [durations[i]+durations[i+1] for i in range(0, len(durations)-1, 2)]
        basis = pairs or durations
        estimates = [d/max(1, round(d/self.nominal)) for d in basis]
        bit = statistics.median(estimates)
        bits = [1]*self.leading
        residuals = []
        reasons = [forced_reason] if forced_reason else []
        for (level, _, _), d in zip(runs, durations):
            count = max(1, round(d/bit))
            residuals.append(abs(d/bit-count))
            if len(bits)+count > 32768:
                reasons.append('packet exceeds 32768-bit analysis limit')
                break
            bits.extend([0 if level == self.carrier else 1]*count)
        if residuals and max(residuals) > self.tolerance:
            reasons.append('run durations do not fit bit cells within tolerance')
        # The final silence can contain data ones and an arbitrary number of FF bytes.
        # Add only enough ones to finish the last byte. Never invent whole FF bytes.
        bits.extend([1]*((-len(bits)) % 8))
        data = bytes(sum(bits[i+j] << (7-j) for j in range(8)) for i in range(0, len(bits), 8))
        start = runs[0][1] - self.leading*bit*self.rate/1e6
        info = classify(data)
        matches = [r for r in self.rules if len(data) == len(r['pattern']) and
                   all(b is None or b == d for b,d in zip(r['pattern'],data))]
        if len(matches) == 1:
            r = matches[0]
            info.update(classification=r['classification'], reason=r['reason'],
                        interpretation=r['interpretation'], evidence=r['evidence'],
                        family=r.get('family',r['id']), rule_id=r['id'],
                        rule_version=RULE_VERSION+'+custom-'+hashlib.sha256(
                            json.dumps(self.rules,sort_keys=True).encode()).hexdigest()[:12])
        elif len(matches) > 1:
            info.update(classification='partial',reason='conflicting custom recognition rules')
        semantic = info['classification']
        if reasons:
            info.update(classification='uncertain', reason='; '.join(reasons))
        self.event_id += 1
        event = dict(id=self.event_id, start_sample=start, start_us=start*1e6/self.rate,
                     end_us=start*1e6/self.rate+len(bits)*bit,
                     bytes=list(data), hex=data.hex(' ').upper(), bit_us=bit,
                     max_residual_bits=max(residuals, default=0), semantic_classification=semantic,
                     framing=f'assumed {self.leading} leading silent bits; minimal trailing ones; extra FF bytes indeterminate',
                     timing_runs=[dict(level=l, sample=s, samples=n) for l,s,n in runs], **info)
        self.on_event(event)
