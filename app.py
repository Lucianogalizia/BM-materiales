from flask import Flask, render_template, request, redirect, url_for, flash
import pandas as pd
import os
from utils import renombrar_columnas

app = Flask(__name__)
app.secret_key = 'clave-secreta-para-sesiones'

# Variable global para almacenar materiales finales
materiales_finales = []

# Ruta al archivo Excel (colócalo en la carpeta "data" del proyecto)
EXCEL_FILE_PATH = os.path.join(os.path.dirname(__file__), 'data', 'ajuste_de_medida.xlsx')

@app.route('/', methods=['GET', 'POST'])
def index():
    """
    Página inicial: Se pregunta si se requiere el ajuste de medida.
    """
    if request.method == 'POST':
        ajuste = request.form.get('ajuste_medida')
        if ajuste == 'SI':
            return redirect(url_for('flujo_a_filtrar'))
        elif ajuste == 'NO':
            return redirect(url_for('flujo_b'))
    return render_template('index.html')

@app.route('/flujo_a/filtrar', methods=['GET', 'POST'])
def flujo_a_filtrar():
    """
    Ruta para cargar el Excel y permitir al usuario seleccionar uno o más DIÁMETRO.
    """
    try:
        df = pd.read_excel(EXCEL_FILE_PATH)
        df.columns = df.columns.str.strip()
        df["DIÁMETRO"] = df["DIÁMETRO"].astype(str).str.strip()
    except Exception as e:
        flash(f"Error al cargar el archivo Excel: {e}", "danger")
        return redirect(url_for('index'))
    
    # Obtiene los diámetros únicos, excluyendo el valor "TODOS"
    all_diams = sorted([x for x in df["DIÁMETRO"].dropna().unique() if str(x).upper() != "TODOS"])
    
    if request.method == 'POST':
        selected_diams = request.form.getlist('diametros')
        if not selected_diams:
            selected_diams = ["TODOS"]
        # Se envían los diámetros seleccionados a la siguiente ruta mediante parámetros
        return redirect(url_for('flujo_a_opciones', diametros=",".join(selected_diams)))
    
    return render_template('flujo_a_filtrar.html', diameters=all_diams)

@app.route('/flujo_a/filtrar/opciones', methods=['GET', 'POST'])
def flujo_a_opciones():
    """
    Ruta para mostrar, por cada DIÁMETRO seleccionado, los filtros adicionales:
      - TIPO (múltiple selección)
      - GRADO DE ACERO (dropdown)
      - GRADO DE ACERO CUPLA (dropdown)
      - TIPO DE CUPLA (dropdown)
    
    Al aplicar filtros se filtra el DataFrame, se renombran las columnas y se almacena
    el resultado en la lista global materiales_finales.
    """
    diametros_str = request.args.get('diametros', '')
    if not diametros_str:
        flash("No se seleccionaron diámetros.", "warning")
        return redirect(url_for('flujo_a_filtrar'))
    
    selected_diams = diametros_str.split(',')
    
    try:
        df = pd.read_excel(EXCEL_FILE_PATH)
        df.columns = df.columns.str.strip()
        df["DIÁMETRO"] = df["DIÁMETRO"].astype(str).str.strip()
    except Exception as e:
        flash(f"Error al cargar el archivo Excel: {e}", "danger")
        return redirect(url_for('index'))
    
    # Prepara las opciones para cada DIÁMETRO seleccionado
    options_dict = {}
    for diam in selected_diams:
        subset = df[df["DIÁMETRO"] == diam]
        # Opciones para TIPO
        unique_tipos = sorted([x for x in subset["TIPO"].dropna().unique() if str(x).upper() != "TODOS"])
        if not unique_tipos:
            unique_tipos = ["TODOS"]
        else:
            unique_tipos.append("TODOS")
        # Opciones para GRADO DE ACERO
        unique_acero = sorted([x for x in subset["GRADO DE ACERO"].dropna().unique() if str(x).upper() != "TODOS"])
        unique_acero = ["Seleccionar"] + unique_acero if unique_acero else ["Seleccionar"]
        # Opciones para GRADO DE ACERO CUPLA
        unique_acero_cup = sorted([x for x in subset["GRADO DE ACERO CUPLA"].dropna().unique() if str(x).upper() != "TODOS"])
        unique_acero_cup = ["Seleccionar"] + unique_acero_cup if unique_acero_cup else ["Seleccionar"]
        # Opciones para TIPO DE CUPLA
        unique_tipo_cup = sorted([x for x in subset["TIPO DE CUPLA"].dropna().unique() if str(x).upper() != "TODOS"])
        unique_tipo_cup = ["Seleccionar"] + unique_tipo_cup if unique_tipo_cup else ["Seleccionar"]
        
        options_dict[diam] = {
            "tipo": unique_tipos,
            "acero": unique_acero,
            "acero_cup": unique_acero_cup,
            "tipo_cup": unique_tipo_cup
        }
    
    if request.method == 'POST':
        # Recolecta los filtros seleccionados para cada DIÁMETRO
        all_filters = {}
        for diam in selected_diams:
            tipo_sel = request.form.getlist(f"tipo_{diam}")
            if not tipo_sel:
                tipo_sel = ["TODOS"]
            else:
                if "TODOS" not in tipo_sel:
                    tipo_sel.append("TODOS")
            ac = request.form.get(f"acero_{diam}", "Seleccionar")
            acero_list = ["TODOS"] if ac == "Seleccionar" else [ac, "TODOS"]
            ac_cup = request.form.get(f"acero_cup_{diam}", "Seleccionar")
            acero_cup_list = ["TODOS"] if ac_cup == "Seleccionar" else [ac_cup, "TODOS"]
            t_cup = request.form.get(f"tipo_cup_{diam}", "Seleccionar")
            tipo_cup_list = ["TODOS"] if t_cup == "Seleccionar" else [t_cup, "TODOS"]
            all_filters[diam] = {
                "tipo_list": tipo_sel,
                "acero_list": acero_list,
                "acero_cup_list": acero_cup_list,
                "tipo_cup_list": tipo_cup_list
            }
        
        # Aplica los filtros al DataFrame
        final_condition = pd.Series([False] * len(df))
        for diam_value, fdict in all_filters.items():
            temp_cond_diam = pd.Series([False] * len(df))
            for tipo_val in fdict["tipo_list"]:
                cond = ((df["DIÁMETRO"].isin([diam_value, "TODOS"])) &
                        (df["TIPO"].isin([tipo_val, "TODOS"])) &
                        (df["GRADO DE ACERO"].isin(fdict["acero_list"])) &
                        (df["GRADO DE ACERO CUPLA"].isin(fdict["acero_cup_list"])) &
                        (df["TIPO DE CUPLA"].isin(fdict["tipo_cup_list"])))
                temp_cond_diam = temp_cond_diam | cond
            final_condition = final_condition | temp_cond_diam
        final_df = df[final_condition]
        final_df_renombrado = renombrar_columnas(final_df)
        materiales_finales.append(("FLUJO A", final_df_renombrado))
        
        # Una vez aplicados los filtros se redirige al FLUJO H
        return redirect(url_for('flujo_h'))
    
    return render_template('flujo_a_opciones.html',
                           selected_diams=selected_diams,
                           options_dict=options_dict)

@app.route('/flujo_b')
def flujo_b():
    # Lógica pendiente para FLUJO B
    return "FLUJO B: Lógica pendiente"

@app.route('/flujo_h')
def flujo_h():
    # Lógica pendiente para FLUJO H
    return "FLUJO H: Lógica pendiente. Materiales finales almacenados: " + str(len(materiales_finales))

if __name__ == '__main__':
    app.run(debug=True)



