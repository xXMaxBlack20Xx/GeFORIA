"""Dos gráficas Tk Canvas; no recalculan ni suavizan las señales del ESP32."""
import math
import tkinter as tk
from tkinter import ttk
from ..config import VISIBLE_SECONDS
from . import theme


class SignalPlot(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent, style='Card.TFrame')
        self.data = ([], [], [])
        self.canvases = []
        for title, color in (("PPG filtrada · ESP32", theme.TEAL), ("SDPTG · segunda derivada del ESP32", "#7D4DB5")):
            canvas = tk.Canvas(self, background=theme.SURFACE, highlightthickness=0,
                               height=155, takefocus=False)
            canvas.pack(fill='both', expand=True, pady=(0, 4))
            canvas.bind('<Configure>', lambda e: self.draw())
            self.canvases.append((canvas, title, color))

    def set_data(self, times, values, derivatives):
        self.data = (list(times), list(values), list(derivatives))
        self.draw()

    def draw(self):
        times, values, derivatives = self.data
        for (canvas, title, color), series in zip(self.canvases, (values, derivatives)):
            canvas.delete('all')
            width, height = (canvas.winfo_width(), canvas.winfo_height())
            if width < 100 or height < 75:
                continue
            left, top, right, bottom = (65, 32, width - 18, height - 28)
            canvas.create_text(14, 12, text=title, fill=theme.TEXT, anchor='w', font=(theme.FONT, 10, 'bold'))
            canvas.create_text(right, 12, text='Amplitud (u.a.)', fill=theme.MUTED, anchor='e', font=(theme.FONT, 8))
            end = max(VISIBLE_SECONDS, times[-1]) if times else VISIBLE_SECONDS
            start = max(0.0, end - VISIBLE_SECONDS)
            visible = [(t, v) for t, v in zip(times, series) if t >= start]
            finite = [v for _, v in visible if v is not None and math.isfinite(v)]
            lo, hi = (min(finite), max(finite)) if finite else (-1.0, 1.0)
            margin = max((hi - lo) * 0.12, 0.01)
            lo, hi = (lo - margin, hi + margin)
            for fraction in (0, .5, 1):
                y = top + (bottom - top) * fraction
                canvas.create_line(left, y, right, y, fill='#E4ECEF')
                canvas.create_text(left-7, y, text=f"{hi - fraction*(hi-lo):.2g}", anchor="e",
                                    fill=theme.MUTED, font=(theme.FONT, 8))
            for fraction in (0, .25, .5, .75, 1):
                x = left + (right - left) * fraction
                canvas.create_line(x, top, x, bottom, fill='#EDF2F4')
                canvas.create_text(x, bottom+13, text=f"{start + fraction*VISIBLE_SECONDS:.1f}s",
                                   fill=theme.MUTED, font=(theme.FONT, 8))
            if not finite:
                canvas.create_text((left+right)/2, (top+bottom)/2,
                    text="Esperando señal…" if not times else "Sin valores D2 disponibles",
                    fill=theme.MUTED, font=(theme.FONT, 10))
                continue
            # Agrupación por píxel con extremos, conservando picos y huecos.
            buckets, bucket, previous_x = ([], [], None)
            for t, v in visible:
                x = left + (t - start) / VISIBLE_SECONDS * (right - left)
                if v is None or not math.isfinite(v):
                    if bucket:
                        buckets.extend(self._extremes(bucket))
                        bucket = []
                    buckets.append(None)
                    previous_x = None
                    continue
                point = (x, bottom - (v - lo) / (hi - lo) * (bottom - top))
                pixel = int(x)
                if previous_x is not None and pixel != previous_x and bucket:
                    buckets.extend(self._extremes(bucket))
                    bucket = []
                bucket.append(point)
                previous_x = pixel
            if bucket:
                buckets.extend(self._extremes(bucket))
            segment = []
            for point in buckets + [None]:
                if point is None:
                    if len(segment)>=4:
                        canvas.create_line(*segment, fill=color, width=1.6)
                    segment = []
                else:
                    segment.extend(point)

    @staticmethod
    def _extremes(points):
        indices = sorted({0, len(points)-1,
                          min(range(len(points)), key=lambda i: points[i][1]),
                          max(range(len(points)), key=lambda i: points[i][1])})
        return [points[i] for i in indices]
