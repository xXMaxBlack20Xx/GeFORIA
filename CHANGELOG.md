# Cambios

## 2026-11-16 · Arranque reparado y entrega para Windows

- Corregido el ciclo de geometría de las ayudas de formulario que impedía
  mostrar la ventana; ancho del canvas estabilizado antes del primer mapeo.
- Cierre explícito de los destinos SQLite de respaldo, incluidas las migraciones.
- Conservados el expediente, las señales y registros anteriores, el protocolo
  del ESP32, la demo y el lanzador de Fedora `iniciar_geforia.sh`.
- Nuevos `iniciar_geforia.bat` e `iniciar_demo.bat`: detección de Python/Tkinter,
  entorno `.venv-windows` independiente, primera instalación con reintento y
  reutilización sin reinstalar en cada apertura; errores visibles.
- Nueva `GUIA_WINDOWS.md` para descargar desde GitHub, instalar Python y utilizar
  la aplicación sin conocimientos de programación.
- Exclusión de entornos, cachés, bases personales, respaldos y temporales de Git.
- Regresiones de arranque, navegación, respaldos y lanzadores; validación Windows
  automatizada definida en GitHub Actions. Resultados y límites, sin equiparar
  revisión de BAT con ejecución, en `docs/VALIDACION.md`.

## 3.0.0

### Arquitectura

- Separación de modelos, validación, persistencia, protocolo, adquisición y UI.
- Punto de entrada `main.py` y configuración central.
- Sin SQL en las vistas ni llamadas Tk desde el hilo serie.
- Dependencia obligatoria externa reducida a pyserial para hardware.
- Gráficas con Tk Canvas; el filtro exploratorio original permanece en un
  módulo independiente con alternativa sin dependencias científicas.

### Experiencia e interfaz

- Expediente en Básicos, Salud opcional y Revisar, con guardado directo desde
  cualquier sección y conservación del borrador.
- Código automático editable antes del alta y fijo después; solo nombre y edad
  requieren captura manual para empezar.
- Listas de sexo, tabaquismo y actividad; las dos últimas permiten texto libre
  para conservar descripciones anteriores.
- Validación al salir del campo y al avanzar; errores específicos y foco en la
  primera corrección necesaria.
- Confirmación al actualizar datos, recuperar otro expediente o descartar
  información; advertencia al cerrar con cambios o captura sin guardar.
- Navegación lateral activa, tema claro, acentos verde azulado, tarjetas de
  métricas, espaciado consistente y estados de controles.
- Controles de conexión en dos filas, formularios desplazables, tablas con
  desplazamiento horizontal y vertical y atajos de teclado.
- Historial separado en mediciones y consultas; búsqueda, detalle y señal.
- Nuevo formulario de consulta independiente y observaciones por medición.

### Correcciones

- Conservar la calidad del resultado R en lugar de guardar siempre «Pendiente».
- No reutilizar BPM previo si el resultado final no contiene BPM válido.
- Congelar la captura al recibir el resultado para no mezclar muestras posteriores.
- Prevenir el guardado duplicado de una misma captura final.
- Aislar las colas al reconectar y evitar dos lectores sobre la misma sesión.
- Conservar fragmentos de mensajes serie entre timeouts; limitar líneas corruptas.
- Evitar crecimiento ilimitado de muestras en cola si la interfaz se bloquea.
- Resolver reinicios del índice temporal sin mezclar datos anteriores.
- Eliminar consultas y configuración asociadas al eliminar un paciente mediante
  el repositorio, respetando las claves externas.
- Comprobar la integridad de la señal antes de almacenar una medición.
- Respaldar antes de la migración y ejecutar los cambios de esquema en transacción.
- Guardar perfil y selección activa de forma atómica.

### Conservado

- Expediente único activo y todos los campos de la versión recibida.
- Tablas y campos heredados, incluida la columna `grasa`, sin descartarlos al editar.
- USB/Bluetooth SPP, baudios, protocolo S/B/R y comandos r/s.
- Gráficas PPG/D2, métricas del firmware, pruebas de 60 s y capturas parciales.
- Guardado de los últimos 30 s disponibles como JSON comprimido con zlib.
- Historial de mediciones, eliminación confirmada y registro de consultas.
- Lectura de mediciones anteriores sin señal y recuperación de expedientes.

### Verificación y límites

- Pruebas automatizadas de reglas, datos heredados, señales y comunicación simulada.
- Pruebas gráficas incluidas, con omisión explícita si no hay pantalla.
- En la entrega inicial no se había inspeccionado visualmente la ventana.
  La reparación posterior sí se comprobó en Fedora. Sigue pendiente el hardware
  real; véase el registro actualizado en `docs/VALIDACION.md`.
