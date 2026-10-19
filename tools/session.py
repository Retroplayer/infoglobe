"""Session processing shared by live capture and offline analysis."""
import json
import struct
from .decoder import Decoder
from .wire import Framer, METADATA, SAMPLES, MARKER, STATUS, END, LOSS


class Session:
    def __init__(self, on_event=lambda event: None, on_notice=lambda text: None, **settings):
        self.settings = settings
        self.on_event = on_event
        self.on_notice = on_notice
        self.events = []
        self.markers = []
        self.metadata = []
        self.problems = []
        self.decoder = None
        self.active = False
        self.ended = False
        self.session = None
        self.framer = Framer(self.problem)

    def problem(self, message):
        self.problems.append(message)
        self.on_notice(f'WARNING: {message}')
        if self.decoder:
            self.decoder.finish(message)
            self.decoder.reset(message)

    def event(self, event):
        event['id'] = len(self.events)+1
        event['session'] = self.session
        self.events.append(event)
        self.on_event(event)

    def feed(self, data):
        for record in self.framer.feed(data):
            try:
                self.record(record)
            except (ValueError, KeyError, TypeError, struct.error) as exc:
                self.problem(f'invalid record {record.sequence}: {exc}')

    def record(self, record):
        if record.flags:
            raise ValueError('unsupported record flags')
        if record.type == METADATA:
            if self.active:
                self.problem('new session without END/LOSS record')
            meta = json.loads(record.payload)
            if meta['format'] != 'u32le-msb-first' or not 1 <= meta['sample_rate'] <= 10000000:
                raise ValueError('unsupported sample format/rate')
            self.metadata.append(meta)
            self.session = meta['session']
            settings = dict(self.settings)
            settings.setdefault('active_low', meta['active_low'])
            self.decoder = Decoder(self.event, sample_rate=meta['sample_rate'], **settings)
            self.active, self.ended = True, False
            self.on_notice(f"SESSION {self.session}: {meta['sample_rate']} samples/s, GPIO {meta['gpio']}")
        elif record.type == SAMPLES:
            if not self.active:
                raise ValueError('samples outside an active session')
            if self.decoder.next_sample is not None and record.sample != self.decoder.next_sample:
                self.problem(f'sample discontinuity: expected {self.decoder.next_sample}, got {record.sample}')
            self.decoder.samples(record.sample, record.payload)
        elif record.type == MARKER:
            if len(record.payload) < 8:
                raise ValueError('short marker')
            receipt_us = struct.unpack_from('<Q', record.payload)[0]
            rate = self.decoder.rate if self.decoder else 1000000
            marker = dict(session=self.session, sample=record.sample,
                          time_us=record.sample*1e6/rate, receipt_device_us=receipt_us,
                          text=record.payload[8:].decode('utf-8', errors='replace'))
            self.markers.append(marker)
            self.on_notice(f"MARK {marker['time_us']/1e6:.6f}s: {marker['text']}")
        elif record.type in (END, LOSS):
            info = json.loads(record.payload)
            if self.decoder:
                self.decoder.finish(info.get('reason', 'end'))
            self.active, self.ended = False, True
            if record.type == LOSS:
                self.problem(f"acquisition loss: {info.get('reason')}")
            self.on_notice(f'END {json.dumps(info, sort_keys=True)}')
        elif record.type == STATUS:
            self.on_notice(f'STATUS {record.payload.decode("utf-8", errors="replace")}')
        else:
            self.problem(f'unsupported record type {record.type}')

    def finish(self):
        self.framer.finish()
        if self.active:
            self.problem('recording has no END/LOSS record; capture may be truncated')
        if self.decoder:
            self.decoder.finish()

    def report(self):
        return dict(format='infoglobe-analysis-1', settings=self.settings,
                    metadata=self.metadata, events=self.events, markers=self.markers,
                    problems=self.problems)


def load(path, **settings):
    session = Session(**settings)
    with open(path, 'rb') as source:
        while chunk := source.read(65536):
            session.feed(chunk)
    session.finish()
    return session
