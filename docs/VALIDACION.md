# Validación de la entrega

## Ejecutado

| Comprobación | Resultado |
| --- | --- |
| Compilación de todos los módulos Python | Correcta. |
| Importación de los 21 submódulos de `geforia` | Correcta, sin abrir base de datos ni ventana al importar. |
| Suite del núcleo y servicios | 43 pruebas satisfactorias. |
| Validaciones | Obligatorios, decimales con coma, edad, límites, números no finitos, presión e ID fijo. |
| Persistencia | Alta, edición, expediente activo, claves externas, consultas y eliminación sin huérfanos. |
| Compatibilidad | Migración de esquema antiguo, conservación de `grasa` y estudios, respaldo e idempotencia. |
| Señales | JSON/zlib, valores D2 ausentes, ventana de 30 s y rechazo de señales inconsistentes. |
| Adquisición | Calidad, congelación del resultado, BPM final inválido, captura parcial, reinicio temporal y duplicados. |
| Parser | S/B/R, índices, mensajes inválidos, fragmentos entre lecturas y recuperación de líneas largas. |
| Transporte | Hilo con puerto simulado: comandos r/s, 921600 baudios, fragmentos y desconexión. |
| Fuente demo | Emite muestras, recibe comandos y se detiene sin hardware. |
| `python main.py --help` | Correcto. |
| Intento de arranque gráfico | No disponible: Tk no puede conectarse a una pantalla en este entorno. El programa informa el error. |

La salida de la suite se incluye en `test-results.txt`.

## No ejecutado

- **Inspección visual y flujos con widgets reales:** no hay pantalla accesible.
  `test_ui.py` contiene ocho pruebas de creación de ventana, navegación sin
  pérdida, errores, pasos, guardado, cancelación de actualización, consulta y
  detalle de señal. `unittest` omite la clase completa con un motivo explícito.
- **ESP32 físico:** no había dispositivo ni firmware `.ino` adjunto. No se ha
  probado una medición real de 60 s, la calidad del sensor, USB o Bluetooth SPP.
- **Instalación de pyserial:** el entorno bloquea la resolución de red. El
  transporte se validó mediante un puerto simulado; no se afirma que se haya
  instalado o ejecutado la dependencia real aquí.
- **Windows, macOS y diferentes escalas de pantalla:** no ejecutados. La
  adaptación se implementó con tamaños flexibles y desplazamiento, pero queda
  pendiente su inspección visual en los equipos destino.
- **Tu base personal:** no se modificó. Las pruebas utilizaron datos ficticios.
- **SciPy opcional:** se probó la alternativa de biblioteca estándar. El filtro
  SciPy no se ejecutó porque no estaba instalado.

## Verificación recomendada en el equipo destino

1. Instalar los requisitos y ejecutar `python main.py --demo`.
2. Ejecutar la suite con una sesión gráfica; deben correr también las ocho
   pruebas de widgets. Revisar formularios a 960 × 680 y una resolución mayor.
3. Crear nombre y edad, escribir un dato inválido, corregirlo y navegar de ida y
   vuelta. Guardar y editar; cancelar una actualización y comprobar el borrador.
4. Conectar el modo demo, iniciar una prueba, esperar el resultado, guardar y
   abrir la señal desde Historial. Registrar una consulta y leer sus notas.
5. Abrir primero una copia de la base anterior y comprobar estudios y consultas.
6. Conectar el ESP32 real por USB y después por Bluetooth SPP, hacer una prueba
   completa en cada caso y comprobar los índices frente a la salida del firmware.

La aplicación entregada incluye la implementación real del puerto serie y la
persistencia; el modo demo es una ayuda opcional para validar la experiencia.
Estas limitaciones de verificación no se presentan como pruebas superadas.

## Mejoras futuras

Pruebas de usabilidad con participantes, ajuste visual según el equipo real,
ensayos automatizados con firmware y hardware, paginación de historiales de más
de 1000 estudios y exportaciones de datos si se define su formato.
