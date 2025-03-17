from flask import Flask, render_template, request, redirect, url_for, flash, session
import os
import pandas as pd
from utils import renombrar_columnas

app = Flask(__name__)
app.secret_key = 'supersecretkey'  # Cambiar para producción

# Variable global para almacenar los DataFrames finales de cada flujo
materiales_finales = []

# Página de inicio: redirige al FLUJO A
@app.route('/')
def index():
    session.clear()
    return redirect(url_for('flujo_A'))

# ===============================
# FLUJO A: Ajuste de medida
# ===============================
@app.route('/flujoA', methods=['GET', 'POST'])
def flujo_A():
    if request.method == 'POST':
        ajuste_medida = request.form.get('ajuste_medida')
        if ajuste_medida == "SI":
            try:
                file_path = os.path.join('materiales', 'ajuste de medida(2).xlsx')
                df = pd.read_excel(file_path)
                df.columns = df.columns.str.strip()
                df["DIÁMETRO"] = df["DIÁMETRO"].astype(str).str.strip()
            except Exception as e:
                flash(f"Error al cargar el archivo Excel: {e}", "danger")
                return redirect(url_for('flujo_A'))
            # Se obtiene la lista de diámetros para construir el formulario de filtros
            diametros = sorted([x for x in df["DIÁMETRO"].dropna().unique() if x.upper() != "TODOS"])
            return render_template('flujo_A_filters.html', diametros=diametros)
        elif ajuste_medida == "NO":
            return redirect(url_for('flujo_B'))
    return render_template('flujo_A.html')

@app.route('/flujoA/filters', methods=['POST'])
def flujo_A_filters():
    selected_diametros = request.form.getlist('diametros')
    # Se leen los criterios para cada DIÁMETRO (aquí se espera que el usuario ingrese una lista separada por comas para “tipo”)
    filters = {}
    for diam in selected_diametros:
        tipo_raw = request.form.get(f"tipo_{diam}", "")
        # Convertir la cadena en lista (separando por comas)
        tipo_list = [x.strip() for x in tipo_raw.split(",") if x.strip()] if tipo_raw else []
        filters[diam] = {
            'tipo': tipo_list,
            'acero': request.form.get(f"acero_{diam}"),
            'acero_cup': request.form.get(f"acero_cup_{diam}"),
            'tipo_cup': request.form.get(f"tipo_cup_{diam}")
        }
    file_path = os.path.join('materiales', 'ajuste de medida(2).xlsx')
    df = pd.read_excel(file_path)
    df.columns = df.columns.str.strip()
    # Aplicar la lógica de filtrado (simplificada)
    condition = pd.Series([False] * len(df))
    for diam, crit in filters.items():
        tipo_list = crit['tipo'] if crit['tipo'] else ["TODOS"]
        if "TODOS" not in tipo_list:
            tipo_list.append("TODOS")
        acero_list = [crit['acero'], "TODOS"] if crit['acero'] and crit['acero'] != "Seleccionar" else ["TODOS"]
        acero_cup_list = [crit['acero_cup'], "TODOS"] if crit['acero_cup'] and crit['acero_cup'] != "Seleccionar" else ["TODOS"]
        tipo_cup_list = [crit['tipo_cup'], "TODOS"] if crit['tipo_cup'] and crit['tipo_cup'] != "Seleccionar" else ["TODOS"]
        cond = (df["DIÁMETRO"].isin([diam, "TODOS"]) &
                df["TIPO"].isin(tipo_list) &
                df["GRADO DE ACERO"].isin(acero_list) &
                df["GRADO DE ACERO CUPLA"].isin(acero_cup_list) &
                df["TIPO DE CUPLA"].isin(tipo_cup_list))
        condition = condition | cond
    filtered_df = df[condition]
    filtered_df_renombrado = renombrar_columnas(filtered_df)
    materiales_finales.append(("FLUJO A", filtered_df_renombrado))
    flash("Materiales del FLUJO A guardados.", "success")
    return redirect(url_for('flujo_H'))

# ===============================
# FLUJO B: Tubo de saca
# ===============================
@app.route('/flujoB', methods=['GET', 'POST'])
def flujo_B():
    if request.method == 'POST':
        saca_tubing = request.form.get('saca_tubing')
        if saca_tubing == "SI":
            file_path = os.path.join('materiales', 'saca_tubing.xlsx')
            if not os.path.exists(file_path):
                flash(f"El archivo {file_path} no se encontró.", "danger")
                return redirect(url_for('flujo_B'))
            df = pd.read_excel(file_path)
            df.columns = df.columns.str.strip()
            diametros = sorted([d for d in df['DIÁMETRO'].unique() if d.upper() != 'TODOS'])
            return render_template('flujo_B_form.html', diametros=diametros)
        elif saca_tubing == "NO":
            return redirect(url_for('flujo_C'))
    return render_template('flujo_B.html')

@app.route('/flujoB/submit', methods=['POST'])
def flujo_B_submit():
    selected_diametros = request.form.getlist('diametros')
    quantities = {}
    for diam in selected_diametros:
        qty = request.form.get(f"qty_{diam}", type=float)
        quantities[diam] = qty
    file_path = os.path.join('materiales', 'saca_tubing.xlsx')
    df = pd.read_excel(file_path)
    df.columns = df.columns.str.strip()
    df_filtered = df[(df['DIÁMETRO'].isin(selected_diametros)) | (df['DIÁMETRO'].str.upper() == 'TODOS')].copy()
    for diam, qty in quantities.items():
        mask = (df_filtered['DIÁMETRO'] == diam)
        df_filtered.loc[mask, '4.CANTIDAD'] = qty
    df_filtered_renombrado = renombrar_columnas(df_filtered)
    materiales_finales.append(("FLUJO B", df_filtered_renombrado))
    flash("Materiales del FLUJO B guardados.", "success")
    return redirect(url_for('flujo_C'))

# ===============================
# FLUJO C: Tubería de Baja
# ===============================
@app.route('/flujoC', methods=['GET', 'POST'])
def flujo_C():
    if request.method == 'POST':
        baja_tubing = request.form.get('baja_tubing')
        if baja_tubing == "SI":
            file_path = os.path.join('materiales', 'baja_tubing.xlsx')
            if not os.path.exists(file_path):
                flash("El archivo de baja tubing no se encontró.", "danger")
                return redirect(url_for('flujo_C'))
            df = pd.read_excel(file_path)
            df.columns = df.columns.str.strip()
            diametros = sorted([x for x in df['DIÁMETRO'].unique() if x != "TODOS"])
            return render_template('flujo_C_form.html', diametros=diametros)
        else:
            flash("No se procede con Baja Tubing.", "info")
            return redirect(url_for('flujo_D'))
    return render_template('flujo_C.html')

@app.route('/flujoC/submit', methods=['POST'])
def flujo_C_submit():
    selected_diametros = request.form.getlist('diametros')
    file_path = os.path.join('materiales', 'baja_tubing.xlsx')
    df = pd.read_excel(file_path)
    df.columns = df.columns.str.strip()
    # Lógica simplificada: filtrar por los diámetros seleccionados
    df_filtered = df[df['DIÁMETRO'].isin(selected_diametros)]
    df_filtered_renombrado = renombrar_columnas(df_filtered)
    materiales_finales.append(("FLUJO C", df_filtered_renombrado))
    flash("Materiales del FLUJO C guardados.", "success")
    return redirect(url_for('flujo_D'))

# ===============================
# FLUJO D: Profundiza
# ===============================
@app.route('/flujoD', methods=['GET', 'POST'])
def flujo_D():
    if request.method == 'POST':
        profundizar = request.form.get('profundizar')
        if profundizar == "SI":
            file_path = os.path.join('materiales', 'profundiza.xlsx')
            if not os.path.exists(file_path):
                flash("El archivo de profundiza no se encontró.", "danger")
                return redirect(url_for('flujo_D'))
            df = pd.read_excel(file_path)
            df.columns = df.columns.str.strip()
            # Se determina la columna de DIÁMETRO según disponibilidad
            if "DIÁMETRO" in df.columns:
                diametros = df["DIÁMETRO"].unique().tolist()
            else:
                diametros = df["DIÁMETRO CSG"].unique().tolist()
            return render_template('flujo_D_form.html', diametros=diametros)
        else:
            flash("No se profundizará en la información.", "info")
            return redirect(url_for('flujo_E'))
    return render_template('flujo_D.html')

@app.route('/flujoD/submit', methods=['POST'])
def flujo_D_submit():
    selected_diametros = request.form.getlist('diametros')
    quantities = {}
    for diam in selected_diametros:
        qty = request.form.get(f"qty_{diam}", type=float)
        quantities[diam] = qty
    file_path = os.path.join('materiales', 'profundiza.xlsx')
    df = pd.read_excel(file_path)
    df.columns = df.columns.str.strip()
    for diam, qty in quantities.items():
        mask = df["DIÁMETRO"] == diam if "DIÁMETRO" in df.columns else df["DIÁMETRO CSG"] == diam
        df.loc[mask, "4.CANTIDAD"] = qty
    df_filtered_renombrado = renombrar_columnas(df[df["DIÁMETRO"].isin(selected_diametros)])
    materiales_finales.append(("FLUJO D", df_filtered_renombrado))
    flash("Materiales del FLUJO D guardados.", "success")
    return redirect(url_for('flujo_E'))

# ===============================
# FLUJO E: Baja varillas
# ===============================
@app.route('/flujoE', methods=['GET', 'POST'])
def flujo_E():
    if request.method == 'POST':
        baja_varilla = request.form.get('baja_varilla')
        if baja_varilla == "SI":
            file_path = os.path.join('materiales', 'baja_varillas.xlsx')
            if not os.path.exists(file_path):
                flash("El archivo de baja varillas no se encontró.", "danger")
                return redirect(url_for('flujo_E'))
            df = pd.read_excel(file_path)
            df.columns = df.columns.str.strip()
            diametros = sorted([x for x in df["DIÁMETRO"].dropna().unique() if x.upper() != "TODOS"])
            return render_template('flujo_E_filters.html', diametros=diametros)
        else:
            return redirect(url_for('flujo_F'))
    return render_template('flujo_E.html')

@app.route('/flujoE/filters', methods=['POST'])
def flujo_E_filters():
    selected_diametros = request.form.getlist('diametros')
    file_path = os.path.join('materiales', 'baja_varillas.xlsx')
    df = pd.read_excel(file_path)
    df.columns = df.columns.str.strip()
    condition = pd.Series([False]*len(df))
    for diam in selected_diametros:
        condition = condition | (df["DIÁMETRO"] == diam)
    df_filtered = df[condition]
    df_filtered_renombrado = renombrar_columnas(df_filtered)
    materiales_finales.append(("FLUJO E", df_filtered_renombrado))
    flash("Materiales del FLUJO E guardados.", "success")
    return redirect(url_for('flujo_G'))

# ===============================
# FLUJO F: Abandona pozo
# ===============================
@app.route('/flujoF', methods=['GET', 'POST'])
def flujo_F():
    if request.method == 'POST':
        abandono = request.form.get('abandono')
        if abandono == "SI":
            file_path = os.path.join('materiales', 'abandono_recupero.xlsx')
            if not os.path.exists(file_path):
                flash("El archivo de abandono-recupero no se encontró.", "danger")
                return redirect(url_for('flujo_F'))
            df = pd.read_excel(file_path)
            df.columns = df.columns.str.strip()
            diametros = df["DIÁMETRO"].dropna().unique().tolist()
            if "TODOS" not in diametros:
                diametros.insert(0, "TODOS")
            csg = df["DIÁMETRO CSG"].dropna().unique().tolist()
            if "TODOS" not in csg:
                csg.insert(0, "TODOS")
            return render_template('flujo_F_form.html', diametros=diametros, csg=csg)
        else:
            return redirect(url_for('flujo_H'))
    return render_template('flujo_F.html')

@app.route('/flujoF/submit', methods=['POST'])
def flujo_F_submit():
    selected_diametros = request.form.getlist('diametros')
    selected_csg = request.form.get('diam_csg')
    file_path = os.path.join('materiales', 'abandono_recupero.xlsx')
    df = pd.read_excel(file_path)
    df.columns = df.columns.str.strip()
    if "TODOS" not in selected_diametros:
        df = df[df["DIÁMETRO"].isin(selected_diametros)]
    if selected_csg != "TODOS":
        df = df[df["DIÁMETRO CSG"] == selected_csg]
    for diam in selected_diametros:
        qty = request.form.get(f"qty_{diam}", type=float)
        if qty is not None:
            mask = (df["DIÁMETRO"] == diam)
            df.loc[mask & df["4.CANTIDAD"].isna(), "4.CANTIDAD"] = qty
    df_filtered_renombrado = renombrar_columnas(df)
    materiales_finales.append(("FLUJO F", df_filtered_renombrado))
    flash("Materiales del FLUJO F guardados.", "success")
    return redirect(url_for('flujo_H'))

# ===============================
# FLUJO G: Instalación BM
# ===============================
@app.route('/flujoG', methods=['GET', 'POST'])
def flujo_G():
    if request.method == 'POST':
        wo_bm = request.form.get('wo_bm')
        if wo_bm == "SI":
            file_path = os.path.join('materiales', 'WO.xlsx')
            try:
                df = pd.read_excel(file_path)
                df_renombrado = renombrar_columnas(df)
                materiales_finales.append(("FLUJO G", df_renombrado))
                flash("Materiales del FLUJO G guardados.", "success")
            except Exception as e:
                flash(f"Error al cargar Excel: {e}", "danger")
            return redirect(url_for('flujo_H'))
        else:
            flash("No se mostrarán los materiales de WO.", "info")
            return redirect(url_for('flujo_H'))
    return render_template('flujo_G.html')

# ===============================
# FLUJO H: Material de agregación
# ===============================
@app.route('/flujoH', methods=['GET', 'POST'])
def flujo_H():
    file_path = os.path.join('materiales', 'GENERAL.xlsx')
    if request.method == 'POST':
        agregar_material = request.form.get('agregar_material')
        if agregar_material == "SI":
            selected_materiales = request.form.getlist('materiales')
            quantities = {}
            for mat in selected_materiales:
                qty = request.form.get(f"qty_{mat}", type=float)
                quantities[mat] = qty
            df = pd.read_excel(file_path)
            df.columns = df.columns.str.strip()
            for mat, qty in quantities.items():
                df.loc[df["2. MATERIAL"].astype(str) == mat, "4.CANTIDAD"] = qty
            assigned_df = df[(df["2. MATERIAL"].astype(str).isin(selected_materiales)) & (df["4.CANTIDAD"] > 0)]
            if not assigned_df.empty:
                assigned_df_renombrado = renombrar_columnas(assigned_df)
                materiales_finales.append(("FLUJO H", assigned_df_renombrado))
            flash("Materiales del FLUJO H guardados.", "success")
        return redirect(url_for('result'))
    else:
        try:
            df = pd.read_excel(file_path)
            df.columns = df.columns.str.strip()
            if "2. MATERIAL" in df.columns:
                materiales = df["2. MATERIAL"].astype(str).unique().tolist()
            else:
                materiales = []
        except Exception as e:
            flash(f"Error al cargar el archivo GENERAL: {e}", "danger")
            materiales = []
        return render_template('flujo_H.html', materiales=materiales)

# ===============================
# Página de Resultados Finales
# ===============================
@app.route('/result')
def result():
    return render_template('result.html', materiales_finales=materiales_finales)

if __name__ == '__main__':
    app.run(debug=True)



