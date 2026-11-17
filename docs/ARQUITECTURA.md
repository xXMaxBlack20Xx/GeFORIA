# Arquitectura

Se conserva Tkinter porque permite mejorar navegación, formularios, tablas y
gráficas sin migrar de framework ni añadir un motor web. El nuevo dibujo con
Canvas muestra los datos transmitidos por el ESP32 y elimina la necesidad de
Matplotlib y NumPy para la ventana. No modifica los índices ni el firmware.

## Módulos y dependencias

| Módulo | Responsabilidad | Dependencias principales |
| --- | --- | --- |
| `main.py` | CLI y arranque con mensajes recuperables. | Configuración y `App`. |
| `app.py` | Crear servicios, elegir página y procesar eventos en el hilo gráfico. | Servicios, repositorio y vistas. |
| `models.py` | `Profile` y `Capture` inmutables. | Biblioteca estándar. |
| `validation.py` | Campos obligatorios, rangos y relación sistólica/diastólica. | Modelos y `math`. |
| `persistence/database.py` | Todo el SQL, transacciones, migración, zlib y respaldos. | SQLite, configuración. |
| `services/records.py` | Alta y edición del expediente, activación heredada, consultas. | Validación y repositorio recibido al construir. |
| `services/protocol.py` | Interpretación pura de S/B/R y reconstrucción de líneas partidas. | Constantes y `math`. |
| `services/serial_connection.py` | Leer el puerto, enviar comandos y producir eventos. | pyserial de carga diferida, parser. |
| `services/connection_manager.py` | Una conexión activa, colas nuevas y parada cooperativa. | Trabajadores serie y demo. |
| `services/acquisition.py` | Estado de captura, calidad, ventana almacenada y guardado. | Modelos y configuración. |
| `services/demo.py` | Fuente simulada explícita para revisar la aplicación sin sensor. | Biblioteca estándar. |
| `services/signal_processing.py` | Filtrado exploratorio aislado, conservado como utilidad. | Estándar; SciPy opcional. |
| `ui/profile.py` | Expediente, borrador, pasos y errores junto al campo. | Servicio de expedientes y widgets. |
| `ui/measurement.py` | Guía para conectar, medir y guardar; estados de botones. | Sesión y gestor de conexión. |
| `ui/history.py` | Listados, detalles, eliminación y formulario de consulta. | Servicios y repositorio; no ejecuta SQL. |
| `ui/widgets.py` | Campos, tablas, texto y desplazamiento compartidos. | Tkinter/ttk. |
| `ui/theme.py` | Colores, tipografía y estilos. | Tkinter/ttk. |
| `ui/plot.py` | Gráficas PPG y D2 de los últimos 8 s. | Tk Canvas y biblioteca estándar. |

## Decisiones

- Una responsabilidad por módulo. No se añade un contenedor de inyección,
  un ORM ni una capa genérica de repositorios para una sola base SQLite.
- Los servicios reciben el repositorio o sus colas al construirlos. La lógica
  de validación y el parser se prueban sin ventana ni hardware.
- El hilo serie solo produce eventos; Tk y SQLite se utilizan en el hilo
  principal. La ventana procesa lotes cada 100 ms y dibuja si hay muestras nuevas.
- Cada conexión tiene su cola; no se inicia otra mientras el lector anterior
  siga vivo. Desconectar descarta eventos tardíos, no la última captura.
- El buffer conserva hasta 65 s a 200 Hz. El guardado mantiene la ventana de
  30 s del original; el detalle gráfico muestra los últimos 8 s de lo guardado.
- Al recibir R se conserva una captura inmutable. Las muestras posteriores no
  cambian los resultados ya revisados. La calidad puede ser Válida, Revisar o
  Pendiente para una captura parcial.
- Una prueba de 60 s pertenece al firmware. La barra del ordenador es
  indeterminada para no inventar un progreso cuando el sensor espera estabilidad.
- Los borradores viven en las vistas y no se recargan al cambiar de sección.
  Cerrar con cambios requiere una decisión; no se persisten borradores incompletos
  automáticamente ni se autocompletan valores de salud.

## Datos y compatibilidad

Se conserva la estructura de `pacientes`, `mediciones`, `senales_ppg`,
`geforia_config` y `consultas_geforia`. Solo se añaden campos faltantes al abrir
esquemas antiguos; nunca se reescriben las muestras anteriores. Se registra
`app_schema_version` en la configuración. Un respaldo previo permite volver
a la base original si se necesita.

Los métodos heredados del repositorio se mantienen para lectura, guardado y
eliminación. Los nuevos listados incluyen ID y datos en una misma consulta,
evitando relacionar filas mediante dos consultas independientes.

El helper `filtrar_ppg` ahora devuelve una lista de flotantes. No era utilizado
por la ventana original. Su alternativa de medias móviles permanece disponible;
si se instala SciPy, puede utilizar su filtro de banda como antes. Esta utilidad
no se ejecuta sobre los datos recibidos para dibujar ni calcular resultados.

## Alcance

Aplicación local, un expediente activo, sin servidor, cuentas, telemetría ni
servicios externos. La base no está cifrada y depende de los permisos del
usuario del sistema, igual que en la versión original. La autenticación o el
cifrado requerirían un alcance adicional y una estrategia de recuperación.

El detalle completo de cambios está en `CHANGELOG.md`; la evidencia de pruebas
y los límites reales de la entrega están en `VALIDACION.md`.
