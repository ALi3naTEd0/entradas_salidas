# Registro E/S — Los Cielos Farm

Descripción breve

Sitio de presentación disponible en `docs/` (landing page lista para GitHub Pages, con logo tomado de `docs/assets/`).

Aplicación GUI (Tkinter) para registro, seguimiento y arqueo de entradas y salidas de producto por lote y sucursal. Permite sincronizar el archivo `registro.csv` con un repositorio de GitHub (vía API), filtrar y editar registros, exportar informes (TXT/PDF/CSV), y generar gráficos y resúmenes por lote y por filtros.

## ✅ Características principales

- Interfaz gráfica con pestañas: `Registro`, `Gráficos Generales`, `Arqueo por Lote`. 🔧
- Guardado local en `registro.csv` y sincronización con un repositorio de GitHub (API REST). 🌐
- Mecanismo de merge al sincronizar: conserva el contenido remoto y agrega solo los registros locales nuevos (evita sobrescribir). 🔀
- Backups automáticos en `registros/backups/` antes de sobrescribir local. 🗂️
- Editor de registros con filtros, edición inline (motivo, cliente, no_aplicación) y exportación a PDF. ✏️📄
- Generación de resúmenes y arqueos por lote, exportables a TXT/PDF, y archivado histórico (sin eliminar el registro principal). 📊
- Gráficos con `matplotlib` y opción de ver resultados como lista descriptiva. 📈
- Exportar CSV desde la barra de estado. 📥

## 📦 Requisitos (dependencias)

Recomendado: Python 3.9+ (probado con 3.10/3.11)

Paquetes (ver `requirements.txt`):

- tkinter (incluido en la mayoría de instalaciones de Python con GUI)
- tkcalendar
- pandas
- matplotlib
- requests
- fpdf
- numpy
- pillow

Instalación rápida:

```bash
pip install -r requirements.txt
```

## ⚙️ Configuración (GitHub)

El proyecto utiliza un archivo `github_config.txt` en la misma carpeta que `registro_gui.py` con dos líneas:

1. `usuario/repo` (ejemplo: `ALi3naTEd0/entradas_salidas`)
2. `GITHUB_TOKEN` (token personal con permiso `repo` para leer/escribir archivos via API)

Si `github_config.txt` no existe, la aplicación lo creará con un ejemplo y pedirá que lo edites.

> Nota de seguridad: el token se guarda en texto plano en `github_config.txt`. Para producción, considere un método seguro para gestionar credenciales.

## 🗂️ Formato de `registro.csv`

El archivo CSV esperado tiene la siguiente cabecera (orden y nombres de columnas):

```
fecha,variedad,colaborador,gramos,plantas,supervisor,sucursal,lote,motivo,variedad_mix,cliente,no_aplicacion,tipo
```

- `fecha`: `YYYY-MM-DD`
- `variedad`: nombre de variedad (o `MIX`) — el campo `variedad_mix` se rellena cuando `variedad == MIX`
- `colaborador`: iniciales del colaborador (vacío en Salida)
- `gramos`: número; en Salida se guarda como negativo (ej. `-12`)
- `plantas`: entero (solo para entradas)
- `supervisor`, `sucursal`, `lote`, `motivo`, `cliente`, `no_aplicacion` (string)
- `tipo`: `Entrada` o `Salida`

La aplicación realiza migraciones automáticas si el encabezado es distinto al esperado.

## 🔁 Sincronización con GitHub

- `leer_repo()`: descarga `registro.csv` desde el repo (GitHub API) y guarda el `sha` del archivo para futuras actualizaciones.
- `escribir_repo()`: sube el archivo (codificado en base64) usando `PUT /repos/:owner/:repo/contents/:path` y actualiza `sha`.
- `sincronizar_desde_gist()`: descarga la versión remota y la escribe localmente (creando backup local en `registros/backups/`).
- `sincronizar_a_gist()`: hace merge entre remoto y local (preserva remoto y agrega registros locales únicos al final) y sube el resultado.

> En caso de falla de conexión, la app trabaja con el archivo local y notifica mediante la barra de estado.

## 🖥️ Uso

1. Edita `github_config.txt` con tu `usuario/repo` y `TOKEN` (si deseas sincronizar con GitHub).
2. Ejecuta la app:

```bash
python registro_gui.py
```

3. Pestañas principales:
- Registro: formulario para crear entradas/salidas.
- Gráficos Generales: filtros, selección de campo y botón `Mostrar resultado` para gráfica o lista descriptiva.
- Arqueo por Lote: seleccionar sucursal y lote, ver resumen, exportar/archivar.

Funciones importantes:
- `Filtrar registro` abre un editor con filtros, sumas, edición inline y exportación a PDF.
- `↻ Sincronizar` fuerza refresco con el repo remoto.
- `📥 Exportar CSV` guarda una copia del `registro.csv` en la ubicación que elijas.

## 🧰 Empaquetado (ejecutable)

El código incluye soporte para PyInstaller (detecta `sys.frozen`). Ejemplo de generación de un ejecutable:

```bash
pip install pyinstaller
pyinstaller --onefile --add-data "registro.csv:." registro_gui.py
```

Si deseas incluir icono u otros assets, añade `--add-data` o `--add-binary` según sea necesario.

## ⚠️ Advertencias y notas

- La app es una aplicación de escritorio GUI; no está pensada para ejecutarse en entornos puramente headless sin servidor X/Wayland.
- El token de GitHub se guarda en texto plano; si la seguridad es crítica, use un gestor de secretos.
- Exportación a PDF requiere `fpdf`.
- La sincronización hace backups locales antes de sobrescribir `registro.csv`.

## 🧪 Pruebas y depuración

- Mensajes de error y advertencias aparecen por consola (útil al empaquetar).
- Si no se puede sincronizar, la app continúa en modo local y muestra enlace deshabilitado en la barra de estado.

## 📝 Mantenibilidad / Extensiones sugeridas

- Reemplazar almacenamiento de token por variables de entorno o integración con secret manager.
- Añadir tests automatizados para funciones de merge y export.
- Añadir internacionalización si se requiere otro idioma.

## 📄 LICENSE

Este repositorio incluye una licencia comercial en `LICENSE`. Titular: edfortuny (2026). Jurisdicción: México. Contacto: edfortuny@gmail.com.

---

Si quieres, puedo:

- Añadir un `CONTRIBUTING.md` y un `CHANGELOG.md`.
- Generar un instalador con PyInstaller con parámetros recomendados.
- Personalizar la `LICENSE` con el nombre del cliente y condición de soporte.

Indícame si quieres que personalice la licencia con datos del cliente (nombre y jurisdicción).