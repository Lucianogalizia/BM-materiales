from flask import Flask, render_template, request, redirect, url_for, flash
import os
import pandas as pd

app = Flask(__name__)
app.secret_key = 'clave-secreta'  # Necesaria para usar flash y sesiones

# Lista global para almacenar los DataFrames finales de cada flujo
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
    columnas = ["Cód.SAP", "MATERIAL", "Descripción", "4.CANTIDAD", "CONDICIÓN"]
    columnas_presentes = [col for col in columnas if col in df_renombrado.columns]
    return df_renombrado[columnas_presentes]

# Página de inicio
@app.route('/')
def index():
    return render_template('index.html')

# FLUJO A: Ajuste de medida (pregunta inicial)
@app.route('/flujoA', methods=['GET', 'POST'])
def flujoA():
    if request.method == 'POST':
        ajuste = request.form.get('ajuste')
        if ajuste == "SI":
            return redirect(url_for('flujoA_ajuste'))
        elif ajuste == "NO":
            return redirect(url_for('flujoB'))
    return render_template('flujoA.html')

# FLUJO A: Ajuste – Filtros y procesamiento
@app.route('/flujoA/ajuste', methods=['GET', 'POST'])
def flujoA_ajuste():
    file_path = os.path.join('materiales', 'ajuste de medida(2).xlsx')
    try:
        df = pd.read_excel(file_path)
        df.columns = df.columns.str.strip()
        df["DIÁMETRO"] = df["DIÁMETRO"].astype(str).str.strip()
    except Exception as e:
        flash("Error al cargar el archivo Excel: " + str(e))
        return redirect(url_for('flujoA'))
    
    if request.method == 'GET':
        diametros = sorted([x for x in df["DIÁMETRO"].dropna().unique() if x.upper() != "TODOS"])
        return render_template('flujoA_ajuste.html', diametros=diametros)
    else:
        # Procesa los filtros enviados (para cada DIÁMETRO se espera recibir valores en los inputs)
        selected_diametros = request.form.getlist('diametro')
        all_filters = {}
        for diam in selected_diametros:
            # Se leen los valores; en este ejemplo se usan campos de texto (podrías implementar selects dinámicos)
            tipo = request.form.get(f'tipo_{diam}', 'TODOS')
            acero = request.form.get(f'acero_{diam}', 'Seleccionar')
            acero_cup = request.form.get(f'acero_cup_{diam}', 'Seleccionar')
            tipo_cup = request.form.get(f'tipo_cup_{diam}', 'Seleccionar')
            tipo_list = [tipo] if tipo != 'TODOS' else ['TODOS']
            if tipo != 'TODOS':
                tipo_list.append("TODOS")
            acero_list = [acero, "TODOS"] if acero != 'Seleccionar' else ["TODOS"]
            acero_cup_list = [acero_cup, "TODOS"] if acero_cup != 'Seleccionar' else ["TODOS"]
            tipo_cup_list = [tipo_cup, "TODOS"] if tipo_cup != 'Seleccionar' else ["TODOS"]
            all_filters[diam] = {
                "tipo_list": tipo_list,
                "acero_list": acero_list,
                "acero_cup_list": acero_cup_list,
                "tipo_cup_list": tipo_cup_list
            }
        final_condition = pd.Series([False] * len(df))
        for diam, fdict in all_filters.items():
            temp_cond = pd.Series([False] * len(df))
            for tipo_val in fdict["tipo_list"]:
                cond = (
                    df["DIÁMETRO"].isin([diam, "TODOS"]) &
                    df["TIPO"].isin([tipo_val, "TODOS"]) &
                    df["GRADO DE ACERO"].isin(fdict["acero_list"]) &
                    df["GRADO DE ACERO CUPLA"].isin(fdict["acero_cup_list"]) &
                    df["TIPO DE CUPLA"].isin(fdict["tipo_cup_list"])
                )
                temp_cond = temp_cond | cond
            final_condition = final_condition | temp_cond
        final_df = df[final_condition]
        final_df_renombrado = renombrar_columnas(final_df)
        materiales_finales.append(("FLUJO A", final_df_renombrado))
        flash("Materiales del FLUJO A guardados.")
        # Según la lógica original, se continúa al Flujo H
        return redirect(url_for('flujoH'))

# FLUJO B: Tubo de saca
@app.route('/flujoB', methods=['GET', 'POST'])
def flujoB():
    file_path_saca = os.path.join('materiales', 'saca tubing.xlsx')
    try:
        df_saca = pd.read_excel(file_path_saca)
        df_saca.columns = df_saca.columns.str.strip()
        for c in df_saca.columns:
            if df_saca[c].dtype == object:
                df_saca[c] = df_saca[c].astype(str).str.strip()
    except Exception as e:
        flash("Error al cargar el archivo de saca tubing: " + str(e))
        return redirect(url_for('index'))
    
    if request.method == 'GET':
        diametros = sorted([d for d in df_saca['DIÁMETRO'].unique() if d.upper() != 'TODOS'])
        return render_template('flujoB.html', diametros=diametros)
    else:
        selected_diametros = request.form.getlist('diametro')
        df_filtered = df_saca[
            (df_saca['DIÁMETRO'].isin(selected_diametros)) |
            (df_saca['DIÁMETRO'].str.upper() == 'TODOS')
        ].copy()
        for diam in selected_diametros:
            cantidad = request.form.get(f'quantity_{diam}', 0, type=int)
            mask = (df_filtered['DIÁMETRO'] == diam)
            df_filtered.loc[mask, '4.CANTIDAD'] = cantidad
        final_df_renombrado = renombrar_columnas(df_filtered)
        materiales_finales.append(("FLUJO B", final_df_renombrado))
        flash("Materiales del FLUJO B guardados.")
        return redirect(url_for('flujoC'))

# FLUJO C: Tubería de Baja
@app.route('/flujoC', methods=['GET', 'POST'])
def flujoC():
    file_path = os.path.join('materiales', 'baja tubing.xlsx')
    try:
        df_baja = pd.read_excel(file_path)
        df_baja.columns = df_baja.columns.str.strip()
        for c in df_baja.columns:
            if df_baja[c].dtype == object:
                df_baja[c] = df_baja[c].astype(str).str.strip()
    except Exception as e:
        flash("Error al cargar el archivo de baja tubing: " + str(e))
        return redirect(url_for('flujoB'))
    
    if request.method == 'GET':
        diametros = sorted(df_baja['DIÁMETRO'].dropna().unique())
        return render_template('flujoC.html', diametros=diametros)
    else:
        selected_diametros = request.form.getlist('diametro')
        df_filtered = df_baja[df_baja['DIÁMETRO'].isin(selected_diametros)].copy()
        for diam in selected_diametros:
            cantidad = request.form.get(f'quantity_{diam}', 0, type=int)
            mask = (df_filtered['DIÁMETRO'] == diam)
            df_filtered.loc[mask, '4.CANTIDAD'] = cantidad
        final_df_renombrado = renombrar_columnas(df_filtered)
        materiales_finales.append(("FLUJO C", final_df_renombrado))
        flash("Materiales del FLUJO C guardados.")
        return redirect(url_for('flujoD'))

# FLUJO D: Profundiza
@app.route('/flujoD', methods=['GET', 'POST'])
def flujoD():
    file_path = os.path.join('materiales', 'profundiza.xlsx')
    if request.method == 'GET':
        return render_template('flujoD.html')
    else:
        profundiza = request.form.get('profundiza')
        if profundiza == "SI":
            try:
                df_prof = pd.read_excel(file_path)
                df_prof.columns = df_prof.columns.str.strip()
                final_df_renombrado = renombrar_columnas(df_prof)
                materiales_finales.append(("FLUJO D", final_df_renombrado))
                flash("Materiales del FLUJO D guardados.")
            except Exception as e:
                flash("Error al cargar el archivo de profundiza: " + str(e))
        else:
            flash("Se saltó el flujo D.")
        return redirect(url_for('flujoE'))

# FLUJO E: Baja varillas
@app.route('/flujoE', methods=['GET', 'POST'])
def flujoE():
    file_path = os.path.join('materiales', 'baja varillas.xlsx')
    try:
        df_varillas = pd.read_excel(file_path)
        df_varillas.columns = df_varillas.columns.str.strip()
    except Exception as e:
        flash("Error al cargar el archivo de baja varillas: " + str(e))
        return redirect(url_for('flujoD'))
    
    if request.method == 'GET':
        diametros = sorted(df_varillas['DIÁMETRO'].dropna().unique())
        return render_template('flujoE.html', diametros=diametros)
    else:
        selected_diametros = request.form.getlist('diametro')
        df_filtered = df_varillas[df_varillas['DIÁMETRO'].isin(selected_diametros)].copy()
        final_df_renombrado = renombrar_columnas(df_filtered)
        materiales_finales.append(("FLUJO E", final_df_renombrado))
        flash("Materiales del FLUJO E guardados.")
        opcion = request.form.get('opcion', 'NO')
        if opcion == "SI":
            return redirect(url_for('flujoG'))
        else:
            return redirect(url_for('flujoF'))

# FLUJO F: Abandona pozo
@app.route('/flujoF', methods=['GET', 'POST'])
def flujoF():
    file_path = os.path.join('materiales', 'abandono-recupero.xlsx')
    try:
        df_abandono = pd.read_excel(file_path)
        df_abandono.columns = df_abandono.columns.str.strip()
    except Exception as e:
        flash("Error al cargar el archivo de abandono-recupero: " + str(e))
        return redirect(url_for('flujoE'))
    
    if request.method == 'GET':
        return render_template('flujoF.html')
    else:
        respuesta = request.form.get('respuesta')
        if respuesta == "SI":
            final_df_renombrado = renombrar_columnas(df_abandono)
            materiales_finales.append(("FLUJO F", final_df_renombrado))
            flash("Materiales del FLUJO F guardados.")
        else:
            flash("Se saltó el flujo F.")
        return redirect(url_for('flujoG'))

# FLUJO G: Instalación BM
@app.route('/flujoG', methods=['GET', 'POST'])
def flujoG():
    file_path = os.path.join('materiales', 'WO.xlsx')
    if request.method == 'GET':
        return render_template('flujoG.html')
    else:
        respuesta = request.form.get('respuesta')
        if respuesta == "SI":
            try:
                df_wo = pd.read_excel(file_path)
                df_wo.columns = df_wo.columns.str.strip()
                final_df_renombrado = renombrar_columnas(df_wo)
                materiales_finales.append(("FLUJO G", final_df_renombrado))
                flash("Materiales del FLUJO G guardados.")
            except Exception as e:
                flash("Error al cargar el archivo WO.xlsx: " + str(e))
        else:
            flash("Se saltó el flujo G.")
        return redirect(url_for('flujoH'))

# FLUJO H: Material de agregación
@app.route('/flujoH', methods=['GET', 'POST'])
def flujoH():
    file_path = os.path.join('materiales', 'GENERAL(1).xlsx')
    try:
        df_general = pd.read_excel(file_path)
        df_general.columns = df_general.columns.str.strip()
    except Exception as e:
        flash("Error al cargar el archivo GENERAL(1).xlsx: " + str(e))
        return redirect(url_for('index'))
    
    if '4.CANTIDAD' not in df_general.columns:
        df_general['4.CANTIDAD'] = 0
    
    if request.method == 'GET':
        materiales = sorted(df_general["2. MATERIAL"].dropna().unique())
        return render_template('flujoH.html', materiales=materiales)
    else:
        selected_materiales = request.form.getlist('material')
        for material in selected_materiales:
            cantidad = request.form.get(f'cantidad_{material}', 0, type=float)
            mask = (df_general["2. MATERIAL"] == material)
            df_general.loc[mask, '4.CANTIDAD'] = cantidad
        df_filtered = df_general[df_general['4.CANTIDAD'] > 0].copy()
        final_df_renombrado = renombrar_columnas(df_filtered)
        materiales_finales.append(("FLUJO H", final_df_renombrado))
        flash("Materiales del FLUJO H guardados.")
        return redirect(url_for('final'))

# Página final que muestra el listado de materiales
@app.route('/final')
def final():
    results = []
    for flow, df in materiales_finales:
        html_table = df.to_html(classes="table table-striped", index=False)
        results.append((flow, html_table))
    return render_template('final.html', results=results)

if __name__ == '__main__':
    app.run(debug=True)

