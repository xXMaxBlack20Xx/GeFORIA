"""Ciclo de vida de una conexión y aislamiento de sus eventos."""
import queue
import threading
from .serial_connection import SerialWorker
from .demo import DemoWorker


class ConnectionManager:
    def __init__(self, demo=False):
        self.demo = demo
        self.worker = None
        self.events = queue.Queue()
        self.commands = queue.Queue()
        self.stop_event = threading.Event()
        self.accept_events = False

    @property
    def busy(self):
        return self.worker is not None and self.worker.is_alive()

    def connect(self, port: str, bluetooth=False):
        if self.busy:
            raise ValueError('La conexión anterior se está cerrando. Espera un momento.')
        self.events, self.commands = (queue.Queue(), queue.Queue())
        self.stop_event = threading.Event()
        self.accept_events = True
        self.worker = (DemoWorker(self.events, self.stop_event, self.commands) if self.demo else
                       SerialWorker(port, self.events, self.stop_event, self.commands, bluetooth))
        self.worker.start()

    def disconnect(self):
        self.accept_events = False
        self.stop_event.set()

    def start_test(self):
        if not self.busy or self.stop_event.is_set():
            raise ValueError('La conexión no está lista.')
        self.commands.put('s')

    def drain(self):
        for _ in range(1200):
            try:
                event = self.events.get_nowait()
            except queue.Empty:
                break
            if self.accept_events:
                yield event
