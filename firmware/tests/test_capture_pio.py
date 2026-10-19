"""Check assembled sampler timing and bit packing with an independent PIO emulator."""
from collections import deque
from pathlib import Path
import re
import sys
from pioemu import State, emulate
body = Path(sys.argv[1]).read_text().split('capture_program_instructions[] = {')[1].split('};')[0]
opcodes = [int(x,16) for x in re.findall(r'^\s*(0x[0-9a-f]+),',body,re.M)]
assert opcodes == [0x4001]
samples = [int((i*17)%23 < 9) for i in range(256)]
words = []

def stop(opcode,state):
    while state.receive_fifo:
        words.append(state.receive_fifo.popleft())
    return state.clock == len(samples)

def input_source(state: State) -> int:
    return samples[state.clock]

trace = list(emulate(opcodes,stop_when=stop,initial_state=State(receive_fifo=deque()),
                     input_source=input_source,auto_push=True,
                     shift_isr_right=False))
expected = [sum(samples[i+j] << (31-j) for j in range(32)) for i in range(0,len(samples),32)]
assert words == expected, (words,expected)
assert all(after.clock-before.clock == 1 for before,after in trace)
print('PASS: assembled capture PIO; 1 sample/clock, exact sample order and 32-bit packing')
