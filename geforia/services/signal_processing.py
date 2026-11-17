"""Filtrado exploratorio conservado. La UI grafica lo transmitido por el ESP32."""
import math
from statistics import median


def moving_average(values: list[float], width: int) -> list[float]:
    width = max(1, min(int(width), len(values)))
    if width <= 1:
        return list(values)
    left, right = (width // 2, width - 1 - width // 2)
    padded = [values[0]] * left + list(values) + [values[-1]] * right
    total = sum(padded[:width])
    result = [total / width]
    for index in range(width, len(padded)):
        total += padded[index] - padded[index - width]
        result.append(total / width)
    return result


def filtrar_ppg(t, y) -> list[float]:
    """Banda 0.5–8 Hz si SciPy está disponible; alternativa de medias móviles.

    Devuelve una lista, no modifica los datos y no calcula índices clínicos.
    No necesita NumPy/SciPy para utilizarse.
    """
    times, values = (list(map(float, t)), list(map(float, y)))
    zeros = [0.0] * len(values)
    if len(times) != len(values) or len(values) < 15 or not all(map(math.isfinite, values)):
        return zeros
    deltas = [b - a for a, b in zip(times, times[1:]) if math.isfinite(b - a) and b > a]
    if not deltas:
        return zeros
    fs = 1 / median(deltas)
    if not 5 <= fs <= 1000:
        return zeros
    high = min(8.0, fs * 0.42)
    if len(values) >= max(40, int(fs * 0.6)):
        try:
            from scipy.signal import butter, sosfiltfilt
            sos = butter(2, [0.5, high], btype='bandpass', fs=fs, output='sos')
            return sosfiltfilt(sos, values).tolist()
        except (ImportError, ValueError, FloatingPointError):
            pass
    trend = moving_average(values, max(3, int(fs / 0.5)))
    return moving_average([v - m for v, m in zip(values, trend)], max(1, int(fs / (2 * high))))
