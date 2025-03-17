import os
import pandas as pd
from flask import Flask, render_template, request, redirect, url_for, flash

app = Flask(__name__)
app.secret_key = 'mi_clave_secreta'  # Reemplazar por una clave segura en producción

# Variable global para almacenar los DataFrames finales de cada flujo
materiales_finales = []

def renombrar_columnas(df):
    df_renombrado = df.rename(
        columns={
            "1. Cód.SAP": "Cód.SAP",
            "2. MATERIAL": "MATERIAL",
            "3. Descripción": "Descripción",
            "5.CONDICIÓN": "CONDICIÓN"
        }
    )
    # Asegurarse de que queden las siguientes columnas
    columnas = ["Cód.SAP", "MATERIAL", "Descripción", "4.CANTIDAD", "CONDICIÓN"]
    columnas_presentes = [col for col in columnas if col in df_renombrado.columns]
    return df_renombrado[columnas_presentes]

def load_excel_file():
    try:
        # Se asume que el archivo Excel se encuentra en la carpeta "data"
        file_path = os.path.join('materiales', 'ajuste de medida(2).xlsx')
        df = pd.read_excel(file_path)
        df.columns = df.columns.str.strip()
        df["DIÁMETRO"] = df["DIÁMETRO"].astype(str).str.strip()
        return df
    except Exception as e:
        print("Error al cargar el archivo Excel:", e)
        return None

# Ruta para el FLUJO A: Selección inicial de ajuste de medida
@app.route('/flujo_a', methods=['GET', 'POST'])
def flujo_a():
    if request.method == 'POST':
        ajuste_medida = request.form.get('ajuste_medida')
        if ajuste_medida == "SI":
            return redirect(url_for('flujo_a_diam'))
        elif ajuste_medida == "NO":
            return redirect(url_for('flujo_b'))
        else:
            flash("Por favor, seleccione una opción.")
    return render_template('flujo_a.html')

# Ruta para seleccionar DIÁMETRO (primer paso)
@app.route('/flujo_a/diam', methods=['GET', 'POST'])
def flujo_a_diam():
    df = load_excel_file()
    if df is None:
        flash("Error al cargar el archivo Excel.")
        return redirect(url_for('flujo_a'))
    all_diams = sorted([x for x in df["DIÁMETRO"].dropna().unique() if x.upper() != "TODOS"])
    if request.method == 'POST':
        selected_diams = request.form.getlist('diametros')
        if not selected_diams:
            flash("Por favor, seleccione al menos un DIÁMETRO.")
            return redirect(url_for('flujo_a_diam'))
        # Se pasa la lista de DIÁMETRO seleccionados al siguiente formulario
        return render_template('flujo_a_filters.html', diametros=selected_diams, df=df)
    return render_template('flujo_a_diam.html', all_diams=all_diams)

# Ruta para aplicar los filtros basados en los valores seleccionados para cada DIÁMETRO
@app.route('/flujo_a/apply', methods=['POST'])
def flujo_a_apply():
    df = load_excel_file()
    if df is None:
        flash("Error al cargar el archivo Excel.")
        return redirect(url_for('flujo_a'))
    
    # Se reciben los DIÁMETRO seleccionados (se envían como campos ocultos)
    selected_diams = request.form.getlist('diametros')
    all_filters = {}
    for diam in selected_diams:
        # Para cada DIÁMETRO se recogen los valores seleccionados de cada filtro
        tipo_sel = request.form.getlist(f"tipo_{diam}")
        if not tipo_sel:
            tipo_sel = ["TODOS"]
        else:
            tipo_sel.append("TODOS")
        ac = request.form.get(f"acero_{diam}")
        acero_list = ["TODOS"] if (ac == "Seleccionar" or ac is None) else [ac, "TODOS"]
        ac_cup = request.form.get(f"acero_cup_{diam}")
        acero_cup_list = ["TODOS"] if (ac_cup == "Seleccionar" or ac_cup is None) else [ac_cup, "TODOS"]
        t_cup = request.form.get(f"tipo_cup_{diam}")
        tipo_cup_list = ["TODOS"] if (t_cup == "Seleccionar" or t_cup is None) else [t_cup, "TODOS"]
        all_filters[diam] = {
            "tipo_list": tipo_sel,
            "acero_list": acero_list,
            "acero_cup_list": acero_cup_list,
            "tipo_cup_list": tipo_cup_list
        }
    
    # Aplicar el filtrado de manera similar al código original
    final_condition = pd.Series([False] * len(df))
    for diam_value, fdict in all_filters.items():
        temp_cond_diam = pd.Series([False] * len(df))
        for tipo_val in fdict["tipo_list"]:
            cond = (
                df["DIÁMETRO"].isin([diam_value, "TODOS"]) &
                df["TIPO"].isin([tipo_val, "TODOS"]) &
                df["GRADO DE ACERO"].isin(fdict["acero_list"]) &
                df["GRADO DE ACERO CUPLA"].isin(fdict["acero_cup_list"]) &
                df["TIPO DE CUPLA"].isin(fdict["tipo_cup_list"])
            )
            temp_cond_diam = temp_cond_diam | cond
        final_condition = final_condition | temp_cond_diam
    final_df = df[final_condition]
    final_df_renombrado = renombrar_columnas(final_df)
    materiales_finales.append(("FLUJO A", final_df_renombrado))
    
    return render_template('flujo_a_result.html')

# Rutas placeholder para FLUJO B y FLUJO H
@app.route('/flujo_b')
def flujo_b():
    return "Flujo B - En construcción"

@app.route('/flujo_h')
def flujo_h():
    return "Flujo H - En construcción"

if __name__ == '__main__':
    app.run(debug=True)


