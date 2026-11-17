"""Lectura en segundo plano; nunca accede a widgets ni a SQLite."""
import queue
import threading
from ..config import BAUDRATE
from .protocol import LineBuffer, parse_line


def available_ports() -> list[str]:
    try:
        from serial.tools import list_ports
        return [port.device for port in list_ports.comports()]
    except ImportError:
        return []


class SerialWorker(threading.Thread):
    def __init__(self, port, events, stop_event, commands, bluetooth=False):
        super().__init__(daemon=True)
        self.port, self.events, self.stop_event = (port, events, stop_event)
        self.commands, self.bluetooth = (commands, bluetooth)

    def emit(self, event):
        # Solo las muestras se pueden omitir si la UI está saturada.
        # Los resultados y errores no compiten con una cola de muestras ilimitada.
        if event[0] == "muestra" and self.events.qsize() >= 16000:
            return
        self.events.put(event)

    def run(self):
        try:
            import serial
            with serial.Serial(self.port, BAUDRATE, timeout=0.1, write_timeout=0.5) as connection:
                if not self.bluetooth and self.stop_event.wait(1.5):
                    return
                if self.stop_event.is_set():
                    return
                connection.reset_input_buffer()
                connection.write(b'r')
                connection.flush()
                self.emit(('connected', self.port))
                buffer = LineBuffer()
                while not self.stop_event.is_set():
                    while not self.commands.empty():
                        try:
                            command = self.commands.get_nowait()
                        except queue.Empty:
                            break
                        connection.write(command.encode('ascii'))
                        connection.flush()
                    raw = connection.read_until(b'\n', size=4096)
                    for line in buffer.feed(raw):
                        for event in parse_line(line):
                            self.emit(event)
        except ImportError:
            self.emit(('error', 'Falta pyserial. Instala las dependencias con: python -m pip install -r requirements.txt'))
        except (OSError, ValueError) as exc:
            self.emit(('error', str(exc)))
        except Exception as exc:
            # pyserial define SerialException fuera de la biblioteca estándar.
            self.emit(('error', f'No se pudo comunicar con el ESP32: {exc}'))
        finally:
            self.emit(('disconnected', None))
