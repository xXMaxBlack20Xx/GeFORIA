"""Parser puro del firmware ppg_sdptg_V3.ino: S/B/R y mensajes #."""
import math
from ..config import SAMPLE_RATE


class LineBuffer:
    """Conserva mensajes partidos por un timeout sin acumular líneas ilimitadas."""
    def __init__(self):
        self.pending = b''
        self.discarding = False

    def feed(self, raw: bytes) -> list[str]:
        lines = []
        for part in raw.splitlines(keepends=True):
            if not self.discarding:
                self.pending += part
                if len(self.pending) > 4096:
                    self.pending = b''
                    self.discarding = True
            if part.endswith(b"\n"):
                if not self.discarding:
                    lines.append(self.pending.decode('utf-8', errors='replace'))
                self.pending = b''
                self.discarding = False
        return lines


def finite_or_none(value: str) -> float | None:
    number = float(value)
    return number if math.isfinite(number) else None


def parse_line(line: str) -> list[tuple[str, object]]:
    line = line.strip()
    if not line:
        return []
    if line.startswith("#"):
        return [('info', line[1:].strip())]
    parts = line.split(',')
    try:
        if parts[0] == "S" and len(parts) >= 5:
            index, value, derivative = (int(parts[1]), float(parts[3]), float(parts[4]))
            if index >= 0 and math.isfinite(value):
                return [("muestra", (index / SAMPLE_RATE, value,
                         derivative if math.isfinite(derivative) else float("nan")))]
        elif parts[0] == "B" and len(parts) >= 10:
            ba, agi, bpm = (finite_or_none(parts[i]) for i in (7, 8, 9))
            events = [('indices', (ba, agi))]
            if bpm is not None and 0 < bpm < 300:
                events.append(('bpm', bpm))
            return events
        elif parts[0] == "R" and len(parts) >= 15:
            bpm, ba, agi = (finite_or_none(parts[i]) for i in (2, 3, 9))
            return [('resultado', (bpm, parts[14].strip() == '1', ba, agi))]
    except (ValueError, OverflowError):
        pass
    return []
