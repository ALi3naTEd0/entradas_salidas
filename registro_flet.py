import flet as ft
import pandas as pd
import os
from datetime import datetime

CSV_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "registro.csv")
VARIEDADES = [
    "AK-47", "APPLE FRITTER", "BANANA LATTE", "BLACKBERRY HONEY",
    "GRAN JEFA", "MICHAEL JORDAN", "KANDY KUSH", "KING KUSH BREATH",
    "RECON", "RUNTZ", "SUGAR CANE", "WEDDING CAKE", "ZALLAH BREAD"
]
SUCURSALES = ["FSM", "SMB", "RP"]
# Diccionario de opciones de lotes por sucursal (para Flet)
lotes_por_sucursal = {}
for s in SUCURSALES:
    lotes_por_sucursal[s] = [ft.dropdown.Option(f"L{i} - {s}") for i in range(1, 33)]
COLABORADORES = ["KEF", "CHCH", "LE", "AX", "JP", "NRQ"]
SUPERVISORES = ["DRE", "RAB", "JP"]
CAMPOS = ["fecha", "variedad", "colaborador", "gramos", "plantas", "supervisor", "sucursal", "lote", "tipo"]

def main(page: ft.Page):
    # (lotes_por_sucursal ahora es global)
    # Definir todos los controles una sola vez
    # Primero define abrir_date_picker y date_picker
    def abrir_date_picker():
        date_picker.open = True
        page.update()

    date_picker = ft.DatePicker(
        on_change=lambda e: on_date_selected(e),
        first_date=datetime(2020, 1, 1),
        last_date=datetime(2030, 12, 31),
        value=datetime.now()
    )

    # Ahora sí define los controles, usando abrir_date_picker
    fecha = ft.TextField(
        label="Fecha",
        value=datetime.now().strftime("%Y-%m-%d"),
        read_only=True,
        suffix=ft.TextButton(
            content=ft.Text("📅"),
            on_click=lambda e: abrir_date_picker()
        )
    )
    variedad = ft.Dropdown(label="Variedad", options=[ft.dropdown.Option(v) for v in VARIEDADES])
    tipo = ft.Dropdown(label="Tipo", options=[ft.dropdown.Option("Entrada"), ft.dropdown.Option("Salida")], value="Entrada")
    colaborador = ft.Dropdown(label="Colaborador", options=[ft.dropdown.Option(c) for c in COLABORADORES])
    supervisor = ft.Dropdown(label="Supervisor", options=[ft.dropdown.Option(s) for s in SUPERVISORES])
    gramos = ft.TextField(label="Gramos")
    plantas = ft.TextField(label="Plantas")
    sucursal = ft.Dropdown(
        label="Sucursal",
        options=[ft.dropdown.Option(s, s) for s in ["FSM", "SMB", "RP"]],
        value=None,
    )
    # Inicialmente, el Dropdown de lote está vacío
    lote_ref = [ft.Dropdown(label="Lote", options=[])]
    mensaje = ft.Text(value="", color="red")
    page.title = "Los Cielos Farm E/S (Flet)"
    page.scroll = "auto"
    

    # Sección de registro debe estar definida antes de usarla
    registro_section = ft.Column([])

    # Estado para mostrar/ocultar campos
    def actualizar_registro_section():
        controls = [
            ft.Row([fecha, variedad, tipo]),
        ]
        if tipo.value == "Salida":
            controls.append(ft.Row([supervisor]))
            controls.append(ft.Row([gramos]))
        else:
            controls.append(ft.Row([colaborador, supervisor]))
            controls.append(ft.Row([gramos, plantas]))
        # Siempre reutiliza el control global 'lote', nunca lo reemplaza
        controls.append(ft.Row([sucursal, lote_ref[0]]))
        controls.append(ft.Row([ft.ElevatedButton("Guardar Registro", on_click=guardar_registro), mensaje]))
        registro_section.controls = controls
        page.update()

    def actualizar_lotes(e):
        lotes_por_sucursal = {
            "FSM": [ft.dropdown.Option(f"L{i} - FSM") for i in range(1, 33)],
            "SMB": [ft.dropdown.Option(f"L{i} - SMB") for i in range(1, 33)],
            "RP": [ft.dropdown.Option(f"L{i} - RP") for i in range(1, 33)]
        }
        suc = sucursal.value
        # Solo actualizar opciones y valor del Dropdown existente
        lote_ref[0].value = None
        if suc and suc in lotes_por_sucursal:
            lote_ref[0].options = lotes_por_sucursal[suc]
        else:
            lote_ref[0].options = []
        lote_ref[0].update()
        page.update()

    # DatePicker y campo de fecha
    def on_date_selected(e):
        if date_picker.value:
            fecha.value = date_picker.value.strftime("%Y-%m-%d")
            page.update()

    # Elimina la segunda definición de controles y solo deja los listeners y overlay
    tipo.on_change = lambda e: actualizar_registro_section()
    def sucursal_on_change(e):
        actualizar_lotes(e)
        actualizar_registro_section()
    sucursal.on_change = sucursal_on_change
    # Agregar el DatePicker oculto a la página
    page.overlay.append(date_picker)


    def guardar_registro(e):
        datos = [
            fecha.value,
            variedad.value,
            colaborador.value if tipo.value != "Salida" else "",
            gramos.value,
            plantas.value if tipo.value != "Salida" else "1",
            supervisor.value,
            sucursal.value,
            lote_ref[0].value,
            tipo.value
        ]
        # Validación
        campos_obligatorios = [fecha.value, variedad.value, gramos.value, supervisor.value, sucursal.value, lote_ref[0].value]
        if tipo.value != "Salida":
            campos_obligatorios += [plantas.value, colaborador.value]
        if not all(campos_obligatorios):
            mensaje.value = "Todos los campos son obligatorios."
            mensaje.color = "red"
            page.update()
            return
        try:
            float(gramos.value)
            if tipo.value != "Salida":
                int(plantas.value)
        except ValueError:
            mensaje.value = "'gramos' y 'plantas' deben ser numéricos."
            mensaje.color = "red"
            page.update()
            return
        archivo_nuevo = not os.path.exists(CSV_FILE)
        if archivo_nuevo:
            with open(CSV_FILE, "w", encoding="utf-8") as f:
                f.write(",".join(CAMPOS) + "\n")
        with open(CSV_FILE, "a", encoding="utf-8") as f:
            f.write(",".join(datos) + "\n")
        mensaje.value = "Registro guardado exitosamente."
        mensaje.color = "green"
        page.update()
        # Forzar actualización de lotes tras cada render
        actualizar_lotes(None)
        limpiar_campos()

    def limpiar_campos():
        colaborador.value = ""
        gramos.value = ""
        plantas.value = ""
        supervisor.value = ""
        lote_ref[0].value = None
        lote_ref[0].options = []
        variedad.value = ""
        sucursal.value = None
        actualizar_lotes(None)
        fecha.value = datetime.now().strftime("%Y-%m-%d")
        date_picker.value = datetime.now()
        page.update()

    # Filtros para gráficos
    filtro_variedad = ft.Dropdown(label="Variedad", options=[ft.dropdown.Option("Todas")] + [ft.dropdown.Option(v) for v in VARIEDADES])
    filtro_sucursal = ft.Dropdown(label="Sucursal", options=[ft.dropdown.Option("Todas")] + [ft.dropdown.Option(s) for s in SUCURSALES])
    filtro_colaborador = ft.Dropdown(label="Colaborador", options=[ft.dropdown.Option("Todas")] + [ft.dropdown.Option(c) for c in COLABORADORES])
    filtro_supervisor = ft.Dropdown(label="Supervisor", options=[ft.dropdown.Option("Todas")] + [ft.dropdown.Option(s) for s in SUPERVISORES])
    filtro_lote = ft.Dropdown(label="Lote", options=[ft.dropdown.Option("Todas")])
    campo_grafico = ft.Dropdown(label="Campo a graficar", options=[ft.dropdown.Option(c) for c in ["variedad", "sucursal", "colaborador", "supervisor", "lote"]], value="variedad")

    resultado_grafico = ft.Text(value="", color="blue")

    def mostrar_resultado(e):
        if not os.path.exists(CSV_FILE):
            resultado_grafico.value = "No hay datos registrados."
            resultado_grafico.color = "red"
            page.update()
            return
        df = pd.read_csv(CSV_FILE)
        # Filtros
        df_filtrado = df.copy()
        if filtro_variedad.value and filtro_variedad.value != "Todas":
            df_filtrado = df_filtrado[df_filtrado["variedad"] == filtro_variedad.value]
        if filtro_sucursal.value and filtro_sucursal.value != "Todas":
            df_filtrado = df_filtrado[df_filtrado["sucursal"] == filtro_sucursal.value]
        if filtro_colaborador.value and filtro_colaborador.value != "Todas":
            df_filtrado = df_filtrado[df_filtrado["colaborador"] == filtro_colaborador.value]
        if filtro_supervisor.value and filtro_supervisor.value != "Todas":
            df_filtrado = df_filtrado[df_filtrado["supervisor"] == filtro_supervisor.value]
        if filtro_lote.value and filtro_lote.value != "Todas":
            df_filtrado = df_filtrado[df_filtrado["lote"] == filtro_lote.value]
        campo = campo_grafico.value
        if campo in df_filtrado.columns:
            agrupado = df_filtrado.groupby(campo).agg({"gramos": "sum", "plantas": "sum"}).reset_index()
            resultado = f"Resultados agrupados por {campo}:\n"
            for _, row in agrupado.iterrows():
                resultado += f"{row[campo]}: {row['gramos']}g, {row['plantas']} plantas\n"
            resultado_grafico.value = resultado
            resultado_grafico.color = "blue"
        else:
            resultado_grafico.value = "No se puede agrupar por ese campo."
            resultado_grafico.color = "red"
        page.update()

    def exportar_txt(e):
        texto = resultado_grafico.value
        if not texto:
            resultado_grafico.value = "No hay resultado para exportar."
            page.update()
            return
        with open("resultado_exportado.txt", "w", encoding="utf-8") as f:
            f.write(texto)
        resultado_grafico.value += "\nExportado a resultado_exportado.txt"
        page.update()

    def exportar_pdf(e):
        texto = resultado_grafico.value
        if not texto:
            resultado_grafico.value = "No hay resultado para exportar."
            page.update()
            return
        try:
            from fpdf import FPDF
        except ImportError:
            resultado_grafico.value = "Instala fpdf para exportar a PDF: pip install fpdf"
            page.update()
            return
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        for line in texto.split("\n"):
            pdf.cell(200, 10, txt=line, ln=1)
        pdf.output("resultado_exportado.pdf")
        resultado_grafico.value += "\nExportado a resultado_exportado.pdf"
        page.update()

    graficos_section = ft.Column([
        ft.Row([filtro_variedad, filtro_sucursal]),
        ft.Row([filtro_colaborador, filtro_supervisor]),
        ft.Row([filtro_lote, campo_grafico]),
        ft.Row([
            ft.ElevatedButton("Mostrar resultado", on_click=mostrar_resultado),
            ft.ElevatedButton("Exportar TXT", on_click=exportar_txt),
            ft.ElevatedButton("Exportar PDF", on_click=exportar_pdf)
        ]),
        resultado_grafico
    ])

    # Ya definido arriba y actualizado después de definir todas las funciones
    actualizar_registro_section()

    # Navegación por botones en vez de Tabs
    contenido = ft.Column([])

    def mostrar_registro(e):
        contenido.controls = [registro_section]
        page.update()

    def mostrar_graficos(e):
        contenido.controls = [graficos_section]
        page.update()

    nav = ft.Row([
        ft.ElevatedButton("Registro", on_click=mostrar_registro),
        ft.ElevatedButton("Gráficos", on_click=mostrar_graficos)
    ])
    page.add(nav, contenido)
    mostrar_registro(None)

    # ...existing code...
ft.app(target=main)
