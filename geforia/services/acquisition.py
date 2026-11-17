"""Estado y capturas de una sesión, independiente de hardware y UI."""
from collections import deque
import math
from ..config import BUFFER_SIZE, SAVED_SECONDS
from ..models import Capture


class AcquisitionSession:
    def __init__(self):
        self.times = deque(maxlen=BUFFER_SIZE)
        self.values = deque(maxlen=BUFFER_SIZE)
        self.derivatives = deque(maxlen=BUFFER_SIZE)
        self.origin = 'USB'
        self.connected = False
        self.connecting = False
        self.running = False
        self.message = 'Conecta tu ESP32 para comenzar.'
        self.reset()

    def reset(self):
        self.times.clear()
        self.values.clear()
        self.derivatives.clear()
        self.bpm = self.ba = self.agi = None
        self.completed = False
        self.valid = None
        self.capture = None
        self.saved = False
        self.revision = 0

    def start(self):
        if not self.connected or self.running:
            raise ValueError('Conecta el ESP32 y espera antes de iniciar otra prueba.')
        self.reset()
        self.running = True
        self.message = 'Prueba solicitada. Mantén el dedo quieto y espera la respuesta del ESP32.'

    def handle(self, kind: str, payload):
        if kind == "connected":
            self.connected, self.connecting = (True, False)
            self.message = 'Conexión lista. Coloca el dedo e inicia una prueba.'
        elif kind == "muestra":
            t, value, derivative = payload
            if math.isfinite(t) and math.isfinite(value) and not self.completed:
                # El índice puede reiniciarse cuando el firmware comienza la prueba.
                if self.times and t < self.times[-1]:
                    self.times.clear()
                    self.values.clear()
                    self.derivatives.clear()
                self.times.append(t)
                self.values.append(value)
                self.derivatives.append(derivative)
                self.revision += 1
                self.saved = False
        elif kind == "indices" and not self.completed:
            self.ba, self.agi = payload
        elif kind == "bpm" and not self.completed:
            self.bpm = payload
        elif kind == "resultado" and not self.completed:
            bpm, valid, self.ba, self.agi = payload
            self.bpm = bpm if bpm is not None and math.isfinite(bpm) and (0 < bpm < 300) else None
            self.running, self.completed, self.valid = (False, True, valid)
            self.message = 'Prueba terminada · ' + ('calidad válida' if valid else 'revisar calidad')
            self.capture = self.snapshot()
        elif kind == "info":
            self.message = str(payload)[:220]
        elif kind in ("error", "disconnected"):
            self.connected = self.connecting = self.running = False
            self.message = str(payload) if kind == 'error' else 'Desconectado. La última captura se conserva.'

    @property
    def can_save(self):
        return not self.running and (not self.saved) and (self.snapshot() is not None)

    def snapshot(self) -> Capture | None:
        if self.capture is not None:
            return self.capture
        if self.bpm is None or not math.isfinite(self.bpm) or not 0 < self.bpm < 300 or len(self.times) < 2:
            return None
        start = max(self.times[0], self.times[-1] - SAVED_SECONDS)
        samples = [(float(t-start), float(v), float(d) if d is not None and math.isfinite(d) else None)
                   for t, v, d in zip(self.times, self.values, self.derivatives)
                   if t >= start and math.isfinite(t) and math.isfinite(v)]
        if len(samples) < 2 or samples[-1][0] <= samples[0][0]:
            return None
        quality = ('Válida' if self.valid else 'Revisar') if self.completed else 'Pendiente'
        return Capture(self.bpm, self.ba, self.agi, self.origin, quality,
                       tuple(s[0] for s in samples), tuple(s[1] for s in samples), tuple(s[2] for s in samples))

    def save(self, database, profile_id, observations=""):
        if not profile_id or not database.paciente(profile_id):
            raise ValueError('Guarda primero tu expediente personal.')
        if not self.can_save:
            raise ValueError('Se necesita una captura con BPM y señal; espera el final o detén la captura actual.')
        capture = self.snapshot()
        database.guardar_medicion(profile_id, capture.bpm, "FC registrada",
            "Resultados de investigación, sin diagnóstico", capture.origin,
            capture.quality, capture.ba, capture.agi, observations.strip(), senal=capture.signal)
        self.saved = True
        return capture
