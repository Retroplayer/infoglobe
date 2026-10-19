"""Create clearly labeled synthetic captures for offline tool exercises."""
import argparse
import json
import struct
from .wire import Record, encode, METADATA, SAMPLES, MARKER, END


def pack_runs(runs):
    """Pack (level, sample count) runs into LE words with chronological MSB samples."""
    output = bytearray()
    word = used = 0
    for level, count in runs:
        while count:
            n = min(32-used, count)
            word = (word << n) | ((1 << n)-1 if level else 0)
            used += n
            count -= n
            if used == 32:
                output.extend(struct.pack('<I',word))
                word = used = 0
    if used:
        word = (word << (32-used)) | ((1 << (32-used))-1)
        output.extend(struct.pack('<I',word))
    return bytes(output)


def recording(packets, *, bit_us=1000, stretch_us=0, chunk_words=1024, session=1):
    runs = []
    at = 0
    for start, data in packets:
        if start < at:
            raise ValueError('overlapping synthetic packets')
        runs.append((1,start-at))
        spans = []
        for b in data:
            for bit in range(7,-1,-1):
                level = (b >> bit) & 1
                if spans and spans[-1][0] == level:
                    spans[-1] = (level,spans[-1][1]+bit_us)
                else:
                    spans.append((level,bit_us))
        for level,n in spans:
            runs.append((level,n+(-stretch_us if level else stretch_us)))
        at = start+len(data)*8*bit_us
    runs.append((1,50000))
    payload = pack_runs(runs)
    metadata = dict(firmware='synthetic-1-NOT-HARDWARE',session=session,sample_rate=1000000,
                    gpio=3,active_low=True,format='u32le-msb-first',block_samples=chunk_words*32)
    records = [Record(METADATA,0,0,json.dumps(metadata).encode())]
    for i in range(0,len(payload),chunk_words*4):
        records.append(Record(SAMPLES,len(records),i*8,payload[i:i+chunk_words*4]))
    records.append(Record(MARKER,len(records),200000,struct.pack('<Q',123456)+b'SYNTHETIC demo observation'))
    records.append(Record(END,len(records),len(payload)*8,b'{"reason":"synthetic_complete","loss":false}'))
    return b''.join(encode(r) for r in records)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output')
    args = parser.parse_args()
    packets = [(10000,b'\x01BASELINE'),(200000,b'\x07\x10\x42'),
               (400000,b'\x00\x00TEST\x06'),(600000,b'\x04SCROLL'),
               (800000,b'\x00\x00HELLO\x0c')]
    with open(args.output,'xb') as f:
        f.write(recording(packets))
    print(f'Saved SYNTHETIC recording to {args.output}; not an Infoglobe measurement.')

if __name__ == '__main__':
    main()
