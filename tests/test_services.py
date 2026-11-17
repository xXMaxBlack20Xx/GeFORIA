import queue
import threading
import time
import types
import unittest
from unittest.mock import patch
from geforia.services.connection_manager import ConnectionManager
from geforia.services.serial_connection import SerialWorker
from geforia.validation import make_profile


class ServiceIntegrationTests(unittest.TestCase):
    def test_numeric_zero_age_is_preserved(self):
        profile = make_profile({'id': 'A', 'nombre': 'Persona', 'edad': 0})
        self.assertEqual(profile.edad, 0)

    def test_serial_worker_commands_fragments_result_and_shutdown(self):
        events, commands = (queue.Queue(), queue.Queue())
        stop = threading.Event()
        commands.put('s')
        chunks=iter([b'S,200,123,',b'.5,0\n',b'B,0,0,0,0,0,0,-.4,-.2,72\n',
                     b'R,0,72,-.4,0,0,0,0,0,-.2,0,0,0,0,1\n'])
        class FakeSerial:
            written = []
            def __init__(self,*args,**kwargs):
                self.args, self.kwargs = (args, kwargs)
                self.__class__.instance = self
            def __enter__(self):
                return self
            def __exit__(self,*args):
                pass
            def reset_input_buffer(self):
                pass
            def write(self,value):
                self.written.append(value)
            def flush(self):
                pass
            def read_until(self,*args,**kwargs):
                try:
                    return next(chunks)
                except StopIteration:
                    stop.set()
                    return b''
        with patch.dict('sys.modules',{'serial':types.SimpleNamespace(Serial=FakeSerial)}):
            worker = SerialWorker('TEST', events, stop, commands, bluetooth=True)
            worker.start()
            worker.join(timeout=2)
        self.assertFalse(worker.is_alive())
        self.assertEqual(FakeSerial.written, [b'r', b's'])
        self.assertEqual(FakeSerial.instance.args, ('TEST', 921600))
        received = list(events.queue)
        self.assertIn(('resultado', (72.0, True, -0.4, -0.2)), received)
        self.assertIn(('muestra', (1.0, 0.5, 0.0)), received)
        self.assertEqual(received[-1], ('disconnected', None))

    def test_missing_dependency_is_a_readable_event(self):
        events = queue.Queue()
        with patch.dict('sys.modules',{'serial':None}):
            worker = SerialWorker('TEST', events, threading.Event(), queue.Queue())
            worker.run()
        self.assertEqual(events.get()[0], 'error')
        self.assertEqual(events.get(), ('disconnected', None))

    def test_demo_can_stream_and_disconnect_without_hardware(self):
        manager = ConnectionManager(demo=True)
        try:
            manager.connect('DEMO')
            deadline = time.monotonic() + 2
            received = []
            while time.monotonic()<deadline and not any(kind=='muestra' for kind,_ in received):
                time.sleep(0.02)
                received.extend(manager.drain())
            self.assertTrue(any((kind == 'connected' for kind, _ in received)))
            self.assertTrue(any((kind == 'muestra' for kind, _ in received)))
            manager.start_test()
        finally:
            manager.disconnect()
            if manager.worker:
                manager.worker.join(timeout=2)
        self.assertFalse(manager.busy)
        self.assertEqual(list(manager.drain()), [])

    def test_reconnect_cannot_overlap_old_worker(self):
        manager = ConnectionManager(demo=True)
        try:
            manager.connect('DEMO')
            with self.assertRaises(ValueError):
                manager.connect('DEMO')
        finally:
            manager.disconnect()
            manager.worker.join(timeout=2)


if __name__=='__main__':
    unittest.main()
