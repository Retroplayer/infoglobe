"""Run from the repository root: python -m tools.infoglobe --help."""
import argparse
from collections import Counter
import datetime
import json
import math
from pathlib import Path
import queue
import sys
import threading
import time
from .session import Session, load


def serial_open(port, baud=115200):
    try:
        import serial
    except ImportError as exc:
        raise SystemExit('Install host dependencies: python -m pip install -r tools/requirements.txt') from exc
    return serial.Serial(port, baud, timeout=.05, write_timeout=2)


def selected(event, view, uncertain):
    c = event['classification']
    if c == 'uncertain':
        return uncertain or view in ('all', 'uncertain')
    return (view == 'all' or (view == 'new' and c in ('partial', 'unknown'))
            or (view == 'unknown' and c == 'unknown') or (view == 'known' and c == 'known'))


def show(event, prefix=''):
    print(f"{prefix}#{event['id']:04d} {event['start_us']/1e6:10.6f}s "
          f"{event['classification']:9s} {event['hex']} | "
          f"{event['interpretation'] or event['family']} | {event['reason']}", flush=True)


def settings(args):
    result = dict(bit_us=args.bit_us, gap_ms=args.gap_ms,
                  tolerance=args.tolerance, leading_ones=args.leading_ones)
    if args.active_high:
        result['active_low'] = False
    if args.rules:
        rules = json.loads(Path(args.rules).read_text(encoding='utf-8'))
        if not isinstance(rules,list):
            raise ValueError('rules file must be a JSON list')
        for rule in rules:
            if not isinstance(rule,dict) or not all(isinstance(rule.get(k),str) for k in
                    ('id','classification','reason','interpretation','evidence')):
                raise ValueError('rule requires id, classification, reason, interpretation, evidence strings')
            if rule['classification'] not in ('known','partial','unknown'):
                raise ValueError('invalid custom rule classification')
            pattern = rule.get('pattern')
            if not isinstance(pattern,list) or not pattern or not all(
                    b is None or (isinstance(b,int) and not isinstance(b,bool) and 0<=b<=255) for b in pattern):
                raise ValueError('rule pattern must be a nonempty list of byte integers or null wildcards')
        result['rules'] = rules
    return result


def dump_json(path, data):
    Path(path).write_text(json.dumps(data, indent=2, ensure_ascii=False)+'\n', encoding='utf-8')


def analyze(args):
    session = load(args.file, **settings(args))
    events = session.events
    wanted = {i for i,e in enumerate(events) if selected(e,args.view,args.include_uncertain)}
    visible = set(wanted)
    for i in wanted:
        visible.update(j for j in range(max(0,i-args.context),min(len(events),i+args.context+1))
                       if events[j]['session'] == events[i]['session'])
    hidden = 0
    for i,event in enumerate(events):
        if i not in visible:
            hidden += 1
            continue
        if hidden:
            print(f'... {hidden} hidden packets; retained in recording ...')
            hidden = 0
        show(event, '' if i in wanted else 'CONTEXT ')
    if hidden:
        print(f'... {hidden} hidden packets; retained in recording ...')
    for marker in session.markers:
        print(f"MARK session={marker['session']} {marker['time_us']/1e6:.6f}s {marker['text']}")
    for problem in session.problems:
        print(f'WARNING: {problem}', file=sys.stderr)
    print(f"{len(events)} packets: {dict(Counter(e['classification'] for e in events))}")
    print('Framing assumes the selected leading silent bits and minimal trailing ones; whole FF bytes may be invisible.')
    if args.json:
        dump_json(args.json, session.report())
    return 1 if session.problems else 0


def capture(args):
    # Exclusive creation prevents overwriting a prior experiment.
    view = args.view
    hidden = 0
    def event(e):
        nonlocal hidden
        if selected(e,view,args.include_uncertain):
            if hidden:
                print(f'... {hidden} hidden packets; saved; use analyze --context to inspect ...')
                hidden = 0
            show(e)
        else:
            hidden += 1
    session = Session(event, lambda text: print(text, flush=True), **settings(args))
    commands = queue.Queue()
    def keyboard():
        try:
            for line in sys.stdin:
                commands.put(line.rstrip('\r\n'))
        except (OSError, ValueError):
            return
    threading.Thread(target=keyboard, daemon=True).start()
    for target in (args.output, args.output+'.notes.jsonl', args.output+'.analysis.json'):
        if Path(target).exists():
            raise FileExistsError(f'refusing to overwrite {target}')
    try:
        with open(args.output, 'xb') as output, open(args.output+'.notes.jsonl', 'x', encoding='utf-8') as notes, serial_open(args.port) as port:
            port.reset_input_buffer()
            print('Capturing. Enter observation text or /mark TEXT; /view all|new|unknown|known|uncertain; /status; /stop.')
            print('Ctrl-C also requests a clean stop. Record video and mark a shared visible event for synchronization.')
            port.write(b'start\n')
            deadline = time.monotonic()+args.duration if args.duration else None
            stopping = None
            startup_deadline = time.monotonic()+10
            while True:
                try:
                    chunk = port.read(16384)
                    if chunk:
                        output.write(chunk)  # Save original wire bytes before analysis.
                        session.feed(chunk)
                    while not commands.empty():
                        text = commands.get_nowait()
                        if text == '/stop':
                            port.write(b'stop\n'); stopping = time.monotonic()+5
                        elif text == '/status':
                            port.write(b'status\n')
                        elif text.startswith('/view '):
                            candidate = text[6:].strip()
                            if candidate in ('all','new','unknown','known','uncertain'):
                                view = candidate
                                print(f'VIEW {view}; capture remains unfiltered')
                            else:
                                print('Unknown view')
                        elif text:
                            text = text[6:] if text.startswith('/mark ') else text
                            # Keep valid UTF-8 within the device marker capacity.
                            encoded = text.encode('utf-8')[:190]
                            text = encoded.decode('utf-8',errors='ignore')
                            host_note = dict(host_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                                             host_monotonic=time.monotonic(), text=text)
                            notes.write(json.dumps(host_note,ensure_ascii=False)+'\n'); notes.flush()
                            port.write(b'mark '+text.encode('utf-8')+b'\n')
                    if deadline and time.monotonic() >= deadline and stopping is None:
                        port.write(b'stop\n'); stopping = time.monotonic()+5
                    if not session.metadata and time.monotonic() >= startup_deadline:
                        session.problem('no recorder metadata within 10 seconds; check port and recorder firmware')
                        break
                    if session.ended:
                        break
                    if stopping and time.monotonic() >= stopping:
                        print('Stop timed out; recording will be flagged if incomplete.',file=sys.stderr)
                        break
                    output.flush()
                except KeyboardInterrupt:
                    if stopping:
                        break
                    port.write(b'stop\n'); stopping = time.monotonic()+5
    except (OSError, ValueError) as exc:
        session.problem(f'capture interrupted: {exc}')
    session.finish()
    dump_json(args.output+'.analysis.json',session.report())
    print(f'Saved {args.output}; {len(session.events)} packets, {len(session.problems)} warnings, {hidden} final hidden packets.')
    return 1 if session.problems else 0


def summary(args):
    session = load(args.file, **settings(args))
    groups = Counter()
    for event in session.events:
        key = (event['classification'],event['hex'] if args.exact else event['family'],event.get('effect'))
        groups[key] += 1
    for (kind, pattern, effect),count in groups.most_common():
        print(f'{count:6d} {kind:9s} {pattern}'+(f' effect={effect:02X}' if effect is not None else ''))
    return 1 if session.problems else 0


def export(args):
    session = load(args.file, **settings(args))
    chosen = next((i for i,e in enumerate(session.events) if e['id']==args.event),None)
    if chosen is None:
        raise ValueError('event ID not found')
    session_id = session.events[chosen]['session']
    events = [e for e in session.events[max(0,chosen-args.before):chosen+args.after+1] if e['session']==session_id]
    if any(e['classification']=='uncertain' for e in events) and not args.allow_uncertain:
        raise ValueError('sequence contains uncertain decodes; inspect timing or use --allow-uncertain')
    dump_json(args.output,dict(format='infoglobe-replay-1',source=str(args.file),
        framing_warning='Bytes are inferred from envelope; leading bits and trailing FF bytes can be ambiguous.',
        settings=settings(args), events=events))
    print(f'Exported {len(events)} packet(s), including event #{args.event}, to {args.output}')


def replay_schedule(events, speed=1):
    if not events or not math.isfinite(speed) or speed <= 0:
        raise ValueError('nonempty sequence and finite positive speed required')
    origin = events[0]['start_us']
    last_end = -float('inf')
    result = []
    for event in events:
        data = bytes(event['bytes'])
        bit = event['bit_us']
        if not 1 <= len(data) <= 256 or not 100 <= bit <= 10000:
            raise ValueError('packet exceeds transmitter byte/timing limits')
        bit_setting = round(bit)
        start = (event['start_us']-origin)/1e6/speed
        if not math.isfinite(start):
            raise ValueError('replay timestamps must be finite')
        duration = len(data)*8*bit_setting/1e6
        # Existing transmitter needs a nonzero trailing gap plus serial command overhead.
        if start < last_end+.003:
            raise ValueError('sequence gaps are too short for CDC replay; cannot reproduce safely at this speed')
        result.append((start,data,bit_setting))
        last_end = start+duration
    return result


def replay(args):
    data = json.loads(Path(args.file).read_text(encoding='utf-8'))
    if data.get('format') != 'infoglobe-replay-1':
        raise ValueError('not an exported replay sequence')
    if any(e['classification']=='uncertain' for e in data['events']) and not args.allow_uncertain:
        raise ValueError('uncertain sequence requires --allow-uncertain')
    if not math.isfinite(args.max_late_ms) or args.max_late_ms < 0:
        raise ValueError('--max-late-ms must be finite and nonnegative')
    plan = replay_schedule(data['events'],args.speed)
    if not args.port or args.dry_run:
        for at,packet,bit in plan:
            print(f'{at:10.6f}s bit={bit} raw {packet.hex(" ").upper()}')
        print('Dry run. Supply --port to transmit. CDC replay is approximate, not a hardware-timed sequencer.')
        return
    with serial_open(args.port) as port:
        def command(text, expected, timeout=3):
            port.write(text.encode('ascii')+b'\n')
            until = time.monotonic()+timeout
            while time.monotonic()<until:
                line = port.readline().decode('ascii', errors='replace').strip()
                if line:
                    print(line)
                if line.startswith('ERR'):
                    raise ValueError(f'transmitter rejected command: {line}')
                if line.startswith(expected):
                    return
            raise ValueError(f'transmitter timeout waiting for {expected}')
        port.reset_input_buffer()
        try:
            command('stop','OK')
            command('repeat 0','OK')
            command('polarity 1','OK')
            command('gap 1','OK')
            epoch = time.monotonic()+.2
            previous_bit = None
            for at,packet,bit in plan:
                if bit != previous_bit:
                    command(f'bit {bit}','OK')
                    previous_bit = bit
                target = epoch+at
                while time.monotonic()<target:
                    time.sleep(min(.005,target-time.monotonic()) if target>time.monotonic() else 0)
                lateness = time.monotonic()-target
                if lateness > args.max_late_ms/1000:
                    raise ValueError(f'replay deadline missed by {lateness*1000:.1f} ms; aborted')
                print(f'REPLAY event at {at:.6f}s; host dispatch lateness {lateness*1000:.3f} ms')
                command('raw '+packet.hex(' '),'DONE',len(packet)*8*bit/1e6+3)
                # Allow the transmitter gap and CDC round trip before another setting/packet.
                time.sleep(.002)
        finally:
            port.write(b'stop\n')


def timing_arguments(parser):
    parser.add_argument('--rules',help='JSON recognition rules; exact packet-length patterns')
    parser.add_argument('--bit-us',type=float,default=1000)
    parser.add_argument('--gap-ms',type=float,default=20)
    parser.add_argument('--tolerance',type=float,default=.25,help='maximum run residual, in bit cells')
    parser.add_argument('--active-high',action='store_true',help='carrier detected as HIGH instead of LOW')
    parser.add_argument('--leading-ones',type=int,choices=range(8),default=0)


def view_arguments(parser):
    parser.add_argument('--view',choices=['all','new','unknown','known','uncertain'],default='new')
    parser.add_argument('--include-uncertain',action='store_true',help='also show acquisition/decoding problems')


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    subs = parser.add_subparsers(dest='command',required=True)
    p = subs.add_parser('capture',help='record receiver firmware CDC output without filtering the file')
    p.add_argument('--port',required=True);p.add_argument('--output',required=True)
    p.add_argument('--duration',type=float,help='automatically stop after N seconds')
    timing_arguments(p);view_arguments(p);p.set_defaults(func=capture)
    p = subs.add_parser('analyze',help='decode/reclassify an existing recording')
    p.add_argument('file');p.add_argument('--json');p.add_argument('--context',type=int,default=0)
    timing_arguments(p);view_arguments(p);p.set_defaults(func=analyze)
    p = subs.add_parser('summary',help='group repeated packets or command families')
    p.add_argument('file');p.add_argument('--exact',action='store_true')
    timing_arguments(p);p.set_defaults(func=summary)
    p = subs.add_parser('export',help='export event and surrounding packets for replay')
    p.add_argument('file');p.add_argument('--event',type=int,required=True)
    p.add_argument('--before',type=int,default=0);p.add_argument('--after',type=int,default=0)
    p.add_argument('--output',required=True);p.add_argument('--allow-uncertain',action='store_true')
    timing_arguments(p);p.set_defaults(func=export)
    p = subs.add_parser('replay',help='dry-run or send an exported sequence to transmitter firmware')
    p.add_argument('file');p.add_argument('--port');p.add_argument('--dry-run',action='store_true')
    p.add_argument('--speed',type=float,default=1);p.add_argument('--max-late-ms',type=float,default=20)
    p.add_argument('--allow-uncertain',action='store_true');p.set_defaults(func=replay)
    args = parser.parse_args(argv)
    for name in ('context','before','after'):
        if hasattr(args,name) and getattr(args,name)<0:
            parser.error(f'--{name} must be nonnegative')
    if hasattr(args,'duration') and args.duration is not None and args.duration<=0:
        parser.error('--duration must be positive')
    try:
        return args.func(args) or 0
    except (ValueError, OSError) as exc:
        print(f'ERROR: {exc}',file=sys.stderr)
        return 1

if __name__ == '__main__':
    raise SystemExit(main())
