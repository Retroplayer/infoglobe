import contextlib
import io
import json
from pathlib import Path
import struct
import tempfile
import unittest
from tools.decoder import Decoder, classify
from tools.infoglobe import main, replay_schedule, selected
from tools.session import Session
from tools.synthetic import pack_runs, recording
from tools.wire import Framer, Record, encode, SAMPLES


class WireTests(unittest.TestCase):
    def test_fragmented_crc_and_resynchronization(self):
        one = encode(Record(SAMPLES,0,0,b'\x55'*16))
        bad = bytearray(encode(Record(SAMPLES,1,128,b'\xaa'*16)))
        bad[25] ^= 1
        three = encode(Record(SAMPLES,2,256,b'\xff'*16))
        framer = Framer()
        got = []
        for b in one+bad+three:
            got.extend(framer.feed(bytes([b])))
        framer.finish()
        self.assertEqual([r.sequence for r in got],[0,2])
        self.assertGreaterEqual(framer.errors,2)

    def test_truncated_record(self):
        f = Framer()
        list(f.feed(encode(Record(1,0,0,b'hello'))[:-1]))
        f.finish()
        self.assertEqual(f.errors,1)

    def test_sequence_wrap(self):
        f = Framer()
        list(f.feed(encode(Record(1,0xffffffff,0,b''))+encode(Record(1,0,0,b''))))
        self.assertEqual(f.errors,0)


class DecoderTests(unittest.TestCase):
    def decode(self,packets,**kwargs):
        s = Session()
        data = recording(packets,**kwargs)
        for i in range(0,len(data),157):
            s.feed(data[i:i+157])
        s.finish()
        self.assertFalse(s.problems,s.problems)
        return s

    def test_packets_cross_dma_boundaries_and_known_unknown(self):
        packets = [(10000,b'\x04HI'),(100000,b'\x07\x42'),
                   (200000,b'\x00\x00TEST\x06'),(400000,b'\x00\x00HI\x0c')]
        s = self.decode(packets,chunk_words=17)
        self.assertEqual([bytes(e['bytes']) for e in s.events],[p[1] for p in packets])
        self.assertEqual([e['classification'] for e in s.events],['known','unknown','partial','known'])
        self.assertEqual(len(s.markers),1)

    def test_receiver_stretch_and_bit_rate_estimation(self):
        s = self.decode([(10000,b'\x04TIMING TEST')],bit_us=980,stretch_us=100)
        self.assertEqual(bytes(s.events[0]['bytes']),b'\x04TIMING TEST')
        self.assertEqual(s.events[0]['classification'],'known')
        self.assertAlmostEqual(s.events[0]['bit_us'],980,delta=1)

    def test_long_carrier_and_silent_ff_ambiguity(self):
        packets = [(10000,b'\x00\x00\x00'),(100000,b'\x06\xff')]
        s = self.decode(packets)
        self.assertEqual(s.events[0]['bytes'],[0,0,0])
        self.assertEqual(s.events[1]['bytes'],[6])
        self.assertIn('FF',s.events[1]['framing'])

    def test_bad_timing_is_not_unknown_command(self):
        events = []
        d = Decoder(events.append)
        payload = pack_runs([(1,1000),(0,1500),(1,1600),(0,5100),(1,30000)])
        d.samples(0,payload);d.finish()
        self.assertEqual(events[0]['classification'],'uncertain')

    def test_continuity_break_never_joins_packets(self):
        events = []
        d = Decoder(events.append)
        d.samples(0,pack_runs([(0,4000)]))
        d.samples(8000,pack_runs([(0,4000),(1,30000)]))
        d.finish()
        self.assertGreaterEqual(len(events),1)
        self.assertEqual(events[0]['classification'],'uncertain')

    def test_active_high(self):
        events = []
        raw = pack_runs([(1,7000),(0,1000),(1,1000),(0,30000)])
        d = Decoder(events.append,active_low=False)
        d.samples(0,raw);d.finish()
        self.assertEqual(events[0]['bytes'],[1,127])

    def test_unresolved_definitions_remain_partial(self):
        for data in (b'\x02\x01HI',b'\x03HI',b'\x05HI',b'\x06EXTRA',b'\x01\x80',b'\x00\x00HI\x23'):
            self.assertEqual(classify(data)['classification'],'partial')

    def test_filter_is_nondestructive(self):
        s = self.decode([(10000,b'\x01HI'),(100000,b'\x07\x42')])
        visible = [e for e in s.events if selected(e,'new',False)]
        self.assertEqual(len(visible),1)
        self.assertEqual(len(s.events),2)
        self.assertEqual(visible[0]['classification'],'unknown')


class WorkflowTests(unittest.TestCase):
    def test_analyze_export_and_replay_dry_run(self):
        with tempfile.TemporaryDirectory() as temp:
            p = Path(temp)
            capture = p/'test.igcap'
            capture.write_bytes(recording([(10000,b'\x01HI'),(150000,b'\x07\x42'),(300000,b'\x04HI')]))
            original = capture.read_bytes()
            with contextlib.redirect_stdout(io.StringIO()) as out:
                result = main(['analyze',str(capture),'--context','1','--json',str(p/'analysis.json')])
                self.assertEqual(result,0)
                self.assertIn('CONTEXT',out.getvalue())
                self.assertEqual(main(['export',str(capture),'--event','2','--before','1','--after','1',
                                       '--output',str(p/'replay.json')]),0)
                self.assertEqual(main(['replay',str(p/'replay.json'),'--dry-run']),0)
            self.assertEqual(capture.read_bytes(),original)
            report = json.loads((p/'analysis.json').read_text())
            self.assertEqual(len(report['events']),3)
            self.assertIn('timing_runs',report['events'][1])

    def test_tight_sequence_rejected(self):
        events = [dict(start_us=0,bytes=[1],bit_us=1000),dict(start_us=9000,bytes=[1],bit_us=1000)]
        with self.assertRaises(ValueError):
            replay_schedule(events)

    def test_loss_and_truncation_reported(self):
        data = recording([(10000,b'\x01HI')])
        s = Session()
        s.feed(data[:-35]);s.finish()
        self.assertTrue(s.problems)

class LiveWorkflowTests(unittest.TestCase):
    def test_capture_saves_unfiltered_wire_stream_and_annotations(self):
        from unittest.mock import patch
        class FakeSerial:
            def __init__(self, data):
                self.data = data
                self.commands = []
            def __enter__(self): return self
            def __exit__(self,*args): pass
            def reset_input_buffer(self): pass
            def write(self,data): self.commands.append(data)
            def read(self,n):
                chunk,self.data = self.data[:311],self.data[311:]
                return chunk
        data = recording([(10000,b'\x01HI'),(100000,b'\x07\x42')])
        fake = FakeSerial(data)
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp)/'live.igcap'
            with patch('tools.infoglobe.serial_open',return_value=fake), \
                 patch('sys.stdin',io.StringIO('/mark observing an unknown effect\n')), \
                 contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(main(['capture','--port','fake','--output',str(output),'--view','unknown']),0)
            self.assertEqual(output.read_bytes(),data)
            report = json.loads(Path(str(output)+'.analysis.json').read_text())
            self.assertEqual(len(report['events']),2)
            self.assertTrue(any(c.startswith(b'mark ') for c in fake.commands))
            self.assertTrue(Path(str(output)+'.notes.jsonl').read_text())

    def test_capture_keeps_partial_recording_on_disconnect(self):
        from unittest.mock import patch
        class DisconnectingSerial:
            def __enter__(self): return self
            def __exit__(self,*args): pass
            def reset_input_buffer(self): pass
            def write(self,data): pass
            def read(self,n): raise OSError('simulated cable disconnect')
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp)/'partial.igcap'
            with patch('tools.infoglobe.serial_open',return_value=DisconnectingSerial()), \
                 patch('sys.stdin',io.StringIO('')),contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(main(['capture','--port','fake','--output',str(output)]),1)
            report = json.loads(Path(str(output)+'.analysis.json').read_text())
            self.assertTrue(any('disconnect' in p for p in report['problems']))

    def test_replay_transmitter_handshake_and_raw_bytes(self):
        from unittest.mock import patch
        class FakeTransmitter:
            def __init__(self): self.commands=[];self.responses=[]
            def __enter__(self): return self
            def __exit__(self,*args): pass
            def reset_input_buffer(self): pass
            def write(self,data):
                self.commands.append(data)
                self.responses.append(b'DONE\n' if data.startswith(b'raw ') else b'OK\n')
            def readline(self): return self.responses.pop(0) if self.responses else b''
        with tempfile.TemporaryDirectory() as temp:
            replay = Path(temp)/'replay.json'
            replay.write_text(json.dumps(dict(format='infoglobe-replay-1',events=[
                dict(start_us=0,bytes=[4,72,73],bit_us=1000,classification='known')])))
            fake = FakeTransmitter()
            with patch('tools.infoglobe.serial_open',return_value=fake),contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(main(['replay',str(replay),'--port','fake']),0)
            self.assertIn(b'raw 04 48 49\n',fake.commands)
            self.assertEqual(fake.commands[-1],b'stop\n')


class RuleTests(unittest.TestCase):
    def test_custom_rules_reclassify_without_altering_capture(self):
        with tempfile.TemporaryDirectory() as temp:
            p=Path(temp)
            source=p/'capture.igcap'
            source.write_bytes(recording([(10000,b'\x07\x10\x42')]))
            rules=[dict(id='test-07',pattern=[7,16,None],classification='known',
                        interpretation='Synthetic rule test',reason='Unit test only',evidence='synthetic')]
            (p/'rules.json').write_text(json.dumps(rules))
            with contextlib.redirect_stdout(io.StringIO()):
                result=main(['analyze',str(source),'--rules',str(p/'rules.json'),'--view','all',
                             '--json',str(p/'result.json')])
            self.assertEqual(result,0)
            event=json.loads((p/'result.json').read_text())['events'][0]
            self.assertEqual(event['classification'],'known')
            self.assertEqual(event['rule_id'],'test-07')
            self.assertIn('+custom-',event['rule_version'])
            # An unmodified reanalysis still treats it as unknown.
            from tools.session import load
            self.assertEqual(load(source).events[0]['classification'],'unknown')

    def test_conflicting_rules_remain_partial(self):
        events=[]
        rule=dict(id='one',pattern=[0],classification='known',reason='test',
                  interpretation='test',evidence='synthetic')
        d=Decoder(events.append,rules=[rule,dict(rule,id='two')])
        d.samples(0,pack_runs([(0,8000),(1,30000)]));d.finish()
        self.assertEqual(events[0]['classification'],'partial')
        self.assertIn('conflicting',events[0]['reason'])


if __name__ == '__main__':
    unittest.main()
