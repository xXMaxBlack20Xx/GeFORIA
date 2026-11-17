# Validación de GeFORIA · 2026-11-16

## Entrega para Windows: comprobaciones de publicación

- Remoto verificado: `https://github.com/xXMaxBlack20Xx/GeFORIA.git`, rama `main`.
  Repositorio público, comprobado tanto por la API como sin iniciar sesión.
  No se modificaron los permisos de acceso.
- Revalidación en Fedora: **71 pruebas, 66 satisfactorias y 5 omitidas** porque
  requieren `cmd.exe` y Python de Windows. Las ocho pruebas de widgets reales y
  la regresión de arranque normal/demo sí se ejecutaron.
- Diez pruebas de preparación Windows: instalación inicial, reutilización,
  requisitos modificados, marca dañada, entorno parcial, recuperación de pip,
  fallo de instalación y reintento, dependencia ausente, error Tk y argumentos.
  Utilizan procesos simulados: **no acreditan ejecución en Windows**.
- Se reabrieron los comandos reales `main.py --data-dir CARPETA_TEMPORAL` y
  `iniciar_geforia.sh --demo --data-dir CARPETA_TEMPORAL` desde otra carpeta.
  Ventanas en estado `Normal`, cierre por el gestor de ventanas y salida 0.
- Los 22 submódulos y `main` se importan sin crear una raíz Tk. Bash pasa
  `bash -n`; `.gitignore` excluye entornos, bases, respaldos, cachés y logs.
- BAT con rutas entre comillas, expansión retardada desactivada, argumentos
  conservados, mensajes con pausa y finales de línea CRLF conservados en el ZIP.
  La preparación escribe su marca únicamente después de comprobar el entorno.
  Nunca se borra una base ni se usa el entorno `.venv` de Fedora.
- Descarga pública real del ZIP de `main`: 49 archivos, todas las sumas del
  manifiesto verificadas y BAT con CRLF. Sin entornos virtuales ni bases.
  La guía pública respondió HTTP 200 y coincide con el archivo entregado.

### Windows nativo: ejecución satisfactoria en GitHub Actions

**Resultado: correcto en ambos trabajos** de
[Windows CI](https://github.com/xXMaxBlack20Xx/GeFORIA/actions/runs/44036623481),
sobre el código del commit `6b86f79713a5c1da38065bd18fc5dabe0ce60558`.

| Entorno Windows | Ventana Tk real | Suite completa |
| --- | --- | --- |
| Python 3.12, Tcl 8.6.15 | Visible | 71 pruebas: 68 satisfactorias, 3 de Bash omitidas; 30,131 s. |
| Python 3.14, Tcl 9.0.4 | Visible | 71 pruebas: 68 satisfactorias, 3 de Bash omitidas; 34,521 s. |

En ambos trabajos pasaron las ocho pruebas de widgets y las cinco pruebas
reales de BAT. En particular, `iniciar_demo.bat` preparó su entorno, ejecutó
la entrada real, mostró Mis datos, Medición e Historial y cerró correctamente.
La prueba solo añadió una verificación y un cierre programados a la entrada,
sin simular los widgets, servicios ni la base de datos; usó `--data-dir`
temporal. También pasaron instalación inicial, reutilización sin reinstalar,
argumentos, descarga incompleta, Python no encontrado y reintento tras un error.
Se verificaron las 48 sumas del manifiesto y los CRLF de ambos BAT.

La actualización posterior a este commit solo registra resultados y actualiza
documentación y manifiesto; no cambia el código validado. Las omisiones en
Windows corresponden exclusivamente al lanzador Bash, comprobado en Fedora.

#### Incidencia de la primera ejecución

El equipo local es Fedora. La primera ejecución nativa en GitHub Actions
([registro](https://github.com/xXMaxBlack20Xx/GeFORIA/actions/runs/44035752893))
mostró las ventanas y pasó las ocho pruebas de widgets en Windows con Python
3.12 y 3.14. La suite detectó una comparación incorrecta de la prueba del BAT:
`RUNNER~1` y `runneradmin` representaban el mismo archivo con rutas distintas.
Se corrigió utilizando identidad de archivo (`samefile`), sin eliminar la
comprobación de que se utiliza el intérprete del entorno.

El workflow `.github/workflows/windows.yml` exige una ventana Tk visible,
verifica el manifiesto y ejecuta los BAT con `cmd.exe`: instalación, reutilización,
rutas con espacios y `!`, recuperación tras un error y apertura de la interfaz
real a través de `iniciar_demo.bat`, con navegación y cierre programados.
La primera ejecución fallida no se contabiliza como satisfactoria; los
resultados correctos corresponden a la ejecución posterior enlazada arriba.

#### Límites

CI ejecuta Windows real, pero no sustituye una prueba manual de doble clic en el
equipo particular del destinatario ni de sus permisos o controladores USB.
Tampoco acredita adquisición con un ESP32 físico ni el firmware que lleva
instalado el dispositivo. No se abrió ni modificó la base personal del usuario.

---

## Registro de la reparación anterior en Fedora

### Entorno comprobado

Fedora Workstation 45, usuario sin privilegios, Python 3.15.2 de `.venv`,
Tcl/Tk 9.0.4 y pyserial 3.5. Sesión Wayland con Tk a través de Xwayland
(`DISPLAY=:0`). Una ventana Tk independiente se mostró correctamente.
Los paquetes `python3-tkinter`, `tk` y `tcl` ya estaban instalados: no fue
necesario instalar dependencias ni ejecutar la aplicación como root.

### Causa reproducida y reparación

Se ejecutó `.venv/bin/python main.py --data-dir CARPETA_TEMPORAL`. El proceso
seguía vivo a los 15 s, sin salida ni excepción, pero la ventana no se mostraba.
El volcado de pilas situó el bloqueo en el bucle de eventos Tk. El registro de
eventos contó miles de `<Configure>` repetidos, con la raíz sin mapear y tamaño
`1x1`.

En `geforia/ui/widgets.py`, `label()` ajustaba la ayuda al ancho del padre
menos 32 píxeles y `FormField` añadía otro manejador que la ajustaba al ancho
completo. Estos cambios contradictorios de `wraplength` alteraban el tamaño
solicitado del formulario y volvían a disparar el cálculo de geometría dentro
del canvas, antes de que este fijara el ancho visible. Tk nunca terminaba el
trabajo de geometría necesario para mostrar la ventana.

Se eliminó el manejador duplicado y se fijó el ancho inicial de la ventana
interna del canvas; desde el primer `<Configure>` lo controla el viewport.
Sin cambiar datos ni dependencias, las tres páginas pudieron mostrarse.
La prueba de regresión falló por timeout en modo normal y demo con el código
original y pasó con la corrección.

También se detectaron `ResourceWarning` de SQLite: el contexto de una conexión
gestiona transacciones, pero no la cierra. Los destinos de respaldos manuales y
previos a la migración ahora se cierran explícitamente con `closing()`.
No se modificaron el esquema, las señales, las validaciones ni el protocolo.

### Resultados de la reparación anterior

```bash
.venv/bin/python -m unittest discover -s tests -v
```

**56 pruebas satisfactorias, sin omisiones ni advertencias** en esa comprobación.
La salida de la revalidación más reciente se conserva en
[test-results.txt](test-results.txt).

| Comprobación | Resultado |
| --- | --- |
| Importaciones | Los 21 submódulos de `geforia` y `main`, sin crear una raíz Tk. |
| Arranque del comando real `main.py` | Ventana reconocida por el gestor gráfico como `Normal`; cierre `WM_DELETE_WINDOW`, salida 0 y sin errores. |
| Lanzador desde otra carpeta | Mismo resultado con `iniciar_geforia.sh --demo --data-dir CARPETA_TEMPORAL`. |
| Regresión de arranque | Modo normal/demo, tres páginas visibles, cambio a 960 × 680 y cierre; proceso con timeout de 10 s. |
| Widgets reales | Alta ficticia, validaciones, revisión, cancelación de edición, consulta y detalle de señal. |
| Borrador | Nombre, edad, peso y notas conservados al navegar por Mis datos, Medición e Historial. |
| Lanzador | Python local, rutas con espacios, argumentos intactos y mensajes si falta el entorno o `main.py`. |
| Persistencia | Migración y respaldo de una base antigua ficticia, registros heredados, señales zlib, consultas y claves externas. |
| Respaldos SQLite | Destino cerrado explícitamente; prueba de regresión y comprobación con `ResourceWarning` habilitado. |
| Protocolo y transporte simulado | S/B/R, comandos `r`/`s`, 921600 baudios, fragmentación y desconexión. |

### Demostración gráfica completa anterior, adicional a la suite

Se ejecutó la fuente demo **sin acelerar su reloj**: terminó a los 60,17 s.
Se guardaron un expediente ficticio, una medición `DEMO` con **6.001 muestras**
(30 s) y una consulta. Se abrió el detalle con la señal, se desconectó el hilo
y se cerró la ventana mediante `App.close()`. Se comprobó que la conexión
principal quedaba cerrada. La reapertura conservó los registros y
`PRAGMA integrity_check` devolvió `ok`.

Se inspeccionaron capturas de las tres secciones en la sesión gráfica real.
Los datos y capturas de esta comprobación quedaron únicamente en
`/tmp/opencode/geforia-demo-verificada-e_odp1da/`; los arranques por terminal
también utilizaron `--data-dir` temporal. No se abrió ni se alteró la base
personal `~/GeFORIA/registros.sqlite3`.

### Límites de hardware y datos reales

- **ESP32 físico:** no utilizado. Pendientes adquisición real por USB y
  Bluetooth SPP, calidad del sensor e índices frente al firmware.
- **Base personal real:** no abierta por seguridad; la migración se comprobó
  con una base anterior ficticia, no con los datos del usuario.
- **Otros sistemas y escalas:** macOS y escalados distintos no probados.
  La ejecución Windows en CI se detalla al principio de este documento.
- **SciPy opcional:** no instalado ni necesario para abrir la interfaz.
