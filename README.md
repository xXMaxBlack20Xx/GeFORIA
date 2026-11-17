# GeFORIA 3.0

Aplicación de escritorio para un expediente personal, adquisición PPG/SDPTG
desde ESP32 y seguimiento de mediciones y consultas. El proyecto completo
mantiene Tkinter y SQLite. Los índices son exploratorios y proceden del firmware;
la aplicación no emite diagnósticos.

## Empezar

Necesitas **Python 3.10 o superior con Tkinter**, una sesión gráfica y, para
conectar el ESP32, `pyserial`. Extrae todo el ZIP y abre una terminal dentro de
la carpeta `GeFORIA` que contiene `main.py`.

Linux / macOS:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python main.py
```

Windows (PowerShell):

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe main.py
```

Si tu distribución de Linux no incluye Tkinter, instala su paquete de soporte
Tk con el gestor de paquetes de tu sistema. Puedes comprobarlo con
`python3 -m tkinter`: debe abrir una ventana. Las bibliotecas gráficas requieren
una sesión de escritorio; una terminal remota sin pantalla no es suficiente.

La interfaz puede abrirse sin `pyserial`; al intentar conectar el dispositivo
indicará que hay que instalarlo. No necesita NumPy, Matplotlib ni SciPy para
mostrar las gráficas. `requirements-optional.txt` permite instalar SciPy solo
si vas a utilizar el helper de filtrado exploratorio por separado.

## Flujo de uso

1. **Mis datos:** escribe nombre y edad. El código ya está generado; puedes
   personalizarlo antes del primer guardado. Puedes guardar inmediatamente o
   completar Salud y Revisar. Los campos opcionales pueden quedar vacíos.
2. **Medición:** conecta el ESP32, elige USB o Bluetooth SPP, selecciona o escribe
   su puerto y pulsa Conectar. Apoya la mano, coloca el dedo e inicia la prueba.
   El ESP32 confirma la finalización y comunica la calidad. Revisa y guarda.
3. **Historial:** busca estudios por fecha, conexión o texto, abre su detalle y
   señal, registra una consulta o elimina una medición seleccionada.

El borrador del expediente se conserva entre secciones. Al avanzar se validan
los campos pertinentes y los errores se muestran junto a cada entrada. Para
editar, abre Mis datos, modifica la información y confirma la actualización.
El código queda bloqueado después del alta para no mezclar historiales.

La información de salud no se autocompleta con valores supuestos. Los rangos de
captura proceden de la versión anterior y no representan umbrales diagnósticos.

Si necesitas una captura parcial, pulsa **Desconectar** y luego **Guardar captura
actual**. Se necesita BPM y al menos dos muestras válidas. Se confirmará que no
hay resultado final. Desconectar cierra la adquisición del ordenador; no envía
al firmware un comando de cancelación que su protocolo no define.

## Datos anteriores

Por defecto se sigue usando `~/GeFORIA/registros.sqlite3`. No se incluye ninguna
base personal en el ZIP. La primera apertura de una base anterior crea un
respaldo en su subcarpeta `backups` antes de aplicar la migración compatible.
Se mantienen tablas, columnas heredadas y señales JSON comprimidas con zlib.
La migración se ejecuta dentro de una transacción.

Si la base contiene expedientes pero no tiene uno activo configurado, Mis datos
ofrece un selector para recuperar el tuyo. No crea otro expediente encima de un
código existente. Si la base está en otra carpeta:

```bash
python main.py --data-dir /ruta/a/la/carpeta-de-datos
```

El botón **Crear respaldo** permite guardar otra copia SQLite completa.
La restauración se describe en [docs/MIGRACION.md](docs/MIGRACION.md).

## Probar sin el ESP32

```bash
python main.py --demo
```

El modo de demostración es opcional y adicional a la conexión real. Está
identificado en la ventana, usa origen `DEMO` y escribe siempre en la subcarpeta
`demo` de la carpeta de datos elegida. No mezcla sus muestras con el expediente
normal. Elige el puerto `DEMO`, conecta e inicia una prueba. La simulación
también tarda 60 s; sus índices son valores ficticios.

## Conexión real

- Firmware existente: `ppg_sdptg_V3.ino`, **921600 baudios** y 200 muestras/s.
- USB puede reiniciar el ESP32; la aplicación espera su arranque.
- Bluetooth requiere un puerto serie **SPP** emparejado por el sistema;
  esta aplicación no es un cliente BLE.
- Puerto: por ejemplo, `COM4` en Windows o `/dev/ttyUSB0` en Linux. Son ejemplos,
  no valores fijados. Selecciona el dispositivo real.
- Comandos conservados: `r` activa el flujo; `s` solicita la prueba de 60 s.
- El firmware controla la estabilidad y finalización. El tiempo mostrado en la
  ventana es desde la solicitud; no afirma que el sensor ya esté midiendo.

El archivo `.ino` no formaba parte del código recibido. No se reprograma ni se
sustituye el firmware y no se recalculan BPM, b/a ni AGI en el ordenador.

## Teclado y distribución

Tab / Shift+Tab recorren los controles; los campos de texto también permiten
salir con Tab. Ctrl+S guarda la página activa. Alt+1, Alt+2 y Alt+3 cambian de
sección. Las tablas admiten selección por teclado y Enter para abrir el detalle.
Los campos y tablas tienen desplazamiento; los botones principales permanecen
fuera del área desplazable. La interfaz está orientada a escritorio, con una
ventana mínima aproximada de 960 × 680 según la pantalla disponible.

## Estructura

| Ruta | Responsabilidad |
| --- | --- |
| `main.py` | Entrada, argumentos y mensajes de arranque. |
| `geforia/app.py` | Composición de servicios, navegación y ciclo de vida de la ventana. |
| `geforia/config.py` | Configuración y constantes. |
| `geforia/models.py` | Perfil y captura inmutables. |
| `geforia/validation.py` | Reglas y errores por campo. |
| `geforia/persistence/database.py` | SQLite, migración, respaldos, señales y consultas. |
| `geforia/services/` | Casos de uso, protocolo, comunicación y estado de adquisición. |
| `geforia/ui/` | Vistas, widgets, estilos y gráficas. |
| `tests/` | Pruebas del núcleo, servicios y flujos gráficos. |
| `docs/` | Auditoría, arquitectura, migración y resultados de validación. |

## Pruebas

```bash
python -m unittest discover -s tests -v
```

La suite usa únicamente `unittest`. Las pruebas de widgets se omiten
explícitamente cuando no hay pantalla gráfica accesible. Consulta
[docs/VALIDACION.md](docs/VALIDACION.md) para conocer qué se ejecutó durante
esta entrega y qué requiere el equipo real.

## Solución de problemas

- **No abre una ventana:** comprueba Tkinter y ejecuta desde una sesión gráfica.
- **No encuentra puertos:** instala `requirements.txt`, conecta el dispositivo y
  revisa en el sistema operativo que el puerto exista y tengas acceso.
- **Puerto ocupado:** cierra el monitor serie u otra instancia que use el ESP32.
- **Bluetooth sin muestras:** confirma que sea el puerto SPP saliente y que el
  firmware corresponda al protocolo S/B/R.
- **No permite guardar:** crea el expediente y espera el resultado; si deseas
  guardar una captura parcial, desconecta primero.
- **Error de base de datos:** lo escrito se conserva en pantalla; verifica
  permisos y espacio antes de reintentar. No borres la base para resolverlo.

No se implementa un exportador de documentos porque la versión recibida no
incluía esa función. El respaldo SQLite sí conserva todos los registros.
