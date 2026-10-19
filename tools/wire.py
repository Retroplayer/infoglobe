"""Version 1 recorder framing. Original bytes are always saved before parsing."""
from dataclasses import dataclass
import struct
import zlib
MAGIC = b'IGCP'
HEADER = struct.Struct('<4sBBHIQI')
CRC = struct.Struct('<I')
METADATA, SAMPLES, MARKER, STATUS, END, LOSS = range(1, 7)
MAX_PAYLOAD = 65536

@dataclass
class Record:
    type: int
    sequence: int
    sample: int
    payload: bytes
    flags: int = 0


def encode(record):
    head = HEADER.pack(MAGIC, 1, record.type, record.flags, record.sequence,
                       record.sample, len(record.payload))
    return head + record.payload + CRC.pack(zlib.crc32(head + record.payload))


class Framer:
    def __init__(self, on_error=lambda message: None):
        self.buffer = bytearray()
        self.on_error = on_error
        self.last_sequence = None
        self.errors = 0

    def error(self, message):
        self.errors += 1
        self.on_error(message)

    def feed(self, data):
        self.buffer.extend(data)
        while True:
            pos = self.buffer.find(MAGIC)
            if pos < 0:
                if len(self.buffer) > 3:
                    self.error(f'discarded {len(self.buffer)-3} unframed bytes')
                    del self.buffer[:-3]
                return
            if pos:
                self.error(f'discarded {pos} unframed bytes')
                del self.buffer[:pos]
            if len(self.buffer) < HEADER.size:
                return
            _, version, kind, flags, seq, sample, n = HEADER.unpack_from(self.buffer)
            if version != 1 or n > MAX_PAYLOAD:
                self.error('unsupported version or impossible frame length')
                del self.buffer[0]
                continue
            size = HEADER.size + n + CRC.size
            if len(self.buffer) < size:
                return
            expected = CRC.unpack_from(self.buffer, HEADER.size+n)[0]
            if zlib.crc32(self.buffer[:HEADER.size+n]) != expected:
                self.error('CRC mismatch; searching for next frame')
                del self.buffer[0]
                continue
            if self.last_sequence is not None and seq != (self.last_sequence+1) & 0xffffffff:
                self.error(f'sequence discontinuity: {self.last_sequence} -> {seq}')
            self.last_sequence = seq
            payload = bytes(self.buffer[HEADER.size:HEADER.size+n])
            del self.buffer[:size]
            yield Record(kind, seq, sample, payload, flags)

    def finish(self):
        if self.buffer:
            self.error(f'truncated stream: {len(self.buffer)} remaining bytes')
