import tkinter as tk
from tkinter import ttk, messagebox
from tkcalendar import DateEntry
import csv
import os
from datetime import datetime
import pandas as pd
import matplotlib.pyplot as plt
import sys
import requests
import base64

# Soporte para ejecutable PyInstaller: buscar archivo en la misma carpeta que el .exe o script
if getattr(sys, 'frozen', False):
    BASE_PATH = os.path.dirname(sys.executable)
else:
    BASE_PATH = os.path.dirname(os.path.abspath(__file__))

# Archivo de configuración para credenciales de GitHub
CONFIG_FILE = os.path.join(BASE_PATH, "github_config.txt")

def cargar_config():
    """Carga la configuración del repo desde archivo github_config.txt"""
    if not os.path.exists(CONFIG_FILE):
        # Crear archivo de ejemplo
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            f.write("usuario/nombre-repo\nTU_TOKEN_AQUI\n")
        print(f"ERROR: Configura tus credenciales en: {CONFIG_FILE}")
        print("Línea 1: usuario/repo (ej: ALi3naTEd0/entradas_salidas)")
        print("Línea 2: TOKEN de GitHub con permiso 'repo'")
        sys.exit(1)
    
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        lineas = f.read().strip().split("\n")
    
    if len(lineas) < 2:
        print(f"ERROR: El archivo {CONFIG_FILE} debe tener 2 líneas:")
        print("Línea 1: usuario/repo")
        print("Línea 2: TOKEN de GitHub")
        sys.exit(1)
    
    repo = lineas[0].strip()
    token = lineas[1].strip()
    
    if "TU_TOKEN_AQUI" in token or "/" not in repo:
        print(f"ERROR: Edita el archivo {CONFIG_FILE} con tus credenciales reales")
        sys.exit(1)
    
    return repo, token

# Cargar configuración
GITHUB_REPO, GITHUB_TOKEN = cargar_config()
REPO_FILENAME = "registro.csv"

# Archivo local para caché/backup
CSV_FILE = os.path.join(BASE_PATH, "registro.csv")

# Variable global para almacenar el SHA del archivo
archivo_sha = None

def leer_repo():
    """Lee el contenido del CSV desde GitHub Repo"""
    global archivo_sha
    try:
        url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{REPO_FILENAME}"
        headers = {
            "Authorization": f"token {GITHUB_TOKEN}",
            "Accept": "application/vnd.github.v3+json"
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        archivo_sha = data["sha"]  # Guardar SHA para actualizaciones
        contenido = base64.b64decode(data["content"]).decode("utf-8")
        return contenido
    except Exception as e:
        print(f"Error leyendo repo: {e}")
        return None

def escribir_repo(contenido):
    """Escribe el contenido del CSV al GitHub Repo"""
    global archivo_sha
    try:
        # Primero obtener el SHA actual si no lo tenemos
        if archivo_sha is None:
            url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{REPO_FILENAME}"
            headers = {"Authorization": f"token {GITHUB_TOKEN}"}
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                archivo_sha = response.json()["sha"]
        
        url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{REPO_FILENAME}"
        headers = {
            "Authorization": f"token {GITHUB_TOKEN}",
            "Accept": "application/vnd.github.v3+json"
        }
        
        # Codificar contenido en base64
        contenido_b64 = base64.b64encode(contenido.encode("utf-8")).decode("utf-8")
        
        data = {
            "message": f"Actualización registro {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            "content": contenido_b64,
        }
        
        if archivo_sha:
            data["sha"] = archivo_sha
        
        response = requests.put(url, headers=headers, json=data, timeout=10)
        response.raise_for_status()
        
        # Actualizar SHA con el nuevo
        archivo_sha = response.json()["content"]["sha"]
        return True
    except Exception as e:
        print(f"Error escribiendo repo: {e}")
        return False

def sincronizar_desde_gist():
    """Descarga el CSV del Repo y lo guarda localmente"""
    contenido = leer_repo()
    if contenido:
        with open(CSV_FILE, "w", encoding="utf-8", newline="") as f:
            f.write(contenido)
        return True
    return False

def sincronizar_a_gist():
    """Sube el CSV local al Repo con merge automático para evitar conflictos"""
    if not os.path.exists(CSV_FILE):
        return False

    # Leer datos locales, asegurando saltos de línea correctos
    with open(CSV_FILE, "r", encoding="utf-8") as f:
        lineas_locales = [linea.rstrip('\r\n') for linea in f if linea.strip()]

    # Obtener versión más reciente del repo
    contenido_remoto = leer_repo()

    if contenido_remoto:
        # Hacer merge: preservar orden del remoto y agregar nuevos registros locales al final
        lineas_remotas = [linea.rstrip('\r\n') for linea in contenido_remoto.strip().split("\n") if linea.strip()]

        # Primera línea es el encabezado
        encabezado = lineas_locales[0] if lineas_locales else lineas_remotas[0]

        # Mantener todos los registros remotos en su orden original (preserva duplicados válidos)
        registros_remotos = lineas_remotas[1:] if len(lineas_remotas) > 1 else []

        # Crear un conjunto de registros remotos para verificar cuáles son nuevos
        registros_remotos_set = set(registros_remotos)

        # Agregar solo los registros locales que NO existen en el remoto (al final)
        registros_nuevos = []
        for linea in lineas_locales[1:]:
            if linea and linea not in registros_remotos_set:
                registros_nuevos.append(linea)

        # Combinar: remoto (preservado) + nuevos locales (al final)
        todos_registros = registros_remotos + registros_nuevos

        contenido_merged = encabezado + "\n" + "\n".join(todos_registros) + "\n"

        # Guardar localmente el merge, asegurando un salto de línea por registro
        with open(CSV_FILE, "w", encoding="utf-8", newline="") as f:
            f.write(contenido_merged)

        return escribir_repo(contenido_merged)
    else:
        # Si no hay versión remota, subir la local
        contenido_local = "\n".join(lineas_locales) + "\n"
        return escribir_repo(contenido_local)

# Listas de opciones
VARIEDADES = [
    "AK-47", "APPLE FRITTER", "BANANA LATTE", "BLACKBERRY HONEY",
    "GRAN JEFA", "KANDY KUSH", "KING KUSH BREATH", "KOSHER KUSH", "MICHAEL JORDAN",
    "MIX", "MOZZARELLA", "ORANGEL", "RECON", "RED RED WINE", "RUNTZ", "SUGAR CANE", "WEDDING CAKE", "ZALLAH BREAD"
]
SUCURSALES = ["FSM", "SMB", "RP"]
COLABORADORES = ["KEF", "CHCH", "LE", "AX", "JP", "NRQ", "JR"]
SUPERVISORES = ["DRE", "RAB", "JP"]

CAMPOS = ["fecha", "variedad", "colaborador", "gramos", "plantas", "supervisor", "sucursal", "lote", "motivo", "variedad_mix", "cliente", "no_aplicacion"]

class RegistroApp:
    def abrir_editor_registros(self):
        if not os.path.exists(CSV_FILE):
            messagebox.showerror("Error", "No hay datos registrados.")
            return
        editor = tk.Toplevel(self.root)
        editor.title("Editar registros existentes")
        editor.geometry("1200x500")
        frame = ttk.Frame(editor)
        frame.pack(fill="both", expand=True)
        # Filtros de fecha (desde/hasta)
        date_filter_frame = ttk.Frame(frame)
        date_filter_frame.grid(row=0, column=0, sticky="ew", columnspan=2, pady=5)
        ttk.Label(date_filter_frame, text="Fecha desde:").pack(side="left", padx=5)
        fecha_desde_var = DateEntry(date_filter_frame, date_pattern='yyyy-mm-dd', width=12)
        fecha_desde_var.pack(side="left", padx=5)
        fecha_desde_var.delete(0, "end")
        ttk.Label(date_filter_frame, text="Fecha hasta:").pack(side="left", padx=5)
        fecha_hasta_var = DateEntry(date_filter_frame, date_pattern='yyyy-mm-dd', width=12)
        fecha_hasta_var.pack(side="left", padx=5)
        fecha_hasta_var.delete(0, "end")

        # Filtros tipo Excel
        filter_frame = ttk.Frame(frame)
        filter_frame.grid(row=1, column=0, sticky="ew", columnspan=2)
        filter_vars = {}
        def get_unique_values(col):
            vals = set(row.get(col, "") for row in rows)
            return sorted([v for v in vals if v])

        # Cargar datos primero para los filtros
        with open(CSV_FILE, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        columns = CAMPOS + ["tipo"]
        # Crear filtros para todas las columnas excepto fecha (que tiene filtro de rango arriba)
        for j, col in enumerate(columns):
            filter_frame.grid_columnconfigure(j, weight=1, uniform="filtros")
        for j, col in enumerate(columns):
            if col == "fecha":
                # Placeholder para fecha (el filtro de rango está arriba)
                lbl = ttk.Label(filter_frame, text="(filtro arriba)", font=("Arial", 8))
                lbl.grid(row=0, column=j, padx=0, pady=1, sticky="nsew")
            else:
                var = tk.StringVar()
                filter_vars[col] = var
                unique_vals = get_unique_values(col)
                if 1 < len(unique_vals) <= 20:
                    cb = ttk.Combobox(filter_frame, textvariable=var, values=["(Todos)"]+unique_vals, state="readonly")
                    cb.set("(Todos)")
                    cb.grid(row=0, column=j, padx=0, pady=1, sticky="nsew")
                else:
                    ent = ttk.Entry(filter_frame, textvariable=var)
                    ent.grid(row=0, column=j, padx=0, pady=1, sticky="nsew")

        # Tabla con scroll
        tree = ttk.Treeview(frame, columns=columns, show="headings", height=20)
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=100, anchor="center")
        vsb = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
        tree.configure(yscroll=vsb.set)
        tree.grid(row=2, column=0, sticky="nsew")
        vsb.grid(row=2, column=1, sticky="ns")
        frame.grid_rowconfigure(2, weight=1)
        frame.grid_columnconfigure(0, weight=1)


        # Frame para suma y botón PDF
        bottom_frame = ttk.Frame(editor)
        bottom_frame.pack(fill="x", pady=6)
        suma_gramos_var = tk.StringVar()
        suma_label = ttk.Label(bottom_frame, textvariable=suma_gramos_var, font=("Arial", 11, "bold"))
        suma_label.pack(side="left", padx=10)

        def cargar_treeview(filtrados):
            tree.delete(*tree.get_children())
            suma = 0.0
            for i, row in enumerate(filtrados):
                values = [row.get(c, "") for c in columns]
                tree.insert("", "end", iid=str(i), values=values)
                try:
                    gramos = float(row.get("gramos", 0))
                    suma += gramos
                except Exception:
                    pass
            suma_gramos_var.set(f"Suma de gramos: {suma:.2f}")

        cargar_treeview(rows)

        def aplicar_filtros(*args):
            filtrados = rows
            # Filtrar por rango de fechas
            fecha_desde = fecha_desde_var.get().strip()
            fecha_hasta = fecha_hasta_var.get().strip()
            if fecha_desde or fecha_hasta:
                def en_rango_fecha(row):
                    fecha_str = row.get("fecha", "")
                    if not fecha_str:
                        return False
                    try:
                        fecha = datetime.strptime(fecha_str, "%Y-%m-%d")
                        if fecha_desde:
                            desde = datetime.strptime(fecha_desde, "%Y-%m-%d")
                            if fecha < desde:
                                return False
                        if fecha_hasta:
                            hasta = datetime.strptime(fecha_hasta, "%Y-%m-%d")
                            if fecha > hasta:
                                return False
                        return True
                    except:
                        return True
                filtrados = [r for r in filtrados if en_rango_fecha(r)]
            # Filtrar por otros campos (excepto fecha)
            for col in columns:
                if col == "fecha":
                    continue
                val = filter_vars[col].get()
                if val and val != "(Todos)":
                    if len(val) > 0:
                        filtrados = [r for r in filtrados if val.lower() in str(r.get(col, "")).lower()]
            cargar_treeview(filtrados)

        # Asociar eventos a los filtros
        for col in columns:
            if col == "fecha":
                continue
            var = filter_vars[col]
            var.trace_add('write', aplicar_filtros)
        # Asociar eventos a los filtros de fecha
        fecha_desde_var.bind("<<DateEntrySelected>>", aplicar_filtros)
        fecha_desde_var.bind("<KeyRelease>", aplicar_filtros)
        fecha_hasta_var.bind("<<DateEntrySelected>>", aplicar_filtros)
        fecha_hasta_var.bind("<KeyRelease>", aplicar_filtros)
        # Edición en línea de motivo y cliente
        def editar_celda(event):
            item = tree.focus()
            if not item:
                return
            col = tree.identify_column(event.x)
            col_idx = int(col.replace('#','')) - 1
            if col_idx not in [CAMPOS.index("motivo"), CAMPOS.index("cliente"), CAMPOS.index("no_aplicacion")]:
                return
            x, y, width, height = tree.bbox(item, col)
            valor_actual = tree.set(item, CAMPOS[col_idx])
            # Determinar opciones para motivo y cliente
            if col_idx == CAMPOS.index("motivo"):
                tipo = tree.set(item, "tipo")
                if tipo == "Salida":
                    opciones = ["venta", "pre-rolls", "mix"]
                else:
                    opciones = ["inventario", "trim", "traslado", "flor", "mix"]
                combo = ttk.Combobox(tree, values=opciones, state="readonly")
                combo.place(x=x, y=y, width=width, height=height)
                combo.set(valor_actual)
                combo.focus()
                def guardar_combo(e=None):
                    tree.set(item, CAMPOS[col_idx], combo.get())
                    combo.destroy()
                combo.bind("<Return>", guardar_combo)
                combo.bind("<FocusOut>", guardar_combo)
            elif col_idx == CAMPOS.index("cliente"):
                motivo = tree.set(item, "motivo")
                if motivo == "venta":
                    clientes = list({tree.set(iid, "cliente") for iid in tree.get_children() if tree.set(iid, "cliente")})
                    combo = ttk.Combobox(tree, values=clientes, state="normal")
                    combo.place(x=x, y=y, width=width, height=height)
                    combo.set(valor_actual)
                    combo.focus()
                    def guardar_combo(e=None):
                        tree.set(item, CAMPOS[col_idx], combo.get())
                        combo.destroy()
                    combo.bind("<Return>", guardar_combo)
                    combo.bind("<FocusOut>", guardar_combo)
                else:
                    entry = tk.Entry(tree)
                    entry.place(x=x, y=y, width=width, height=height)
                    entry.insert(0, valor_actual)
                    entry.focus()
                    def guardar_edicion(e=None):
                        tree.set(item, CAMPOS[col_idx], entry.get())
                        entry.destroy()
                    entry.bind("<Return>", guardar_edicion)
                    entry.bind("<FocusOut>", guardar_edicion)
            elif col_idx == CAMPOS.index("no_aplicacion"):
                entry = tk.Entry(tree)
                entry.place(x=x, y=y, width=width, height=height)
                entry.insert(0, valor_actual)
                entry.focus()
                def guardar_no_aplicacion(e=None):
                    tree.set(item, CAMPOS[col_idx], entry.get())
                    entry.destroy()
                entry.bind("<Return>", guardar_no_aplicacion)
                entry.bind("<FocusOut>", guardar_no_aplicacion)
        tree.bind("<Double-1>", editar_celda)
        # Botón guardar cambios
        def guardar_cambios():
            nuevos = []
            for iid in tree.get_children():
                nuevos.append([tree.set(iid, c) for c in columns])
            with open(CSV_FILE, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(columns)
                for fila in nuevos:
                    writer.writerow(fila)
            # Sincronizar a GitHub Gist
            if sincronizar_a_gist():
                messagebox.showinfo("Éxito", "Cambios guardados y sincronizados correctamente.")
            else:
                messagebox.showwarning("Advertencia", "Cambios guardados localmente, pero no se pudo sincronizar con la nube.")
            editor.destroy()

        def exportar_pdf():
            try:
                from fpdf import FPDF
            except ImportError:
                messagebox.showerror("Error", "Debe instalar el paquete 'fpdf' para exportar a PDF.\nEjecute: pip install fpdf")
                return
            from tkinter import filedialog
            archivo = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("Archivo PDF", "*.pdf")], title="Guardar como PDF")
            if not archivo:
                return
            # Obtener los datos filtrados actualmente en el treeview
            datos = []
            for iid in tree.get_children():
                datos.append([tree.set(iid, c) for c in columns])
            pdf = FPDF(orientation='L', unit='mm', format='A4')
            pdf.add_page()
            pdf.set_font("Arial", size=9)
            # Encabezados
            col_width = max(25, 277 // len(columns))
            for col in columns:
                pdf.cell(col_width, 8, col, border=1)
            pdf.ln()
            # Filas
            for fila in datos:
                for valor in fila:
                    pdf.cell(col_width, 8, str(valor), border=1)
                pdf.ln()
            try:
                pdf.output(archivo)
                messagebox.showinfo("Éxito", f"Registros exportados a {archivo}")
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo exportar el PDF:\n{e}")

        btn_pdf = ttk.Button(bottom_frame, text="Exportar a PDF", command=exportar_pdf)
        btn_pdf.pack(side="right", padx=10)

    def __init__(self, root):
        self.root = root
        self.lotes_por_sucursal = {s: [f"L{i} - {s}" for i in range(1, 33)] for s in SUCURSALES}
        # Cambiar título y poner icono
        self.root.title("Los Cielos Farm E/S")
        try:
            icon_path = os.path.join(BASE_PATH, "icon.png")
            if os.path.exists(icon_path):
                self.root.iconphoto(True, tk.PhotoImage(file=icon_path))
        except Exception as e:
            pass  # Si hay error, continuar sin icono
        
        # Sincronizar desde Gist al iniciar
        self.root.config(cursor="watch")
        self.root.update()
        if sincronizar_desde_gist():
            print("Datos sincronizados desde GitHub Repo")
            self.gist_conectado = True
        else:
            print("No se pudo sincronizar, usando datos locales")
            self.gist_conectado = False
        self.root.config(cursor="")
        
        self.crear_widgets()
        self.crear_barra_estado()
        
        # Botón para abrir el editor de registros
        btn_editar = ttk.Button(self.root, text="Filtrar registro", command=self.abrir_editor_registros)
        btn_editar.grid(row=1, column=0, pady=5, sticky="w")
    
    def crear_barra_estado(self):
        """Crea la barra de estado inferior con indicador de conexión"""
        import webbrowser
        
        VERSION = "v1.0.0"
        
        status_frame = ttk.Frame(self.root)
        status_frame.grid(row=2, column=0, sticky="ew", pady=(10, 5), padx=5)
        
        # Indicador de conexión
        if self.gist_conectado:
            color = "#2ecc71"  # Verde
            texto = "● Conectado"
        else:
            color = "#e74c3c"  # Rojo
            texto = "● Sin conexión"
        
        self.lbl_status = tk.Label(status_frame, text=texto, fg=color, font=("Arial", 9, "bold"))
        self.lbl_status.pack(side="left", padx=(0, 10))
        
        # Link al Repo
        repo_url = f"https://github.com/{GITHUB_REPO}/blob/main/{REPO_FILENAME}"
        lbl_link = tk.Label(status_frame, text=f"GitHub: {GITHUB_REPO}", fg="#3498db", cursor="hand2", font=("Arial", 9, "underline"))
        lbl_link.pack(side="left")
        lbl_link.bind("<Button-1>", lambda e: webbrowser.open(repo_url))
        
        # Versión
        lbl_version = tk.Label(status_frame, text=VERSION, fg="#7f8c8d", font=("Arial", 9))
        lbl_version.pack(side="right", padx=(10, 5))
        
        # Botón para refrescar conexión
        btn_refresh = ttk.Button(status_frame, text="↻ Sincronizar", width=12, command=self.refrescar_conexion)
        btn_refresh.pack(side="right", padx=5)
        
        # Botón para exportar CSV
        btn_exportar = ttk.Button(status_frame, text="📥 Exportar CSV", width=14, command=self.exportar_csv_local)
        btn_exportar.pack(side="right", padx=5)
    
    def exportar_csv_local(self):
        """Exporta el registro.csv a una ubicación elegida por el usuario"""
        from tkinter import filedialog
        
        if not os.path.exists(CSV_FILE):
            messagebox.showerror("Error", "No hay datos para exportar.")
            return
        
        fecha_actual = datetime.now().strftime('%Y-%m-%d')
        nombre_archivo = f"registro_{fecha_actual}.csv"
        
        archivo = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("Archivo CSV", "*.csv")],
            title="Exportar registro CSV",
            initialfile=nombre_archivo
        )
        
        if archivo:
            import shutil
            shutil.copy(CSV_FILE, archivo)
            messagebox.showinfo("Éxito", f"Registro exportado a:\n{archivo}")
    
    def refrescar_conexion(self):
        """Refresca la conexión con el Repo"""
        self.root.config(cursor="watch")
        self.root.update()
        
        if sincronizar_desde_gist():
            self.gist_conectado = True
            self.lbl_status.config(text="● Conectado", fg="#2ecc71")
            messagebox.showinfo("Éxito", "Datos sincronizados desde GitHub Repo")
        else:
            self.gist_conectado = False
            self.lbl_status.config(text="● Sin conexión", fg="#e74c3c")
            messagebox.showwarning("Error", "No se pudo conectar con GitHub Gist")
        
        self.root.config(cursor="")

    def guardar_registro(self):
        tipo = self.tipo_movimiento.get()
        plantas_val = self.plantas.get() if tipo != "Salida" else "0"
        motivo = self.motivo.get()
        variedad_mix_val = ""
        # Si variedad es MIX, el valor de motivo va en variedad_mix y motivo queda vacío
        if self.variedad.get() == "MIX":
            variedad_mix_val = motivo
            motivo_val = ""
        else:
            variedad_mix_val = ""
            motivo_val = motivo
        cliente = self.cliente.get() if (tipo == "Salida" and motivo == "venta") else ""
        gramos_val = self.gramos.get()
        try:
            gramos_float = float(gramos_val)
            if tipo == "Salida":
                gramos_val = str(-abs(gramos_float))
            else:
                gramos_val = str(abs(gramos_float))
        except Exception:
            pass  # Si no es numérico, se guarda como está y la validación lo atrapará después
        no_aplicacion_val = ""  # Se edita desde Filtrar registro
        datos = [
            self.fecha.get(),
            self.variedad.get(),
            self.colaborador.get() if tipo != "Salida" else "",
            gramos_val,
            plantas_val,
            self.supervisor.get(),
            self.sucursal.get(),
            self.lote.get(),
            motivo_val,
            variedad_mix_val,
            cliente,
            no_aplicacion_val,
            tipo
        ]
        # Validación básica
        if tipo == "Salida":
            campos_obligatorios = [self.fecha.get(), self.variedad.get(), self.gramos.get(), self.supervisor.get(), self.sucursal.get(), self.lote.get()]
            # motivo solo es obligatorio si variedad != 'MIX'
            if not (self.variedad.get() == "MIX"):
                campos_obligatorios.append(motivo)
            if motivo == "venta":
                campos_obligatorios.append(cliente)
        else:
            campos_obligatorios = [self.fecha.get(), self.variedad.get(), self.gramos.get(), plantas_val, self.supervisor.get(), self.sucursal.get(), self.lote.get()]
            # motivo solo es obligatorio si variedad != 'MIX'
            if not (self.variedad.get() == "MIX"):
                campos_obligatorios.append(motivo)
            # Colaborador es opcional (se puede dejar en blanco)
            # variedad_mix NO es obligatorio nunca
        if not all(campos_obligatorios):
            messagebox.showerror("Error", "Todos los campos son obligatorios.")
            return
        try:
            float(self.gramos.get())  # gramos debe ser numérico
            if tipo != "Salida":
                int(plantas_val)  # plantas debe ser entero solo para Entrada
        except ValueError:
            if tipo != "Salida":
                messagebox.showerror("Error", "Los campos 'gramos' y 'plantas' deben ser numéricos.")
            else:
                messagebox.showerror("Error", "El campo 'gramos' debe ser numérico.")
            return
        # Escribir en CSV
        archivo_nuevo = not os.path.exists(CSV_FILE)
        # Si el archivo existe pero no tiene la columna 'variedad_mix', 'motivo' o 'cliente', rehacer encabezado y migrar filas
        if not archivo_nuevo:
            with open(CSV_FILE, 'r', encoding='utf-8') as f:
                filas = list(csv.reader(f))
            encabezado = filas[0] if filas else []
            esperado = CAMPOS + ["tipo"]
            # Si falta variedad_mix o el orden es incorrecto, migrar
            if encabezado != esperado:
                nuevas_filas = []
                for fila in filas[1:]:
                    fila_dict = dict(zip(encabezado, fila))
                    nueva = [
                        fila_dict.get("fecha", ""),
                        fila_dict.get("variedad", ""),
                        fila_dict.get("colaborador", ""),
                        fila_dict.get("gramos", ""),
                        fila_dict.get("plantas", "0"),
                        fila_dict.get("supervisor", ""),
                        fila_dict.get("sucursal", ""),
                        fila_dict.get("lote", ""),
                        fila_dict.get("motivo", ""),
                        fila_dict.get("variedad_mix", ""),
                        fila_dict.get("cliente", fila_dict.get("quien", "")),
                        fila_dict.get("no_aplicacion", ""),
                        fila_dict.get("tipo", "Entrada")
                    ]
                    nuevas_filas.append(nueva)
                with open(CSV_FILE, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow(esperado)
                    for fila in nuevas_filas:
                        writer.writerow(fila)
        # Ahora sí, agregar el nuevo registro
        try:
            # Antes de abrir en append, asegurarse de que el archivo termina en salto de línea
            if os.path.exists(CSV_FILE):
                with open(CSV_FILE, 'rb+') as f:
                    f.seek(0, 2)
                    if f.tell() > 0:
                        f.seek(-1, 2)
                        last_char = f.read(1)
                        if last_char != b'\n':
                            f.write(b'\n')
            with open(CSV_FILE, 'a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                if archivo_nuevo:
                    writer.writerow(CAMPOS + ["tipo"])
                writer.writerow(datos)
            # Sincronizar a GitHub Gist
            if sincronizar_a_gist():
                messagebox.showinfo("Éxito", "Registro guardado y sincronizado correctamente.")
            else:
                messagebox.showwarning("Advertencia", "Registro guardado localmente, pero no se pudo sincronizar con la nube.")
            self.limpiar_campos()
        except Exception as e:
            messagebox.showerror("Error al guardar", f"No se pudo guardar el registro en el archivo:\n{CSV_FILE}\n\nError: {e}\n\nVerifique permisos de escritura en la carpeta.")

    def crear_widgets(self):
        tab_control = ttk.Notebook(self.root)
        tab_control.grid(row=0, column=0, sticky="nsew")

        # Tab 1: Registro
        frame = ttk.Frame(tab_control, padding=10)
        tab_control.add(frame, text="Registro")

        # Fecha
        ttk.Label(frame, text="Fecha:").grid(row=0, column=0, sticky="e")
        self.fecha = DateEntry(frame, date_pattern='yyyy-mm-dd', width=12, locale='es_ES')
        self.fecha.set_date(datetime.now())
        self.fecha.grid(row=0, column=1, padx=5, pady=2)
        
        # Variedad
        ttk.Label(frame, text="Variedad:").grid(row=1, column=0, sticky="e")
        self.variedad = ttk.Combobox(frame, values=VARIEDADES, state="readonly")
        self.variedad.grid(row=1, column=1, padx=5, pady=2)
        self.variedad.set("")

        # Tipo de movimiento: Entrada o Salida
        ttk.Label(frame, text="Tipo:").grid(row=0, column=2, sticky="e")
        self.tipo_movimiento = ttk.Combobox(frame, values=["Entrada", "Salida"], state="readonly", width=10)
        self.tipo_movimiento.grid(row=0, column=3, padx=5, pady=2)
        self.tipo_movimiento.set("Entrada")

        # Motivo y Quién (visibilidad dinámica)
        self.label_motivo = ttk.Label(frame, text="Motivo:")
        self.motivo = ttk.Combobox(frame, state="readonly")
        self.label_cliente = ttk.Label(frame, text="Cliente (si venta):")
        self.cliente = ttk.Entry(frame)
        self.motivo.set("")
        self.cliente.delete(0, "end")

        # Colaborador y Supervisor (visibilidad dinámica)
        self.label_colaborador = ttk.Label(frame, text="Colaborador:")
        self.colaborador = ttk.Combobox(frame, values=COLABORADORES, state="readonly")
        self.label_supervisor = ttk.Label(frame, text="Supervisor:")
        self.supervisor = ttk.Combobox(frame, values=SUPERVISORES, state="readonly")
        self.label_gramos = ttk.Label(frame, text="Gramos:")
        GRAMOS = [str(i) for i in range(0, 201)]
        self.gramos = ttk.Combobox(frame, values=GRAMOS, state="normal")
        self.label_plantas = ttk.Label(frame, text="Plantas:")
        self.plantas = ttk.Combobox(frame, values=[str(i) for i in range(0, 101)], state="normal")
        self.label_no_aplicacion = ttk.Label(frame, text="No. Aplicación:")
        self.no_aplicacion = ttk.Entry(frame)
        self.colaborador.set("")
        self.supervisor.set("")
        self.gramos.set("")
        self.plantas.set("0")

        # Sucursal (la posición se ajusta dinámicamente)
        self.sucursal_label = ttk.Label(frame, text="Sucursal:")
        self.sucursal = ttk.Combobox(frame, values=SUCURSALES, state="readonly")
        self.sucursal.set("")
        self.sucursal.bind("<<ComboboxSelected>>", self.actualizar_lotes)

        # Lote (la posición se ajusta dinámicamente)
        self.label_lote = ttk.Label(frame, text="Lote:")
        self.lote = ttk.Combobox(frame, state="readonly")
        self.lote.set("")
        self.lote['values'] = []

        # Botón Guardar (la posición se ajusta dinámicamente)
        self.btn_guardar = ttk.Button(frame, text="Guardar Registro", command=self.guardar_registro)

        # Mostrar/ocultar campos según tipo y motivo
        def on_tipo_change(event=None):
            tipo = self.tipo_movimiento.get()
            variedad = self.variedad.get()
            # Motivos según tipo y variedad
            if variedad == "MIX":
                # Si es MIX, los motivos son las otras variedades
                motivos = [v for v in VARIEDADES if v != "MIX"]
            elif tipo == "Salida":
                motivos = ["venta", "pre-rolls", "mix", "ajuste"]
            else:
                # Entrada tiene todas las opciones
                motivos = ["inventario", "trim", "traslado", "flor", "mix", "ajuste"]
            self.motivo['values'] = motivos
            self.motivo.set("")
            # Motivo siempre en la fila 6
            self.label_motivo.grid(row=6, column=0, sticky="e")
            self.motivo.grid(row=6, column=1, padx=5, pady=2)
            # Cambiar etiqueta de motivo si es MIX
            if variedad == "MIX":
                self.label_motivo.config(text="Variedad del Mix:")
            else:
                self.label_motivo.config(text="Motivo:")
            # Quién solo si salida y motivo=venta
            def on_motivo_change(event2=None):
                if self.tipo_movimiento.get() == "Salida" and self.motivo.get() == "venta":
                    self.label_cliente.grid(row=7, column=0, sticky="e")
                    self.cliente.grid(row=7, column=1, padx=5, pady=2)
                else:
                    self.label_cliente.grid_remove()
                    self.cliente.grid_remove()
            self.motivo.bind("<<ComboboxSelected>>", on_motivo_change)
            on_motivo_change()
            if tipo == "Salida":
                self.label_colaborador.grid_remove()
                self.colaborador.grid_remove()
                self.label_supervisor.grid(row=2, column=0, sticky="e")
                self.supervisor.grid(row=2, column=1, padx=5, pady=2)
                self.label_gramos.grid(row=3, column=0, sticky="e")
                self.gramos.grid(row=3, column=1, padx=5, pady=2)
                # Ocultar campo plantas y no_aplicacion
                self.label_plantas.grid_remove()
                self.plantas.grid_remove()
                self.label_no_aplicacion.grid_remove()
                self.no_aplicacion.grid_remove()
                # Sucursal y lote en filas 4 y 5
                self.sucursal_label_row = 4
                self.lote_label_row = 5
                self.sucursal_label.grid(row=self.sucursal_label_row, column=0, sticky="e")
                self.sucursal.grid(row=self.sucursal_label_row, column=1, padx=5, pady=2)
                self.label_lote.grid(row=self.lote_label_row, column=0, sticky="e")
                self.lote.grid(row=self.lote_label_row, column=1, padx=5, pady=2)
                # Botón guardar en la fila 8 (después de motivo y cliente)
                self.btn_guardar.grid(row=8, column=0, columnspan=2, pady=10)
            else:
                self.label_colaborador.grid(row=2, column=0, sticky="e")
                self.colaborador.grid(row=2, column=1, padx=5, pady=2)
                self.label_supervisor.grid(row=3, column=0, sticky="e")
                self.supervisor.grid(row=3, column=1, padx=5, pady=2)
                self.label_gramos.grid(row=4, column=0, sticky="e")
                self.gramos.grid(row=4, column=1, padx=5, pady=2)
                self.label_plantas.grid(row=5, column=0, sticky="e")
                self.plantas.grid(row=5, column=1, padx=5, pady=2)
                # Ocultar campo no_aplicacion (se edita en Filtrar registro)
                self.label_no_aplicacion.grid_remove()
                self.no_aplicacion.grid_remove()
                # Sucursal y lote en filas 6 y 7
                self.sucursal_label_row = 6
                self.lote_label_row = 7
                self.sucursal_label.grid(row=self.sucursal_label_row, column=0, sticky="e")
                self.sucursal.grid(row=self.sucursal_label_row, column=1, padx=5, pady=2)
                self.label_lote.grid(row=self.lote_label_row, column=0, sticky="e")
                self.lote.grid(row=self.lote_label_row, column=1, padx=5, pady=2)
                # Motivo en fila 8 para Entrada
                self.label_motivo.grid(row=8, column=0, sticky="e")
                self.motivo.grid(row=8, column=1, padx=5, pady=2)
                self.btn_guardar.grid(row=9, column=0, columnspan=2, pady=10)
        self.tipo_movimiento.bind("<<ComboboxSelected>>", on_tipo_change)
        self.variedad.bind("<<ComboboxSelected>>", on_tipo_change)
        on_tipo_change()

        # Tab 2: Gráficos Generales
        graficos_frame = ttk.Frame(tab_control, padding=10)
        tab_control.add(graficos_frame, text="Gráficos Generales")

        # Filtros de fecha
        ttk.Label(graficos_frame, text="Fecha desde:").grid(row=0, column=0, sticky="e")
        self.filtro_fecha_desde = DateEntry(graficos_frame, date_pattern='yyyy-mm-dd', width=12, locale='es_ES')
        self.filtro_fecha_desde.grid(row=0, column=1, padx=5, pady=2)
        self.filtro_fecha_desde.delete(0, "end")  # Dejar vacío por defecto

        ttk.Label(graficos_frame, text="Fecha hasta:").grid(row=0, column=2, sticky="e")
        self.filtro_fecha_hasta = DateEntry(graficos_frame, date_pattern='yyyy-mm-dd', width=12, locale='es_ES')
        self.filtro_fecha_hasta.grid(row=0, column=3, padx=5, pady=2)
        self.filtro_fecha_hasta.delete(0, "end")  # Dejar vacío por defecto

        # Filtros generales
        ttk.Label(graficos_frame, text="Variedad:").grid(row=1, column=0, sticky="e")
        self.filtro_g_variedad = ttk.Combobox(graficos_frame, values=["Todas"] + VARIEDADES, state="readonly")
        self.filtro_g_variedad.grid(row=1, column=1, padx=5, pady=2)
        self.filtro_g_variedad.set("")

        ttk.Label(graficos_frame, text="Sucursal:").grid(row=2, column=0, sticky="e")
        self.filtro_g_sucursal = ttk.Combobox(graficos_frame, values=["Todas"] + SUCURSALES, state="readonly")
        self.filtro_g_sucursal.grid(row=2, column=1, padx=5, pady=2)
        self.filtro_g_sucursal.set("")
        self.filtro_g_sucursal.bind("<<ComboboxSelected>>", self.actualizar_lotes_graficos)

        ttk.Label(graficos_frame, text="Colaborador:").grid(row=3, column=0, sticky="e")
        self.filtro_g_colaborador = ttk.Combobox(graficos_frame, values=["Todas"] + COLABORADORES, state="readonly")
        self.filtro_g_colaborador.grid(row=3, column=1, padx=5, pady=2)
        self.filtro_g_colaborador.set("")

        ttk.Label(graficos_frame, text="Supervisor:").grid(row=4, column=0, sticky="e")
        self.filtro_g_supervisor = ttk.Combobox(graficos_frame, values=["Todas"] + SUPERVISORES, state="readonly")
        self.filtro_g_supervisor.grid(row=4, column=1, padx=5, pady=2)
        self.filtro_g_supervisor.set("")

        ttk.Label(graficos_frame, text="Lote:").grid(row=5, column=0, sticky="e")
        self.filtro_g_lote = ttk.Combobox(graficos_frame, state="readonly")
        self.filtro_g_lote.grid(row=5, column=1, padx=5, pady=2)
        self.filtro_g_lote.set("")
        self.filtro_g_lote['values'] = ["Todas"]

        # Filtro Motivo
        ttk.Label(graficos_frame, text="Motivo:").grid(row=6, column=0, sticky="e")
        self.filtro_g_motivo = ttk.Combobox(graficos_frame, values=["Todas", "inventario", "trim", "traslado", "flor", "venta", "pre-rolls", "mix"], state="readonly")
        self.filtro_g_motivo.grid(row=6, column=1, padx=5, pady=2)
        self.filtro_g_motivo.set("")

        # Filtro Cliente (solo para ventas)
        ttk.Label(graficos_frame, text="Cliente (si venta):").grid(row=7, column=0, sticky="e")
        self.filtro_g_cliente = ttk.Entry(graficos_frame)
        self.filtro_g_cliente.grid(row=7, column=1, padx=5, pady=2)

        # Campo a graficar
        ttk.Label(graficos_frame, text="Campo a graficar:").grid(row=8, column=0, sticky="e")
        self.campo_grafico = ttk.Combobox(graficos_frame, values=["variedad", "sucursal", "colaborador", "supervisor", "lote", "motivo", "cliente"], state="readonly")
        self.campo_grafico.grid(row=8, column=1, padx=5, pady=2)
        self.campo_grafico.set("variedad")

        # Switch para modo gráfico o lista
        self.modo_lista = tk.BooleanVar(value=False)
        self.switch_modo = ttk.Checkbutton(graficos_frame, text="Mostrar como lista descriptiva", variable=self.modo_lista)
        self.switch_modo.grid(row=9, column=0, columnspan=2, pady=2)

        # Botón para mostrar gráfico general o lista (debe ir debajo del switch, en la siguiente fila)
        self.btn_grafico_general = ttk.Button(graficos_frame, text="Mostrar resultado", command=self.mostrar_grafico_general_unico)
        self.btn_grafico_general.grid(row=10, column=0, columnspan=2, pady=10)

        # Tab 3: Arqueo por Lote
        corte_frame = ttk.Frame(tab_control, padding=10)
        tab_control.add(corte_frame, text="Arqueo por Lote")

        ttk.Label(corte_frame, text="=== ARQUEO POR LOTE ===", font=("Arial", 12, "bold")).grid(row=0, column=0, columnspan=4, pady=10)

        # Selección de sucursal para filtrar lotes
        ttk.Label(corte_frame, text="Sucursal:").grid(row=1, column=0, sticky="e")
        self.corte_sucursal = ttk.Combobox(corte_frame, values=["TODOS"] + SUCURSALES, state="readonly")
        self.corte_sucursal.grid(row=1, column=1, padx=5, pady=2)
        self.corte_sucursal.set("")
        self.corte_sucursal.bind("<<ComboboxSelected>>", self.actualizar_lotes_corte)

        # Selección de lote
        ttk.Label(corte_frame, text="Lote:").grid(row=2, column=0, sticky="e")
        self.corte_lote = ttk.Combobox(corte_frame, state="readonly")
        self.corte_lote.grid(row=2, column=1, padx=5, pady=2)
        self.corte_lote.set("")

        # Fecha inicial
        ttk.Label(corte_frame, text="Fecha desde:").grid(row=3, column=0, sticky="e")
        self.corte_fecha_desde = DateEntry(corte_frame, date_pattern='yyyy-mm-dd', width=12, locale='es_ES')
        self.corte_fecha_desde.grid(row=3, column=1, padx=5, pady=2)
        self.corte_fecha_desde.delete(0, "end")

        # Fecha final
        ttk.Label(corte_frame, text="Fecha hasta:").grid(row=3, column=2, sticky="e")
        self.corte_fecha_hasta = DateEntry(corte_frame, date_pattern='yyyy-mm-dd', width=12, locale='es_ES')
        self.corte_fecha_hasta.grid(row=3, column=3, padx=5, pady=2)

        # Botones
        btn_frame_corte = ttk.Frame(corte_frame)
        btn_frame_corte.grid(row=4, column=0, columnspan=2, pady=10)
        
        ttk.Button(btn_frame_corte, text="Ver Resumen", command=self.ver_resumen_corte).pack(side="left", padx=5)
        ttk.Button(btn_frame_corte, text="Exportar PDF", command=self.exportar_corte_pdf).pack(side="left", padx=5)
        ttk.Button(btn_frame_corte, text="Exportar TXT", command=self.exportar_corte_txt).pack(side="left", padx=5)
        ttk.Button(btn_frame_corte, text="Archivar y Cerrar Lote", command=self.archivar_corte).pack(side="left", padx=5)

        # Área de texto para mostrar el resumen
        self.corte_texto = tk.Text(corte_frame, wrap="word", font=("Courier", 10), height=25, width=80)
        self.corte_texto.grid(row=5, column=0, columnspan=4, padx=5, pady=5, sticky="nsew")
        corte_frame.grid_rowconfigure(5, weight=1)
        corte_frame.grid_columnconfigure(3, weight=1)

        # Scrollbar para el texto
        corte_scroll = ttk.Scrollbar(corte_frame, orient="vertical", command=self.corte_texto.yview)
        corte_scroll.grid(row=5, column=4, sticky="ns")
        self.corte_texto.configure(yscrollcommand=corte_scroll.set)

    def actualizar_lotes_corte(self, event=None):
        """Actualiza los lotes disponibles según la sucursal seleccionada"""
        sucursal = self.corte_sucursal.get()
        if sucursal == "TODOS":
            # Mostrar todos los lotes de todas las sucursales
            todos_lotes = ["TODOS"]
            for lotes in self.lotes_por_sucursal.values():
                todos_lotes.extend(lotes)
            # Eliminar duplicados manteniendo orden
            lotes_unicos = list(dict.fromkeys(todos_lotes))
            self.corte_lote['values'] = lotes_unicos
        elif sucursal in self.lotes_por_sucursal:
            self.corte_lote['values'] = ["TODOS"] + self.lotes_por_sucursal[sucursal]
        else:
            self.corte_lote['values'] = []
        self.corte_lote.set("")

    def generar_resumen_corte(self):
        """Genera el resumen del corte mensual para el lote seleccionado"""
        lote = self.corte_lote.get()
        fecha_desde = self.corte_fecha_desde.get().strip()
        fecha_hasta = self.corte_fecha_hasta.get().strip()
        sucursal = self.corte_sucursal.get()
        
        if not lote or not sucursal:
            messagebox.showerror("Error", "Debe seleccionar sucursal y lote.")
            return None
        
        if not os.path.exists(CSV_FILE):
            messagebox.showerror("Error", "No hay datos registrados.")
            return None
        
        df = pd.read_csv(CSV_FILE)
        
        # Filtrar por sucursal y lote
        df["fecha"] = pd.to_datetime(df["fecha"], errors="coerce")
        
        # Aplicar filtro de sucursal
        if sucursal != "TODOS":
            df_filtrado = df[df["sucursal"] == sucursal].copy()
        else:
            df_filtrado = df.copy()
        
        # Aplicar filtro de lote
        if lote != "TODOS":
            df_lote = df_filtrado[df_filtrado["lote"] == lote].copy()
        else:
            df_lote = df_filtrado.copy()
        
        # Aplicar filtro de fechas si están definidas
        if fecha_desde:
            df_lote = df_lote[df_lote["fecha"] >= pd.to_datetime(fecha_desde)]
        if fecha_hasta:
            df_lote = df_lote[df_lote["fecha"] <= pd.to_datetime(fecha_hasta)]
        
        if df_lote.empty:
            rango = ""
            if fecha_desde and fecha_hasta:
                rango = f" entre {fecha_desde} y {fecha_hasta}"
            elif fecha_desde:
                rango = f" desde {fecha_desde}"
            elif fecha_hasta:
                rango = f" hasta {fecha_hasta}"
            return f"No hay registros para el lote {lote}{rango}"
        
        # Convertir gramos a numérico
        df_lote["gramos"] = pd.to_numeric(df_lote["gramos"], errors="coerce").fillna(0)
        df_lote["plantas"] = pd.to_numeric(df_lote["plantas"], errors="coerce").fillna(0)
        
        # Separar entradas y salidas
        df_entradas = df_lote[df_lote["tipo"] == "Entrada"]
        df_salidas = df_lote[df_lote["tipo"] == "Salida"]
        
        # Calcular totales
        total_gramos_entrada = df_entradas["gramos"].sum()
        total_plantas_entrada = df_entradas["plantas"].sum()
        total_gramos_salida = abs(df_salidas["gramos"].sum())  # Salidas son negativas
        
        # Balance
        balance_gramos = total_gramos_entrada - total_gramos_salida
        
        # Desglose por variedad
        entradas_por_variedad = df_entradas.groupby("variedad").agg({
            "gramos": "sum",
            "plantas": "sum"
        }).sort_values("gramos", ascending=False)
        
        salidas_por_variedad = df_salidas.groupby("variedad")["gramos"].sum().abs().sort_values(ascending=False)
        
        # Desglose de salidas por motivo
        salidas_por_motivo = df_salidas.groupby("motivo")["gramos"].sum().abs().sort_values(ascending=False)
        
        # Ventas por cliente
        df_ventas = df_salidas[df_salidas["motivo"] == "venta"]
        ventas_por_cliente = df_ventas.groupby("cliente")["gramos"].sum().abs().sort_values(ascending=False)
        
        # Desglose por colaborador
        entradas_por_colaborador = df_entradas.groupby("colaborador").agg({
            "gramos": "sum",
            "plantas": "sum"
        }).sort_values("gramos", ascending=False)
        
        # Generar reporte
        lineas = []
        lineas.append("=" * 60)
        titulo_lote = "TODOS LOS LOTES" if lote == "TODOS" else lote
        titulo_sucursal = "TODAS LAS SUCURSALES" if sucursal == "TODOS" else sucursal
        lineas.append(f"       ARQUEO - {titulo_lote}")
        lineas.append(f"       Sucursal: {titulo_sucursal}")
        if fecha_desde and fecha_hasta:
            lineas.append(f"       Período: {fecha_desde} al {fecha_hasta}")
        elif fecha_desde:
            lineas.append(f"       Desde: {fecha_desde}")
        elif fecha_hasta:
            lineas.append(f"       Hasta: {fecha_hasta}")
        else:
            lineas.append(f"       Período: Todo el historial")
        lineas.append(f"       Generado: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        lineas.append("=" * 60)
        lineas.append("")
        
        lineas.append(">>> RESUMEN GENERAL <<<")
        lineas.append("-" * 40)
        lineas.append(f"Total Entradas:     {total_gramos_entrada:,.2f} gramos")
        lineas.append(f"Total Plantas:      {int(total_plantas_entrada)} plantas")
        lineas.append(f"Total Salidas:      {total_gramos_salida:,.2f} gramos")
        lineas.append(f"BALANCE FINAL:      {balance_gramos:,.2f} gramos")
        lineas.append("")
        
        lineas.append(">>> ENTRADAS POR VARIEDAD <<<")
        lineas.append("-" * 40)
        for var, row in entradas_por_variedad.iterrows():
            lineas.append(f"  {var:20} {row['gramos']:>10,.2f}g  ({int(row['plantas'])} plantas)")
        lineas.append("")
        
        lineas.append(">>> SALIDAS POR VARIEDAD <<<")
        lineas.append("-" * 40)
        for var, gramos in salidas_por_variedad.items():
            lineas.append(f"  {var:20} {gramos:>10,.2f}g")
        lineas.append("")
        
        lineas.append(">>> SALIDAS POR MOTIVO <<<")
        lineas.append("-" * 40)
        for motivo, gramos in salidas_por_motivo.items():
            lineas.append(f"  {motivo:20} {gramos:>10,.2f}g")
        lineas.append("")
        
        if not ventas_por_cliente.empty:
            lineas.append(">>> VENTAS POR CLIENTE <<<")
            lineas.append("-" * 40)
            for cliente, gramos in ventas_por_cliente.items():
                if cliente and str(cliente).strip():
                    lineas.append(f"  {str(cliente):20} {gramos:>10,.2f}g")
            lineas.append("")
        
        lineas.append(">>> PRODUCCIÓN POR COLABORADOR <<<")
        lineas.append("-" * 40)
        for colab, row in entradas_por_colaborador.iterrows():
            if colab and str(colab).strip():
                lineas.append(f"  {str(colab):20} {row['gramos']:>10,.2f}g  ({int(row['plantas'])} plantas)")
        lineas.append("")
        
        lineas.append("=" * 60)
        lineas.append(f"Total de registros en el período: {len(df_lote)}")
        lineas.append("=" * 60)
        
        return "\n".join(lineas)

    def ver_resumen_corte(self):
        """Muestra el resumen del corte en el área de texto"""
        resumen = self.generar_resumen_corte()
        if resumen:
            self.corte_texto.config(state="normal")
            self.corte_texto.delete("1.0", "end")
            self.corte_texto.insert("end", resumen)
            self.corte_texto.config(state="disabled")

    def exportar_corte_txt(self):
        """Exporta el corte a archivo TXT"""
        resumen = self.generar_resumen_corte()
        if not resumen:
            return
        
        # Crear carpeta registros si no existe
        carpeta_registros = os.path.join(BASE_PATH, "registros")
        if not os.path.exists(carpeta_registros):
            os.makedirs(carpeta_registros)
        
        from tkinter import filedialog
        lote = self.corte_lote.get().replace(" ", "_")
        fecha_desde = self.corte_fecha_desde.get()
        fecha_hasta = self.corte_fecha_hasta.get()
        archivo = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Archivo de texto", "*.txt")],
            title="Guardar corte como TXT",
            initialdir=carpeta_registros,
            initialfilename=f"corte_{lote}_{fecha_desde}_a_{fecha_hasta}.txt"
        )
        if archivo:
            with open(archivo, "w", encoding="utf-8") as f:
                f.write(resumen)
            messagebox.showinfo("Éxito", f"Corte exportado a {archivo}")

    def exportar_corte_pdf(self):
        """Exporta el corte a archivo PDF"""
        resumen = self.generar_resumen_corte()
        if not resumen:
            return
        
        try:
            from fpdf import FPDF
        except ImportError:
            messagebox.showerror("Error", "Debe instalar fpdf: pip install fpdf")
            return
        
        # Crear carpeta registros si no existe
        carpeta_registros = os.path.join(BASE_PATH, "registros")
        if not os.path.exists(carpeta_registros):
            os.makedirs(carpeta_registros)
        
        from tkinter import filedialog
        lote = self.corte_lote.get().replace(" ", "_")
        fecha_desde = self.corte_fecha_desde.get()
        fecha_hasta = self.corte_fecha_hasta.get()
        archivo = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("Archivo PDF", "*.pdf")],
            title="Guardar corte como PDF",
            initialdir=carpeta_registros,
            initialfilename=f"corte_{lote}_{fecha_desde}_a_{fecha_hasta}.pdf"
        )
        if archivo:
            pdf = FPDF()
            pdf.add_page()
            pdf.set_auto_page_break(auto=True, margin=15)
            pdf.set_font("Courier", size=9)
            for linea in resumen.splitlines():
                pdf.multi_cell(0, 5, linea)
            pdf.output(archivo)
            messagebox.showinfo("Éxito", f"Corte exportado a {archivo}")

    def archivar_corte(self):
        """Exporta los registros del corte a un archivo histórico (sin eliminar del principal)"""
        lote = self.corte_lote.get()
        fecha_desde = self.corte_fecha_desde.get().strip()
        fecha_hasta = self.corte_fecha_hasta.get().strip()
        sucursal = self.corte_sucursal.get()
        
        if not lote or not sucursal:
            messagebox.showerror("Error", "Debe seleccionar sucursal y lote.")
            return
        
        if not os.path.exists(CSV_FILE):
            messagebox.showerror("Error", "No hay datos registrados.")
            return
        
        df = pd.read_csv(CSV_FILE)
        df["fecha"] = pd.to_datetime(df["fecha"], errors="coerce")
        
        # Filtrar registros a exportar
        df_exportar = df[df["lote"] == lote].copy()
        
        if fecha_desde:
            df_exportar = df_exportar[df_exportar["fecha"] >= pd.to_datetime(fecha_desde)]
        if fecha_hasta:
            df_exportar = df_exportar[df_exportar["fecha"] <= pd.to_datetime(fecha_hasta)]
        
        if df_exportar.empty:
            messagebox.showinfo("Info", f"No hay registros para exportar en {lote}")
            return
        
        # Nombre del archivo con rango de fechas
        if fecha_desde and fecha_hasta:
            fecha_archivo = f"{fecha_desde}_a_{fecha_hasta}"
        elif fecha_desde:
            fecha_archivo = f"desde_{fecha_desde}"
        elif fecha_hasta:
            fecha_archivo = f"hasta_{fecha_hasta}"
        else:
            fecha_archivo = datetime.now().strftime('%Y-%m-%d')
        
        # Confirmar acción
        respuesta = messagebox.askyesno(
            "Confirmar Exportación",
            f"¿Exportar corte del lote {lote}?\n\n"
            f"Se crearán archivos históricos con {len(df_exportar)} registros.\n"
            f"Los datos se MANTIENEN en el registro principal."
        )
        
        if not respuesta:
            return
        
        # Crear carpeta registros si no existe
        carpeta_registros = os.path.join(BASE_PATH, "registros")
        if not os.path.exists(carpeta_registros):
            os.makedirs(carpeta_registros)
        
        # Guardar archivo histórico
        archivo_historico = os.path.join(carpeta_registros, f"historico_{lote.replace(' ', '_')}_{fecha_archivo}.csv")
        
        # Convertir fecha a string para guardar
        df_exportar["fecha"] = df_exportar["fecha"].dt.strftime('%Y-%m-%d')
        
        # Guardar histórico
        df_exportar.to_csv(archivo_historico, index=False)
        
        # Generar y guardar resumen
        resumen = self.generar_resumen_corte()
        archivo_resumen = ""
        if resumen:
            archivo_resumen = os.path.join(carpeta_registros, f"resumen_{lote.replace(' ', '_')}_{fecha_archivo}.txt")
            with open(archivo_resumen, "w", encoding="utf-8") as f:
                f.write(resumen)
        
        messagebox.showinfo(
            "Éxito",
            f"Corte del lote {lote} exportado correctamente.\n\n"
            f"Registros exportados: {len(df_exportar)}\n"
            f"Archivo histórico: {archivo_historico}\n"
            f"Resumen guardado: {archivo_resumen}\n\n"
            f"Los datos siguen en el registro principal."
        )
        
        # Actualizar el área de texto
        self.corte_texto.config(state="normal")
        self.corte_texto.delete("1.0", "end")
        self.corte_texto.insert("end", f"Corte del lote {lote} exportado exitosamente.\n\n")
        self.corte_texto.insert("end", f"Archivos generados:\n")
        self.corte_texto.insert("end", f"  - {archivo_historico}\n")
        self.corte_texto.insert("end", f"  - {archivo_resumen}\n")
        self.corte_texto.config(state="disabled")

    def actualizar_lotes_graficos(self, event=None):
        # Leer los lotes disponibles según los filtros actuales en la pestaña de gráficos
        sucursal = self.filtro_g_sucursal.get().strip()
        variedad = self.filtro_g_variedad.get().strip()
        colaborador = self.filtro_g_colaborador.get().strip()
        supervisor = self.filtro_g_supervisor.get().strip()
        lotes_disponibles = set()
        if os.path.exists(CSV_FILE):
            df = pd.read_csv(CSV_FILE)
            for col in ["variedad", "colaborador", "supervisor", "sucursal", "lote"]:
                df[col] = df[col].astype(str).str.strip()
            # Aplicar filtros excepto lote
            if sucursal and sucursal != "Todas":
                df = df[df["sucursal"].str.upper() == sucursal.upper()]
            if variedad and variedad != "Todas":
                df = df[df["variedad"].str.upper() == variedad.upper()]
            if colaborador and colaborador != "Todas":
                df = df[df["colaborador"].str.upper() == colaborador.upper()]
            if supervisor and supervisor != "Todas":
                df = df[df["supervisor"].str.upper() == supervisor.upper()]
            lotes_disponibles = sorted(df["lote"].unique())
        if lotes_disponibles:
            self.filtro_g_lote['values'] = ["Todas"] + lotes_disponibles
        else:
            self.filtro_g_lote['values'] = ["Todas"]
        self.filtro_g_lote.set("")

    def actualizar_lotes(self, event=None):
        sucursal = self.sucursal.get()
        if sucursal in self.lotes_por_sucursal:
            self.lote['values'] = self.lotes_por_sucursal[sucursal]
        else:
            self.lote['values'] = []
        self.lote.set("")

    def mostrar_grafico_general_unico(self):
        if not os.path.exists(CSV_FILE):
            messagebox.showerror("Error", "No hay datos registrados.")
            return
        df = pd.read_csv(CSV_FILE)
        for col in ["variedad", "colaborador", "supervisor", "sucursal", "lote"]:
            df[col] = df[col].astype(str).str.strip()
        # Si existe la columna tipo, solo convertir gramos a numérico
        if "tipo" in df.columns:
            df["tipo"] = df["tipo"].fillna("").astype(str)
            df["gramos"] = pd.to_numeric(df["gramos"], errors="coerce")
            df = df.dropna(subset=["gramos"])
        else:
            df["gramos"] = pd.to_numeric(df["gramos"], errors="coerce")
            df = df.dropna(subset=["gramos"])
        
        # Filtrar por fecha
        fecha_desde = self.filtro_fecha_desde.get().strip()
        fecha_hasta = self.filtro_fecha_hasta.get().strip()
        if fecha_desde or fecha_hasta:
            df["fecha"] = pd.to_datetime(df["fecha"], errors="coerce")
            if fecha_desde:
                try:
                    df = df[df["fecha"] >= pd.to_datetime(fecha_desde)]
                except:
                    pass
            if fecha_hasta:
                try:
                    df = df[df["fecha"] <= pd.to_datetime(fecha_hasta)]
                except:
                    pass
        
        # Aplicar filtros
        filtros = {
            "variedad": self.filtro_g_variedad.get().strip(),
            "sucursal": self.filtro_g_sucursal.get().strip(),
            "colaborador": self.filtro_g_colaborador.get().strip(),
            "supervisor": self.filtro_g_supervisor.get().strip(),
            "lote": self.filtro_g_lote.get().strip(),
            "motivo": self.filtro_g_motivo.get().strip(),
            "cliente": self.filtro_g_cliente.get().strip()
        }
        for k, v in filtros.items():
            if v and v != "Todas":
                if k == "lote":
                    df = df[df[k] == v]
                elif k == "cliente":
                    df = df[df[k].str.contains(v, case=False, na=False)]
                else:
                    df = df[df[k].str.upper() == v.upper()]
        if df.empty:
            messagebox.showinfo("Sin datos", "No hay datos para los filtros seleccionados.")
            return
        campo = self.campo_grafico.get()
        # Switch entre modo gráfico y modo lista
        if self.modo_lista.get():
            filtros_aplicados = [k for k, v in filtros.items() if v and v != "Todas"]
            lista_descriptiva = []
            if len(filtros_aplicados) == 1 and campo in filtros_aplicados and campo != "sucursal":
                valor = filtros[campo]
                df_filtrado = df[df[campo].str.upper() == valor.upper()]
                resumen = df_filtrado.groupby("sucursal")["gramos"].sum().sort_values(ascending=False)
                def plantas_entrada(subdf):
                    if "tipo" in subdf.columns and "plantas" in subdf.columns:
                        mask_entrada = (subdf["tipo"].str.lower() == "entrada") | (subdf["tipo"].str.strip() == "")
                        return subdf.loc[mask_entrada, "plantas"].astype(float).sum()
                    elif "plantas" in subdf.columns:
                        return subdf["plantas"].astype(float).sum()
                    else:
                        return subdf.shape[0]
                if "tipo" in df_filtrado.columns and "plantas" in df_filtrado.columns:
                    mask_entrada = (df_filtrado["tipo"].str.lower() == "entrada") | (df_filtrado["tipo"].str.strip() == "")
                    conteos = df_filtrado.loc[mask_entrada].groupby("sucursal")["plantas"].apply(lambda x: x.astype(float).sum()).reindex(resumen.index, fill_value=0)
                elif "plantas" in df_filtrado.columns:
                    conteos = df_filtrado.groupby("sucursal")["plantas"].apply(lambda x: x.astype(float).sum()).reindex(resumen.index, fill_value=0)
                else:
                    conteos = df_filtrado.groupby("sucursal").size().reindex(resumen.index, fill_value=0)
                def lotes_con_plantas(subdf):
                    lotes = subdf["lote"].value_counts().sort_index()
                    gramos_por_lote = subdf.groupby("lote")["gramos"].sum()
                    if "tipo" in subdf.columns:
                        plantas_por_lote = subdf[subdf["tipo"].str.lower() == "entrada"].groupby("lote").size()
                    else:
                        plantas_por_lote = subdf.groupby("lote").size()
                    resultado = []
                    for lote, count in lotes.items():
                        gramos = gramos_por_lote.get(lote, 0)
                        plantas = plantas_por_lote.get(lote, 0)
                        resultado.append(f"{lote} ({plantas} planta{'s' if plantas != 1 else ''}, {gramos:.2f}grs)")
                    return ', '.join(resultado)
                lotes_por_sucursal = df_filtrado.groupby("sucursal").apply(lotes_con_plantas).reindex(resumen.index, fill_value='')
                for i, suc in enumerate(resumen.index):
                    lista_descriptiva.append(f"Sucursal: {suc}\n  Total gramos: {resumen.iloc[i]:.2f}\n  Plantas (solo Entrada): {conteos.iloc[i]}\n  Lotes: {lotes_por_sucursal.iloc[i]}")
            else:
                resumen = df.groupby(campo)["gramos"].sum().sort_values(ascending=False)
                if "tipo" in df.columns and "plantas" in df.columns:
                    mask_entrada = (df["tipo"].str.lower() == "entrada") | (df["tipo"].str.strip() == "")
                    conteos = df.loc[mask_entrada].groupby(campo)["plantas"].apply(lambda x: x.astype(float).sum()).reindex(resumen.index, fill_value=0)
                elif "plantas" in df.columns:
                    conteos = df.groupby(campo)["plantas"].apply(lambda x: x.astype(float).sum()).reindex(resumen.index, fill_value=0)
                else:
                    conteos = df.groupby(campo).size().reindex(resumen.index, fill_value=0)
                def lotes_con_plantas_grupo(subdf):
                    lotes = subdf["lote"].value_counts().sort_index()
                    gramos_por_lote = subdf.groupby("lote")["gramos"].sum()
                    if "tipo" in subdf.columns:
                        plantas_por_lote = subdf[subdf["tipo"].str.lower() == "entrada"].groupby("lote").size()
                    else:
                        plantas_por_lote = subdf.groupby("lote").size()
                    resultado = []
                    for lote, count in lotes.items():
                        gramos = gramos_por_lote.get(lote, 0)
                        plantas = plantas_por_lote.get(lote, 0)
                        resultado.append(f"{lote} ({plantas} planta{'s' if plantas != 1 else ''}, {gramos:.2f}grs)")
                    return ', '.join(resultado)
                lotes_por_grupo = df.groupby(campo).apply(lotes_con_plantas_grupo).reindex(resumen.index, fill_value='')
                for i, grupo in enumerate(resumen.index):
                    # Mostrar motivo y cliente si corresponde
                    if campo == "motivo":
                        subdf = df[df[campo] == grupo]
                        clientes = subdf["cliente"].dropna().unique()
                        clientes_str = f"\n  Cliente(s): {', '.join([str(c) for c in clientes if str(c).strip()])}" if len(clientes) > 0 else ""
                        lista_descriptiva.append(f"{campo.capitalize()}: {grupo}\n  Total gramos: {resumen.iloc[i]:.2f}\n  Plantas (solo Entrada): {conteos.iloc[i]}\n  Lotes: {lotes_por_grupo.iloc[i]}{clientes_str}")
                    elif campo == "cliente":
                        lista_descriptiva.append(f"{campo.capitalize()}: {grupo}\n  Total gramos: {resumen.iloc[i]:.2f}\n  Plantas (solo Entrada): {conteos.iloc[i]}\n  Lotes: {lotes_por_grupo.iloc[i]}")
                    else:
                        lista_descriptiva.append(f"{campo.capitalize()}: {grupo}\n  Total gramos: {resumen.iloc[i]:.2f}\n  Plantas (solo Entrada): {conteos.iloc[i]}\n  Lotes: {lotes_por_grupo.iloc[i]}")
            if "tipo" in df.columns and "plantas" in df.columns:
                total_plantas = df[df["tipo"].str.lower() == "entrada"]["plantas"].astype(float).sum()
            elif "plantas" in df.columns:
                total_plantas = df["plantas"].astype(float).sum()
            else:
                total_plantas = 0
            total_plantas_str = f"\nTOTAL GENERAL DE PLANTAS (solo Entrada): {int(total_plantas)}\n"
            total_registros = len(df)
            suma_gramos = df["gramos"].sum()
            promedio_gramos = df["gramos"].mean()

            max_registro = df.loc[df["gramos"].idxmax()]
            estadisticas = (
                f"\nEstadísticas generales:\n"
                f"  Total registros: {total_registros}\n"
                f"  Suma gramos: {suma_gramos:.2f}\n"
                f"  Promedio gramos: {promedio_gramos:.2f}\n"
                f"  Máximo registro: {max_registro.to_dict()}\n"
            )
            resultado = "\n\n".join(lista_descriptiva) + total_plantas_str + estadisticas
            self.mostrar_lista_descriptiva(resultado)
        else:
            # Modo gráfico
            filtros_aplicados = [k for k, v in filtros.items() if v and v != "Todas"]
            if len(filtros_aplicados) == 1 and campo in filtros_aplicados and campo != "sucursal":
                valor = filtros[campo]
                df_filtrado = df[df[campo].str.upper() == valor.upper()]
                resumen = df_filtrado.groupby("sucursal")["gramos"].sum().sort_values(ascending=False)
                fig, ax = plt.subplots(figsize=(8,4))
                resumen.plot(kind="bar", color="skyblue", ax=ax)
                plt.title(f"Gramos de '{valor}' por sucursal")
                plt.ylabel("Gramos")
                plt.xlabel("Sucursal")
                plt.tight_layout()
                # Agregar info de lotes, plantas y gramos (solo Entrada)
                for i, suc in enumerate(resumen.index):
                    subdf = df_filtrado[df_filtrado["sucursal"] == suc]
                    lotes = subdf["lote"].nunique()
                    if "tipo" in subdf.columns and "plantas" in subdf.columns:
                        plantas = subdf[subdf["tipo"].str.lower() == "entrada"]["plantas"].astype(float).sum()
                    elif "plantas" in subdf.columns:
                        plantas = subdf["plantas"].astype(float).sum()
                    else:
                        plantas = 0
                    gramos = resumen.iloc[i]
                    ax.text(i, gramos + max(resumen)*0.08, f"{suc}\n{gramos:.2f}g\nLotes:{lotes}\nPlantas:{plantas}", ha='center', va='bottom', fontsize=9, color='black')
                plt.show()
            else:
                resumen = df.groupby(campo)["gramos"].sum().sort_values(ascending=False)
                fig, ax = plt.subplots(figsize=(8,4))
                resumen.plot(kind="bar", color="skyblue", ax=ax)
                plt.title(f"Total de gramos por {campo}")
                plt.ylabel("Gramos")
                plt.xlabel(campo.capitalize())
                plt.tight_layout()
                # Agregar info de lotes, plantas y gramos (solo Entrada)
                for i, grupo in enumerate(resumen.index):
                    subdf = df[df[campo] == grupo]
                    lotes = subdf["lote"].nunique()
                    if "tipo" in subdf.columns and "plantas" in subdf.columns:
                        plantas = subdf[subdf["tipo"].str.lower() == "entrada"]["plantas"].astype(float).sum()
                    elif "plantas" in subdf.columns:
                        plantas = subdf["plantas"].astype(float).sum()
                    else:
                        plantas = 0
                    gramos = resumen.iloc[i]
                    ax.text(i, gramos + max(resumen)*0.08, f"{grupo}\n{gramos:.2f}g\nLotes:{lotes}\nPlantas:{plantas}", ha='center', va='bottom', fontsize=9, color='black')
                plt.show()

    def mostrar_lista_descriptiva(self, texto):
        ventana = tk.Toplevel(self.root)
        ventana.title("Lista descriptiva de resultados")
        ventana.geometry("600x500")
        frame = ttk.Frame(ventana)
        frame.pack(fill="both", expand=True)
        txt = tk.Text(frame, wrap="word", font=("Arial", 11))
        txt.pack(expand=True, fill="both")
        txt.insert("end", texto)
        txt.config(state="disabled")

        btn_frame = ttk.Frame(ventana)
        btn_frame.pack(fill="x", pady=5)
        btn_txt = ttk.Button(btn_frame, text="Exportar a TXT", command=lambda: self.exportar_lista_txt(texto))
        btn_txt.pack(side="left", padx=10)
        btn_pdf = ttk.Button(btn_frame, text="Exportar a PDF", command=lambda: self.exportar_lista_pdf(texto))
        btn_pdf.pack(side="left", padx=10)

    def exportar_lista_txt(self, texto):
        from tkinter import filedialog
        archivo = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Archivo de texto", "*.txt")], title="Guardar como TXT")
        if archivo:
            with open(archivo, "w", encoding="utf-8") as f:
                f.write(texto)
            messagebox.showinfo("Éxito", f"Lista exportada a {archivo}")

    def exportar_lista_pdf(self, texto):
        try:
            from fpdf import FPDF
        except ImportError:
            messagebox.showerror("Error", "Debe instalar el paquete 'fpdf' para exportar a PDF.\nEjecute: pip install fpdf")
            return
        from tkinter import filedialog
        archivo = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("Archivo PDF", "*.pdf")], title="Guardar como PDF")
        if archivo:
            pdf = FPDF()
            pdf.add_page()
            pdf.set_auto_page_break(auto=True, margin=15)
            pdf.set_font("Arial", size=11)
            # Dividir el texto en líneas y agregar cada línea
            for linea in texto.splitlines():
                pdf.multi_cell(0, 8, linea)
            pdf.output(archivo)
            messagebox.showinfo("Éxito", f"Lista exportada a {archivo}")
    def mostrar_grafico(self):
        import pandas as pd
        import matplotlib.pyplot as plt
        # Leer el CSV
        if not os.path.exists(CSV_FILE):
            messagebox.showerror("Error", "No hay datos registrados.")
            return
        df = pd.read_csv(CSV_FILE)
        # Limpiar espacios y normalizar columnas clave
        for col in ["variedad", "colaborador", "supervisor", "sucursal", "lote"]:
            df[col] = df[col].astype(str).str.strip()
        # Convertir gramos a numérico
        df["gramos"] = pd.to_numeric(df["gramos"], errors="coerce")
        df = df.dropna(subset=["gramos"])
        variedad = self.filtro_variedad.get().strip()
        sucursal = self.filtro_sucursal.get().strip()
        if variedad and variedad != "Todas":
            df = df[df["variedad"].str.upper() == variedad.upper()]
        if sucursal and sucursal != "Todas":
            df = df[df["sucursal"].str.upper() == sucursal.upper()]
        if df.empty:
            messagebox.showinfo("Sin datos", "No hay datos para los filtros seleccionados.")
            return
        resumen = df.groupby("variedad")["gramos"].sum()
        resumen = resumen.sort_values(ascending=False)
        plt.figure(figsize=(8,4))
        resumen.plot(kind="bar", color="skyblue")
        plt.title("Total de gramos por variedad")
        plt.ylabel("Gramos")
        plt.xlabel("Variedad")
        plt.tight_layout()
        plt.show()



    def limpiar_campos(self):
        self.colaborador.set("")
        self.gramos.set("")
        self.plantas.set("0")
        self.supervisor.set("")
        self.lote.set("")
        self.variedad.set("")
        self.sucursal.set("")
        self.motivo.set("")
        self.cliente.delete(0, "end")
        self.no_aplicacion.delete(0, "end")
        # Solo actualiza la fecha si es necesario, y de forma segura
        try:
            self.fecha.set_date(datetime.now().date())
        except Exception:
            pass

if __name__ == "__main__":
    root = tk.Tk()
    app = RegistroApp(root)
    root.mainloop()
