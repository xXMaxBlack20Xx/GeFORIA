# Datos y migración

## Primera apertura

1. Cierra la aplicación anterior y cualquier visor que esté modificando la base.
2. La nueva versión utiliza `~/GeFORIA/registros.sqlite3`, como la recibida.
   Si está en otro lugar, ejecuta `python main.py --data-dir CARPETA`.
3. Antes de migrar una base existente sin la versión de esquema actual, se crea
   una copia completa mediante la API de respaldo de SQLite en
   `CARPETA/backups/registros_antes_v3_FECHA_HORA.sqlite3`.
4. Se crean las tablas faltantes y se agregan columnas que no existan, dentro de
   una transacción. Si falla el respaldo o la migración, no se continúa con la UI.
5. Si existe un expediente activo válido, se conserva. Si no, Mis datos permite
   seleccionar entre los expedientes anteriores. El usuario elige explícitamente.

No es necesario exportar, importar ni convertir manualmente señales. Se mantiene
el JSON con claves `t`, `y`, `sdptg`, comprimido con zlib en `senales_ppg`.
Las mediciones antiguas sin señal siguen apareciendo en el historial.

La base personal del usuario no se abrió durante el desarrollo. La migración se
probó con una base temporal que reproduce el esquema antiguo y registros
ficticios; eso no sustituye comprobar una copia de tu base real.

## Comprobar antes de usar datos reales

Puedes copiar la base a otra carpeta y abrir esa copia con `--data-dir`.
Comprueba nombre, cantidad de estudios, consultas y una señal guardada. La
carpeta del proyecto y la carpeta de datos pueden ser diferentes.

No ejecutes dos versiones de la aplicación sobre la misma base al mismo tiempo.
La copia previa se crea una vez por migración; no representa un historial
automático de todas las ediciones posteriores. Usa Crear respaldo cuando lo
necesites.

## Restaurar un respaldo

1. Cierra GeFORIA y cualquier otro programa que use la base.
2. Conserva una copia de la base actual fuera de la carpeta activa.
3. Copia el respaldo deseado dentro de la carpeta de datos y nómbralo
   `registros.sqlite3`.
4. Abre GeFORIA con la carpeta de datos correspondiente y comprueba el contenido.

La restauración revierte el conjunto completo de registros a la fecha del
respaldo. Si necesitas regresar al programa anterior, utiliza la base previa
guardada y el código original; no se exige que versiones antiguas interpreten
las nuevas marcas de calidad.
