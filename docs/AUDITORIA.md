# Auditoría previa y prioridades

Base analizada: `GeFORIA_Expediente_Personal_PPG_SDPTG_CORREGIDO (1).py` (646 líneas).
La refactorización del núcleo se realiza antes de construir las nuevas vistas.

| Prioridad | Hallazgo | Resolución prevista |
| --- | --- | --- |
| Alta | `App` reúne SQL, formularios, serial, almacenamiento y gráficos. | Extraer persistencia, dominio, validaciones, protocolo y sesión de adquisición; las vistas no ejecutan SQL. |
| Alta | Se guarda calidad «Pendiente» aunque `R` comunica si la prueba es válida. | Conservar calidad y congelar la captura al terminar; distinguir una captura parcial. |
| Alta | Cambiar de página recarga el expediente y descarta cambios. | Mantener el formulario vivo y pedir decisión al cerrar con cambios. |
| Alta | Desconectar/reconectar puede mezclar eventos o perder comandos. | Una cola por conexión, estados explícitos, parada cooperativa y espera no bloqueante. |
| Alta | Formulario con doce entradas libres y notas sin prioridad. | Tres secciones con revisión, errores por campo y listas editables donde corresponde. |
| Media | Botones de ancho fijo exceden el área disponible. | Controles en dos filas, paneles expandibles y desplazamiento de formularios/tablas. |
| Media | ID editable después de crearlo, aunque el guardado rechaza el cambio. | Código automático al crear y campo bloqueado después. |
| Media | Errores técnicos y confirmaciones modales para acciones rutinarias. | Avisos persistentes junto a la tarea; diálogos para decisiones y fallos de almacenamiento. |
| Media | No hay protección explícita al sobrescribir ni copia previa a migración. | Confirmar cambios del expediente existente y respaldar antes de la migración inicial. |
| Media | `eliminar_paciente` no elimina consultas y puede violar su clave externa. | Borrado transaccional de consultas, señales y estudios antes del expediente. |
| Baja | Imports y filtro NumPy/SciPy sin uso en la interfaz. | Eliminar imports muertos; conservar filtrado exploratorio en módulo separado con alternativa estándar. |

## Inventario funcional que se debe conservar

- Un expediente activo; código fijo, nombre, edad, sexo, peso, presión, temperatura,
  antecedentes, tabaquismo, actividad, medicamentos y notas.
- Lectura de la base `~/GeFORIA/registros.sqlite3`, incluyendo campos heredados.
- USB y Bluetooth SPP mediante puerto serie a 921600 baudios, comandos `r` y `s`.
- Mensajes S/B/R, gráficas de PPG y D2, BPM, b/a y AGI.
- Prueba de 60 s controlada por firmware; el ordenador no determina su finalización.
- Captura manual parcial, guardado de los últimos 30 s y señales JSON comprimidas.
- Historial de estudios, eliminación con confirmación, consultas y seguimiento.
- Métodos existentes de acceso a pacientes y señales para compatibilidad de datos.

La versión recibida no implementa exportación de documentos ni incluye el firmware
`.ino`. No se inventa ni se reemplaza dicho firmware. Se mantienen su protocolo
y sus cálculos; los índices no se reinterpretan como diagnósticos.
