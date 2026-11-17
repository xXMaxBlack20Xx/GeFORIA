# GeFORIA en Windows: descargar y abrir

No necesitas saber programar. Necesitas Windows 10 u 11, una conexión a
Internet para la primera preparación y Python, que es el programa gratuito
que permite ejecutar GeFORIA. **No hace falta abrir como administrador.**

**Puedes probar las pantallas sin sensor.** Para medir de verdad necesitas
el ESP32 con su sensor y el firmware compatible; descargar GeFORIA no prepara
ni reprograma ese dispositivo. Los resultados son exploratorios, no diagnósticos.

## 1. Descargar desde GitHub

1. Abre el repositorio:
   **https://github.com/xXMaxBlack20Xx/GeFORIA**
2. Comprueba que esté seleccionada la rama **main**.
3. Pulsa el botón verde **Code** y después **Download ZIP**.

También puedes usar directamente este enlace:
**https://github.com/xXMaxBlack20Xx/GeFORIA/archive/refs/heads/main.zip**

El repositorio es **público** en la fecha de esta entrega: no necesitas una
cuenta para descargarlo. Si en el futuro pasa a ser privado, necesitarás
iniciar sesión en GitHub con una cuenta que tenga acceso; pide una invitación
al propietario si aparece «404» o no puedes descargar. No es necesario cambiar
los permisos del repositorio.

## 2. Extraer todo el ZIP

1. Busca `GeFORIA-main.zip` en **Descargas**.
2. Haz clic derecho y selecciona **Extraer todo…**.
3. Elige una carpeta tuya, por ejemplo **Documentos**, y pulsa **Extraer**.
4. Abre la carpeta extraída, **no el ZIP**.

Conserva todos los archivos juntos. No muevas solo el lanzador al escritorio.
Puedes crear un acceso directo al lanzador con clic derecho → **Mostrar más
opciones** → **Enviar a → Escritorio (crear acceso directo)**.

## 3. Identificar la carpeta correcta

Abre `GeFORIA-main` hasta encontrar juntos:

- `iniciar_geforia.bat`
- `iniciar_demo.bat`
- `main.py`
- `requirements.txt`
- La carpeta `geforia`

Esa es la carpeta del programa. Puede haber una carpeta exterior con otro
`GeFORIA-main` dentro: utiliza la que contiene esos archivos.
En el Explorador, activa **Ver → Mostrar → Extensiones de nombre de archivo**
para distinguir `.bat` de `.py`.

## 4. Instalar Python una sola vez

1. Entra en la página oficial:
   **https://www.python.org/downloads/windows/**
2. Elige una versión estable de Python **3.10 o posterior**, no una versión
   de prueba. Para simplificar, descarga **Windows installer (64-bit)**;
   si tu equipo es ARM, elige **Windows installer (ARM64)**.
   No elijas **embeddable package**: esa descarga no incluye todo lo necesario.
3. Abre el instalador. Si aparece **Add python.exe to PATH**, márcalo.
   Esto permite que GeFORIA encuentre Python.
4. En **Customize installation**, deja marcadas **pip** y **tcl/tk and IDLE**.
   `pip` descarga los pequeños complementos; Tcl/Tk permite mostrar las ventanas.
   Si se ofrece el lanzador **py**, puedes dejarlo marcado para tu usuario.
5. Instala para **tu usuario**, sin activar **Install for all users**.
   Termina con **Install** y **Close**. No necesitas instalar herramientas de
   programación adicionales.

Los nombres de algunos botones pueden variar según la versión. Si descargaste
el **Python install manager** en lugar del instalador clásico, sigue sus
indicaciones para instalar una versión estable y vuelve después a esta guía.
Si el equipo es de una escuela o empresa y bloquea la instalación, pide ayuda
al responsable; no desactives sus medidas de seguridad.

## 5. Abrir GeFORIA por primera vez

1. Vuelve a la carpeta del paso 3.
2. Haz **doble clic en `iniciar_geforia.bat`**.
3. Se abrirá una ventana de texto. Déjala abierta mientras prepara el programa.
4. Cuando termine aparecerá la ventana de **GeFORIA**.

Si Windows muestra un aviso de seguridad, comprueba que descargaste el ZIP del
repositorio indicado arriba. En un equipo gestionado sigue las indicaciones de
su responsable. No desactives el antivirus ni ejecutes GeFORIA como administrador.

### ¿Qué ocurre durante la primera preparación?

El lanzador encuentra Python con soporte para ventanas y crea una carpeta
`.venv-windows`. Es una copia de trabajo privada de Python para este programa;
no sustituye otras instalaciones ni el entorno de Fedora.

Después instala los complementos indicados en `requirements.txt`, actualmente
`pyserial`, que permite comunicarse con el ESP32. **Esta primera preparación
necesita Internet** y puede tardar unos minutos. No cierres la ventana.

Solo se marca como terminada después de comprobar los complementos. Si falla o
se interrumpe, puedes corregir el problema y volver a hacer doble clic para
reintentar. No borres tu expediente. Evita abrir varios lanzadores a la vez.

## 6. Volver a abrirla

Haz doble clic otra vez en **`iniciar_geforia.bat`** o en su acceso directo.
Se reutiliza lo ya preparado: **no se reinstala todo en cada apertura**.
Se vuelve a preparar si falta algún complemento o cambian los requisitos al
actualizar el programa.

Después de preparar el programa puedes abrirlo sin Internet; el sensor utiliza
USB o Bluetooth, no la conexión a Internet. Para cerrar, utiliza la **X** de la
ventana GeFORIA y responde a cualquier aviso sobre datos sin guardar.
No cierres primero la ventana de texto.

## 7. Probar sin sensor: iniciar_demo.bat

1. Haz doble clic en **`iniciar_demo.bat`**. La primera vez prepara lo mismo que
   el lanzador principal.
2. Comprueba que la ventana diga **DEMO**.
3. En **Mis datos**, escribe un nombre ficticio y una edad, y pulsa
   **Guardar expediente**.
4. En **Medición**, elige el puerto **DEMO**, pulsa **Conectar** y después
   **Iniciar prueba · 60 s**.
5. Espera aproximadamente un minuto. Los números y las señales son **simulados**.
6. Pulsa **Guardar medición** y búscala en **Historial**.

La demo funciona sin conectar un ESP32. Guarda su expediente y sus mediciones
en una subcarpeta `demo`, separada de los datos normales. No mide a ninguna
persona ni comprueba que tu sensor físico funcione.

## 8. Empezar con tus datos y el ESP32

- **Mis datos:** escribe tu nombre y edad. El código del expediente ya está
  generado. Pulsa **Guardar expediente**. Los datos de salud son opcionales;
  no inventes valores que no conozcas. Puedes cambiar de sección sin perder
  el borrador. Al volver a abrir el programa se recupera lo que hayas guardado.
- **Medición:** para una medición real abre `iniciar_geforia.bat`, sin la palabra
  **DEMO** en la ventana. Conecta tu ESP32, selecciona **USB** o **Bluetooth SPP**,
  pulsa **Buscar puertos**, selecciona su puerto (por ejemplo `COM4`) y pulsa
  **Conectar**. Coloca el dedo en el sensor y pulsa **Iniciar prueba · 60 s**.
  Espera el resultado del ESP32, revisa la calidad y pulsa **Guardar medición**.
- **Historial:** consulta las mediciones guardadas, selecciona una y pulsa
  **Ver detalle y señal**. En **Consultas y seguimiento** puedes registrar una
  consulta con sus notas.

**Requisito del dispositivo:** firmware compatible `ppg_sdptg_V3.ino`, protocolo
S/B/R a 921600 baudios. El archivo del firmware no se incluye en esta entrega.
Solicítalo al responsable del dispositivo si aún no lo tiene instalado.
Bluetooth debe ser **SPP**, un enlace que Windows muestra como puerto serie;
no basta con un dispositivo Bluetooth BLE.

## ¿Dónde quedan mis datos?

En la carpeta **GeFORIA** de tu usuario de Windows, normalmente
`C:\Users\TuNombre\GeFORIA\registros.sqlite3`. Ese archivo es la base de datos:
contiene el expediente y los registros. La demo usa
`C:\Users\TuNombre\GeFORIA\demo\registros.sqlite3`.

Usa **Crear respaldo** para guardar una copia. No envíes tu base personal junto
con el programa, no la borres para resolver errores y no la subas a GitHub.
Si actualizas el programa, no sustituyas esa carpeta de datos.

## Si algo no funciona

### Python no encontrado

Instala Python siguiendo el paso 4, incluyendo **Add python.exe to PATH**.
Después cierra el mensaje y vuelve a abrir `iniciar_geforia.bat`.
Si Python ya está instalado, abre su instalador y utiliza **Modify** para
revisar las opciones.

### Tkinter no disponible

Tkinter es la parte que dibuja las ventanas. Abre el instalador oficial de
Python → **Modify**, activa **tcl/tk and IDLE** y termina la instalación.
No intentes descargar Tkinter por separado desde páginas no oficiales.

### Error al instalar complementos

Comprueba Internet, el espacio libre y que el programa esté extraído en una
carpeta tuya, no dentro del ZIP ni en **Archivos de programa**. Cierra otras
ventanas de GeFORIA y vuelve a abrir el lanzador: reintentará la preparación.
En una red escolar o empresarial, pide ayuda si el mensaje menciona un proxy
o un certificado; no desactives la comprobación de seguridad.

### La ventana se cierra o no aparece

Abre **`iniciar_geforia.bat`**, no `main.py`. Si hay un error, el lanzador deja
el mensaje visible hasta que pulses una tecla: cópialo o toma una foto.
Comprueba que extrajiste todo el ZIP. Si cerraste la ventana de texto
manualmente, vuelve a abrir el programa y déjala abierta.

### No aparece el puerto del ESP32

Prueba un cable USB que transmita datos, no uno solo de carga. Conecta el
dispositivo y pulsa **Buscar puertos**. En Windows, haz clic derecho en
**Inicio → Administrador de dispositivos → Puertos (COM y LPT)** para encontrar
su nombre. Si pide un controlador, utiliza el recomendado por el fabricante
de tu placa o pide ayuda al responsable del dispositivo.
Para Bluetooth, empareja el ESP32 desde Windows y selecciona su puerto **SPP**.

### El puerto está ocupado

Cierra otras ventanas de GeFORIA, el monitor serie de Arduino u otros programas
que estén usando el ESP32. Después vuelve a pulsar **Conectar**.

---

Guía en GitHub:
https://github.com/xXMaxBlack20Xx/GeFORIA/blob/main/GUIA_WINDOWS.md

Estado de las comprobaciones y límites de esta entrega:
[docs/VALIDACION.md](docs/VALIDACION.md).
