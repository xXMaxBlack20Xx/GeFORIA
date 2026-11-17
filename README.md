# GeFORIA 3.0

Aplicación de escritorio para un expediente personal, adquisición PPG/SDPTG
desde ESP32 y seguimiento de mediciones y consultas. El proyecto completo
mantiene Tkinter y SQLite. Los índices son exploratorios y proceden del firmware;
la aplicación no emite diagnósticos.

## Empezar

Necesitas **Python 3.10 o superior con Tkinter**, una sesión gráfica y, para
conectar el ESP32, `pyserial`. Extrae todo el ZIP y abre una terminal dentro de
la carpeta `GeFORIA` que contiene `main.py`.

### Windows: abrir con doble clic

Sigue **[GUIA_WINDOWS.md](GUIA_WINDOWS.md)**: explica la descarga, extracción e
instalación de Python paso a paso, sin necesitar conocimientos de programación.

1. [Descarga el ZIP de main](https://github.com/xXMaxBlack20Xx/GeFORIA/archive/refs/heads/main.zip)
   y **extrae todo** su contenido.
2. Instala Python 3.10 o posterior con Tkinter desde
   [python.org](https://www.python.org/downloads/windows/).
3. Haz doble clic en **`iniciar_geforia.bat`**.
   Para probar sin sensor, abre **`iniciar_demo.bat`**.

La primera preparación requiere Internet para crear `.venv-windows` e instalar
los complementos. Las siguientes aperturas reutilizan ese entorno; si una
preparación falla, el siguiente intento la reanuda. Los errores permanecen
visibles. No hacen falta permisos de administrador ni activar un entorno
manualmente. El entorno de Fedora `.venv` se conserva por separado.

Los dos BAT aceptan argumentos, por ejemplo desde PowerShell:

```powershell
.\iniciar_demo.bat --data-dir "$env:TEMP\GeFORIA prueba"
```

La demo muestra datos ficticios. La medición real exige el ESP32 con su sensor
y firmware compatible; el firmware no se incluye ni se instala con el lanzador.

### Fedora Linux

Preparación inicial (si los paquetes ya están instalados, no hay que reinstalarlos):

```bash
sudo dnf install python3 python3-pip python3-tkinter
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
```

Desde una terminal de tu sesión de escritorio, abre la aplicación con:

```bash
./iniciar_geforia.sh
```

El lanzador utiliza `.venv/bin/python`, no requiere activar el entorno y acepta
los mismos argumentos que `main.py`. También funciona desde otra carpeta:

```bash
/ruta/a/GeFORIA/iniciar_geforia.sh --demo
```

Si al extraer el ZIP se perdió el permiso de ejecución, usa
`chmod +x iniciar_geforia.sh` o `bash iniciar_geforia.sh`. **No ejecutes GeFORIA
con `sudo`**. Para comprobar Tkinter con el intérprete correcto:

```bash
.venv/bin/python -m tkinter
```

Debe aparecer una ventana. Tkinter se instala con `dnf`, no con `pip`; para un
Python distinto del incluido en Fedora necesitas el soporte Tk de ese intérprete.
Una conexión SSH sin acceso a la pantalla no basta.

Para probar sin utilizar tu carpeta personal de datos:

```bash
./iniciar_geforia.sh --demo --data-dir "$(mktemp -d -t geforia-prueba.XXXXXX)"
```

La demostración guardará sus datos ficticios en `demo/` dentro de esa carpeta
temporal. Un `--data-dir` relativo se interpreta desde la carpeta donde invoques
el lanzador.

### Otros sistemas

Linux / macOS:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python main.py
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
| `iniciar_geforia.bat` / `iniciar_demo.bat` | Doble clic en Windows, preparación y modo demo. |
| `iniciar_geforia.sh` | Lanzador para el entorno de Fedora/Linux. |
| `GUIA_WINDOWS.md` | Guía de descarga, instalación y uso para principiantes. |
| `geforia/windows_launcher.py` | Entorno Windows independiente, comprobaciones y reintento de preparación. |
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
.venv/bin/python -m unittest discover -s tests -v
```

En Windows, después de la primera preparación:

```powershell
.\.venv-windows\Scripts\python.exe -m unittest discover -s tests -v
```

La suite usa únicamente `unittest`. Las pruebas de widgets se omiten
explícitamente cuando no hay pantalla gráfica accesible. La regresión de
arranque abre la ventana en modo normal y demo, recorre las tres secciones,
redimensiona y cierra; tiene un límite de tiempo para detectar bloqueos de Tk.
Las pruebas específicas de BAT solo se ejecutan en Windows; su omisión en Linux
no acredita que el lanzador funcione en Windows. Consulta
[docs/VALIDACION.md](docs/VALIDACION.md) para conocer qué se ejecutó durante
esta entrega y qué requiere el equipo real.

## Solución de problemas

- **Windows:** consulta primero [GUIA_WINDOWS.md](GUIA_WINDOWS.md#si-algo-no-funciona).
- **Fedora, no abre una ventana:** ejecuta `./iniciar_geforia.sh` desde una terminal para
  ver el error y comprueba `.venv/bin/python -m tkinter`. Esta versión corrige
  un ciclo de redimensionado de las ayudas del formulario que podía bloquear Tk
  antes de mostrar la ventana; no se soluciona borrando los datos.
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
