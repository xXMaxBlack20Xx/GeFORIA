"""Fuente simulada opcional, identificada y almacenada por separado."""
import math
import queue
import threading
import time


class DemoWorker(threading.Thread):
    def __init__(self, events, stop_event, commands):
        super().__init__(daemon=True)
        self.events, self.stop_event, self.commands = (events, stop_event, commands)

    def run(self):
        self.events.put(('connected', 'DEMO'))
        index, started = (0, None)
        while not self.stop_event.wait(0.05):
            try:
                while True:
                    if self.commands.get_nowait() == "s":
                        index, started = (0, time.monotonic())
            except queue.Empty:
                pass
            for _ in range(10):
                t = index / 200
                phase = 2 * math.pi * 1.2 * t
                value = math.sin(phase) + 0.23 * math.sin(2 * phase)
                derivative = -(math.sin(phase) + 0.92 * math.sin(2 * phase))
                self.events.put(('muestra', (t, value, derivative)))
                index += 1
            self.events.put(('bpm', 72.0))
            self.events.put(('indices', (-0.42, -0.21)))
            if started is not None and time.monotonic() - started >= 60:
                self.events.put(('resultado', (72.0, True, -0.42, -0.21)))
                started = None
        self.events.put(('disconnected', None))
