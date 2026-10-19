"""Run the assembled PIO instructions in an independent emulator.
Usage: python tests/test_pio.py build/transmit.pio.h
Requires rp2040-pio-emulator==0.88.0.
"""
from collections import deque
from pathlib import Path
import re
import sys
from pioemu import State, emulate

header = Path(sys.argv[1]).read_text()
body = header.split('transmit_program_instructions[] = {')[1].split('};')[0]
opcodes = [int(x, 16) for x in re.findall(r'^\s*(0x[0-9a-f]+),', body, re.M)]
assert len(opcodes) == 7
cases = 0
for length in (1, 2, 3, 4, 5, 35, 38, 256):
    for zero_high in (False, True):
        data = bytes((i * 73 + length) % 256 for i in range(length))
        sig = bytes(b ^ (255 if zero_high else 0) for b in data)
        words = deque([length * 8 - 1])
        for i in range(0, length, 4):
            words.append(int.from_bytes(sig[i:i+4].ljust(4, b'\0'), 'big'))
        initial = State(transmit_fifo=deque(), pin_directions=1)

        def refill_and_stop(opcode, state):
            while words and len(state.transmit_fifo) < 8:
                state.transmit_fifo.append(words.popleft())
            assert state.clock < length * 8 * 33 + 100, 'PIO stalled'
            return state.program_counter == 6  # Stop before IRQ (unsupported by emulator).

        trace = list(emulate(opcodes, stop_when=refill_and_stop,
                             initial_state=initial, auto_pull=True,
                             shift_osr_right=False, out_count=1, set_count=1))
        bits = [(before.clock, after.pin_values & 1) for before, after in trace
                if before.program_counter == 3]
        expected = [(b >> shift) & 1 for b in sig for shift in range(7, -1, -1)]
        assert [b for _, b in bits] == expected
        assert all(b[0] - a[0] == 33 for a, b in zip(bits, bits[1:]))
        final_before, final_after = trace[-1]
        assert final_before.program_counter == 5
        assert final_before.clock - bits[-1][0] == 33
        assert final_after.pin_values & 1 == 0
        cases += 1
print(f'PASS: {cases} assembled-PIO cases; MSB order, 33-cycle cells, exact lengths, idle LOW')
