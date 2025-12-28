import tkinter as tk
from tkinter import ttk, messagebox
from tkcalendar import DateEntry
import csv
import os
from datetime import datetime
import pandas as pd
import matplotlib.pyplot as plt
import sys
# Soporte para ejecutable PyInstaller: buscar archivo en la misma carpeta que el .exe o script
if getattr(sys, 'frozen', False):
    BASE_PATH = sys._MEIPASS if hasattr(sys, '_MEIPASS') else os.path.dirname(sys.executable)
else:
    BASE_PATH = os.path.dirname(os.path.abspath(__file__))
CSV_FILE = os.path.join(BASE_PATH, "registro.csv")

# Listas de opciones
VARIEDADES = [
    "AK-47", "APPLE FRITTER", "BANANA LATTE", "BLACKBERRY HONEY",
    "GRAN JEFA", "MICHAEL JORDAN", "KANDY KUSH", "KING KUSH BREATH",
    "RECON", "RUNTZ", "SUGAR CANE", "WEDDING CAKE", "ZALLAH BREAD"
]
SUCURSALES = ["FSM", "SMB", "RP"]
COLABORADORES = ["KEF", "CHCH", "LE", "AX", "JP", "NRQ"]
SUPERVISORES = ["DRE", "RAB", "JP"]

CAMPOS = ["fecha", "variedad", "colaborador", "gramos", "plantas", "supervisor", "sucursal", "lote"]

class RegistroApp:
    def __init__(self, root):
        self.root = root
        self.lotes_por_sucursal = {}  # Ensure this exists for lotes logic
        # Cambiar título y poner icono
        self.root.title("Los Cielos Farm E/S")
        try:
            icon_path = os.path.join(BASE_PATH, "icon.png")
            if os.path.exists(icon_path):
                self.root.iconphoto(True, tk.PhotoImage(file=icon_path))
        except Exception as e:
            pass  # Si hay error, continuar sin icono
        self.crear_widgets()
    def guardar_registro(self):
        tipo = self.tipo_movimiento.get()
        plantas_val = self.plantas.get() if tipo != "Salida" else "1"
        # Siempre incluir 'plantas' en ambas entradas y salidas (para Salida, valor por defecto '1')
        datos = [
            self.fecha.get(),
            self.variedad.get(),
            self.colaborador.get() if tipo != "Salida" else "",
            self.gramos.get(),
            plantas_val,
            self.supervisor.get(),
            self.sucursal.get(),
            self.lote.get(),
            tipo
        ]
        # Validación básica
        if tipo == "Salida":
            campos_obligatorios = [self.fecha.get(), self.variedad.get(), self.gramos.get(), self.supervisor.get(), self.sucursal.get(), self.lote.get()]
        else:
            campos_obligatorios = [self.fecha.get(), self.variedad.get(), self.gramos.get(), plantas_val, self.supervisor.get(), self.sucursal.get(), self.lote.get(), self.colaborador.get()]
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
        # Si el archivo existe pero no tiene la columna 'tipo' o 'plantas', rehacer encabezado y migrar filas
        if not archivo_nuevo:
            with open(CSV_FILE, 'r', encoding='utf-8') as f:
                filas = list(csv.reader(f))
            encabezado = filas[0] if filas else []
            if encabezado != CAMPOS + ["tipo"]:
                # Migrar todas las filas a la nueva estructura
                nuevas_filas = []
                for fila in filas[1:]:
                    # Si la fila ya tiene todas las columnas, solo ajustar orden si es necesario
                    if len(fila) == len(CAMPOS) + 1:
                        nuevas_filas.append(fila)
                    else:
                        # Intentar mapear por nombre de encabezado si posible
                        fila_dict = dict(zip(encabezado, fila))
                        nueva = [
                            fila_dict.get("fecha", ""),
                            fila_dict.get("variedad", ""),
                            fila_dict.get("colaborador", ""),
                            fila_dict.get("gramos", ""),
                            fila_dict.get("plantas", "1"),
                            fila_dict.get("supervisor", ""),
                            fila_dict.get("sucursal", ""),
                            fila_dict.get("lote", ""),
                            fila_dict.get("tipo", "Entrada")
                        ]
                        nuevas_filas.append(nueva)
                with open(CSV_FILE, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow(CAMPOS + ["tipo"])
                    for fila in nuevas_filas:
                        writer.writerow(fila)
                            # (Eliminado: lógica de conteo de plantas, no debe estar aquí)
        
        self.crear_widgets()

    def crear_widgets(self):
        tab_control = ttk.Notebook(self.root)
        tab_control.grid(row=0, column=0, sticky="nsew")

        # Tab 1: Registro
        frame = ttk.Frame(tab_control, padding=10)
        tab_control.add(frame, text="Registro")

        # Fecha
        ttk.Label(frame, text="Fecha:").grid(row=0, column=0, sticky="e")
        self.fecha = DateEntry(frame, date_pattern='yyyy-mm-dd', width=12)
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

        # Colaborador y Supervisor (visibilidad dinámica)
        self.label_colaborador = ttk.Label(frame, text="Colaborador:")
        self.colaborador = ttk.Combobox(frame, values=COLABORADORES, state="readonly")
        self.label_supervisor = ttk.Label(frame, text="Supervisor:")
        self.supervisor = ttk.Combobox(frame, values=SUPERVISORES, state="readonly")
        self.label_gramos = ttk.Label(frame, text="Gramos:")
        GRAMOS = [str(i) for i in range(0, 201)]
        self.gramos = ttk.Combobox(frame, values=GRAMOS, state="normal")
        self.label_plantas = ttk.Label(frame, text="Plantas:")
        self.plantas = ttk.Combobox(frame, values=[str(i) for i in range(1, 101)], state="normal")
        self.colaborador.set("")
        self.supervisor.set("")
        self.gramos.set("")
        self.plantas.set("")

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

        # Mostrar/ocultar campos según tipo
        def on_tipo_change(event=None):
            if self.tipo_movimiento.get() == "Salida":
                self.label_colaborador.grid_remove()
                self.colaborador.grid_remove()
                self.label_supervisor.grid(row=2, column=0, sticky="e")
                self.supervisor.grid(row=2, column=1, padx=5, pady=2)
                self.label_gramos.grid(row=3, column=0, sticky="e")
                self.gramos.grid(row=3, column=1, padx=5, pady=2)
                # Ocultar campo plantas
                self.label_plantas.grid_remove()
                self.plantas.grid_remove()
                # Sucursal y lote en filas 4 y 5
                self.sucursal_label_row = 4
                self.lote_label_row = 5
            else:
                self.label_colaborador.grid(row=2, column=0, sticky="e")
                self.colaborador.grid(row=2, column=1, padx=5, pady=2)
                self.label_supervisor.grid(row=3, column=0, sticky="e")
                self.supervisor.grid(row=3, column=1, padx=5, pady=2)
                self.label_gramos.grid(row=4, column=0, sticky="e")
                self.gramos.grid(row=4, column=1, padx=5, pady=2)
                self.label_plantas.grid(row=5, column=0, sticky="e")
                self.plantas.grid(row=5, column=1, padx=5, pady=2)
                # Sucursal y lote en filas 6 y 7
                self.sucursal_label_row = 6
                self.lote_label_row = 7
            # Reubicar sucursal y lote según el tipo
            self.sucursal_label.grid(row=self.sucursal_label_row, column=0, sticky="e")
            self.sucursal.grid(row=self.sucursal_label_row, column=1, padx=5, pady=2)
            self.label_lote.grid(row=self.lote_label_row, column=0, sticky="e")
            self.lote.grid(row=self.lote_label_row, column=1, padx=5, pady=2)
            self.btn_guardar.grid(row=self.lote_label_row+1, column=0, columnspan=2, pady=10)
        self.tipo_movimiento.bind("<<ComboboxSelected>>", on_tipo_change)
        on_tipo_change()

        # Tab 2: Gráficos Generales
        graficos_frame = ttk.Frame(tab_control, padding=10)
        tab_control.add(graficos_frame, text="Gráficos Generales")

        # Filtros generales
        ttk.Label(graficos_frame, text="Variedad:").grid(row=0, column=0, sticky="e")
        self.filtro_g_variedad = ttk.Combobox(graficos_frame, values=["Todas"] + VARIEDADES, state="readonly")
        self.filtro_g_variedad.grid(row=0, column=1, padx=5, pady=2)
        self.filtro_g_variedad.set("")

        ttk.Label(graficos_frame, text="Sucursal:").grid(row=1, column=0, sticky="e")
        self.filtro_g_sucursal = ttk.Combobox(graficos_frame, values=["Todas"] + SUCURSALES, state="readonly")
        self.filtro_g_sucursal.grid(row=1, column=1, padx=5, pady=2)
        self.filtro_g_sucursal.set("")
        self.filtro_g_sucursal.bind("<<ComboboxSelected>>", self.actualizar_lotes_graficos)

        ttk.Label(graficos_frame, text="Colaborador:").grid(row=2, column=0, sticky="e")
        self.filtro_g_colaborador = ttk.Combobox(graficos_frame, values=["Todas"] + COLABORADORES, state="readonly")
        self.filtro_g_colaborador.grid(row=2, column=1, padx=5, pady=2)
        self.filtro_g_colaborador.set("")

        ttk.Label(graficos_frame, text="Supervisor:").grid(row=3, column=0, sticky="e")
        self.filtro_g_supervisor = ttk.Combobox(graficos_frame, values=["Todas"] + SUPERVISORES, state="readonly")
        self.filtro_g_supervisor.grid(row=3, column=1, padx=5, pady=2)
        self.filtro_g_supervisor.set("")

        ttk.Label(graficos_frame, text="Lote:").grid(row=4, column=0, sticky="e")
        self.filtro_g_lote = ttk.Combobox(graficos_frame, state="readonly")
        self.filtro_g_lote.grid(row=4, column=1, padx=5, pady=2)
        self.filtro_g_lote.set("")
        self.filtro_g_lote['values'] = ["Todas"]

        # Campo a graficar
        ttk.Label(graficos_frame, text="Campo a graficar:").grid(row=5, column=0, sticky="e")
        self.campo_grafico = ttk.Combobox(graficos_frame, values=["variedad", "sucursal", "colaborador", "supervisor", "lote"], state="readonly")
        self.campo_grafico.grid(row=5, column=1, padx=5, pady=2)
        self.campo_grafico.set("variedad")

        # Switch para modo gráfico o lista
        self.modo_lista = tk.BooleanVar(value=False)
        self.switch_modo = ttk.Checkbutton(graficos_frame, text="Mostrar como lista descriptiva", variable=self.modo_lista)
        self.switch_modo.grid(row=6, column=0, columnspan=2, pady=2)

        # Botón para mostrar gráfico general o lista
        self.btn_grafico_general = ttk.Button(graficos_frame, text="Mostrar resultado", command=self.mostrar_grafico_general_unico)
        self.btn_grafico_general.grid(row=7, column=0, columnspan=2, pady=10)
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
        # Si existe la columna tipo, ajustar gramos según Entrada/Salida
        if "tipo" in df.columns:
            df["tipo"] = df["tipo"].fillna("").astype(str)
            df["gramos"] = pd.to_numeric(df["gramos"], errors="coerce")
            df = df.dropna(subset=["gramos"])
            df.loc[df["tipo"].str.lower() == "salida", "gramos"] *= -1
        else:
            df["gramos"] = pd.to_numeric(df["gramos"], errors="coerce")
            df = df.dropna(subset=["gramos"])
        # Aplicar filtros
        filtros = {
            "variedad": self.filtro_g_variedad.get().strip(),
            "sucursal": self.filtro_g_sucursal.get().strip(),
            "colaborador": self.filtro_g_colaborador.get().strip(),
            "supervisor": self.filtro_g_supervisor.get().strip(),
            "lote": self.filtro_g_lote.get().strip()
        }
        for k, v in filtros.items():
            if v and v != "Todas":
                if k == "lote":
                    df = df[df[k] == v]
                else:
                    df = df[df[k].str.upper() == v.upper()]
        if df.empty:
            messagebox.showinfo("Sin datos", "No hay datos para los filtros seleccionados.")
            return
        campo = self.campo_grafico.get()
        # Switch entre modo gráfico y modo lista
        if self.modo_lista.get():
            # ...existing code for lista descriptiva...
            filtros_aplicados = [k for k, v in filtros.items() if v and v != "Todas"]
            lista_descriptiva = []
            if len(filtros_aplicados) == 1 and campo in filtros_aplicados and campo != "sucursal":
                valor = filtros[campo]
                df_filtrado = df[df[campo].str.upper() == valor.upper()]
                resumen = df_filtrado.groupby("sucursal")["gramos"].sum().sort_values(ascending=False)
                # Solo contar plantas de tipo Entrada dentro del subconjunto filtrado
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
                    # Solo contar plantas de tipo Entrada por lote
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
                # Solo contar plantas de tipo Entrada dentro del subconjunto filtrado
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
                    # Solo contar plantas de tipo Entrada por lote
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
                    lista_descriptiva.append(f"{campo.capitalize()}: {grupo}\n  Total gramos: {resumen.iloc[i]:.2f}\n  Plantas (solo Entrada): {conteos.iloc[i]}\n  Lotes: {lotes_por_grupo.iloc[i]}")
            # Total general de plantas (solo Entrada)
            if "tipo" in df.columns and "plantas" in df.columns:
                total_plantas = df[df["tipo"].str.lower() == "entrada"]["plantas"].astype(float).sum()
            elif "plantas" in df.columns:
                total_plantas = df["plantas"].astype(float).sum()
            else:
                total_plantas = 0
            total_plantas_str = f"\nTOTAL GENERAL DE PLANTAS (solo Entrada): {int(total_plantas)}\n"
            # Estadísticas adicionales
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
            # Mostrar en ventana
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
        self.plantas.set("")
        self.supervisor.set("")
        self.lote.set("")
        self.variedad.set("")
        self.sucursal.set("")
        # Solo actualiza la fecha si es necesario, y de forma segura
        try:
            self.fecha.set_date(datetime.now().date())
        except Exception:
            pass

if __name__ == "__main__":
    root = tk.Tk()
    app = RegistroApp(root)
    root.mainloop()
