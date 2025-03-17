import os
import pandas as pd
from flask import Flask, render_template, request, redirect, url_for, session

app = Flask(__name__)
app.secret_key = 'tu_clave_secreta'  # Necesario para sesiones

# Lista global para almacenar los DataFrames finales de cada flujo
materiales_finales = []


# ---------------------------
# Función auxiliar
# ---------------------------
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


# ---------------------------
# FLUJO A: Ajuste de medida
# ---------------------------
@app.route('/', methods=["GET", "POST"])
def index():
    # Página inicial: pregunta si se realiza ajuste de medida
    if request.method == "POST":
        ajuste = request.form.get("ajuste_medida")
        if ajuste == "SI":
            return redirect(url_for("flowA_filters"))
        elif ajuste == "NO":
            return redirect(url_for("flowB"))
    return render_template("index.html")


@app.route('/flowA/filters', methods=["GET", "POST"])
def flowA_filters():
    # Se carga el Excel de ajuste de medida desde la carpeta "materiales"
    file_path = os.path.join("materiales", "ajuste de medida(2).xlsx")
    try:
        df = pd.read_excel(file_path)
        df.columns = df.columns.str.strip()
        df["DIÁMETRO"] = df["DIÁMETRO"].astype(str).str.strip()
    except Exception as e:
        return f"Error al cargar el Excel: {e}"
    
    # Se obtienen los DIÁMETRO disponibles (excluyendo "TODOS")
    diametros = sorted([x for x in df["DIÁMETRO"].dropna().unique() if str(x).upper() != "TODOS"])
    
    if request.method == "POST":
        selected_diams = request.form.getlist("diametro")
        if not selected_diams:
            selected_diams = ["TODOS"]
        # Se recopilan los filtros para cada DIÁMETRO (los nombres de los campos en el formulario deben ser, por ejemplo, "tipo_<diam>")
        all_filters = {}
        for diam in selected_diams:
            if diam == "TODOS":
                all_filters[diam] = {
                    "tipo_list": ["TODOS"],
                    "acero_list": ["TODOS"],
                    "acero_cup_list": ["TODOS"],
                    "tipo_cup_list": ["TODOS"]
                }
            else:
                tipo_sel = request.form.getlist(f"tipo_{diam}")
                if not tipo_sel:
                    tipo_sel = ["TODOS"]
                else:
                    tipo_sel.append("TODOS")
                ac = request.form.get(f"acero_{diam}")
                acero_list = ["TODOS"] if ac == "Seleccionar" else [ac, "TODOS"]
                ac_cup = request.form.get(f"acero_cup_{diam}")
                acero_cup_list = ["TODOS"] if ac_cup == "Seleccionar" else [ac_cup, "TODOS"]
                t_cup = request.form.get(f"tipo_cup_{diam}")
                tipo_cup_list = ["TODOS"] if t_cup == "Seleccionar" else [t_cup, "TODOS"]
                all_filters[diam] = {
                    "tipo_list": tipo_sel,
                    "acero_list": acero_list,
                    "acero_cup_list": acero_cup_list,
                    "tipo_cup_list": tipo_cup_list
                }
        # Se aplica la lógica de filtrado
        final_condition = pd.Series([False] * len(df))
        for diam_value, fdict in all_filters.items():
            temp_cond_diam = pd.Series([False] * len(df))
            for tipo_val in fdict["tipo_list"]:
                cond = (df["DIÁMETRO"].isin([diam_value, "TODOS"]) &
                        df["TIPO"].isin([tipo_val, "TODOS"]) &
                        df["GRADO DE ACERO"].isin(fdict["acero_list"]) &
                        df["GRADO DE ACERO CUPLA"].isin(fdict["acero_cup_list"]) &
                        df["TIPO DE CUPLA"].isin(fdict["tipo_cup_list"]))
                temp_cond_diam = temp_cond_diam | cond
            final_condition = final_condition | temp_cond_diam
        final_df = df[final_condition]
        final_df_renombrado = renombrar_columnas(final_df)
        materiales_finales.append(("FLUJO A", final_df_renombrado))
        # En FLUJO A, si se responde SI, se salta directamente a Flow H
        return redirect(url_for("flowH"))
    
    # Se renderiza un formulario (flowA_filters.html) que muestre:
    # – Una lista de checkboxes para seleccionar DIÁMETRO(s)
    # – Para cada DIÁMETRO seleccionado, campos para elegir TIPO, GRADO DE ACERO, etc.
    return render_template("flowA_filters.html", diametros=diametros)


# ---------------------------
# FLUJO B: Tubo de saca
# ---------------------------
@app.route('/flowB', methods=["GET", "POST"])
def flowB():
    file_path = os.path.join("materiales", "saca tubing.xlsx")
    if request.method == "POST":
        opcion = request.form.get("saca_tubing")
        if opcion == "SI":
            try:
                df = pd.read_excel(file_path)
                df.columns = df.columns.str.strip()
                for c in df.columns:
                    if df[c].dtype == object:
                        df[c] = df[c].astype(str).str.strip()
            except Exception as e:
                return f"Error al cargar saca tubing: {e}"
            selected_diametros = request.form.getlist("diametro")
            if not selected_diametros:
                selected_diametros = ["TODOS"]
            df_filtered = df[(df["DIÁMETRO"].isin(selected_diametros)) | (df["DIÁMETRO"].str.upper() == "TODOS")].copy()
            # Se espera que en el formulario se envíe un campo de cantidad para cada DIÁMETRO, con nombre "qty_<diametro>"
            for diam in selected_diametros:
                qty = request.form.get(f"qty_{diam}")
                if qty:
                    try:
                        qty = float(qty)
                    except:
                        qty = 0
                    mask = (df_filtered["DIÁMETRO"] == diam)
                    df_filtered.loc[mask, "4.CANTIDAD"] = qty
            df_filtered_renombrado = renombrar_columnas(df_filtered)
            materiales_finales.append(("FLUJO B", df_filtered_renombrado))
        # Continúa al siguiente flujo
        return redirect(url_for("flowC"))
    return render_template("flowB.html")


# ---------------------------
# FLUJO C: Tubería de Baja
# ---------------------------
@app.route('/flowC', methods=["GET", "POST"])
def flowC():
    file_path = os.path.join("materiales", "baja tubing.xlsx")
    try:
        df = pd.read_excel(file_path)
        df.columns = df.columns.str.strip()
        for col in df.columns:
            if df[col].dtype == object:
                df[col] = df[col].astype(str).str.strip()
    except Exception as e:
        return f"Error en Flow C: {e}"
    
    if request.method == "POST":
        selected_diametros = request.form.getlist("diametro")
        if not selected_diametros:
            selected_diametros = ["TODOS"]
        selected_tipos = {}
        for d in selected_diametros:
            tipos = request.form.getlist(f"tipo_{d}")
            if not tipos:
                tipos = ["TODOS"]
            selected_tipos[d] = tipos
        selected_csg = request.form.get("diametro_csg")
        if selected_csg and selected_csg != "TODOS":
            selected_csg_filter = [selected_csg, "TODOS"]
        else:
            selected_csg_filter = ["TODOS"]
        # Procesa las cantidades ingresadas (campo "qty_<diametro>_<tipo>")
        for d in selected_diametros:
            for t in selected_tipos[d]:
                qty = request.form.get(f"qty_{d}_{t}")
                if qty:
                    try:
                        qty = float(qty)
                    except:
                        qty = 0
                    condition = (df["DIÁMETRO"].isin([d, "TODOS"]) & df["TIPO"].isin([t, "TODOS"]))
                    df.loc[condition & df["4.CANTIDAD"].isna(), "4.CANTIDAD"] = qty
        final_condition = pd.Series([False] * len(df))
        for diam_value, tipos_list in selected_tipos.items():
            temp_cond_diam = pd.Series([False] * len(df))
            for tipo_val in tipos_list:
                cond = (df["DIÁMETRO"].isin([diam_value, "TODOS"]) & df["TIPO"].isin([tipo_val, "TODOS"]))
                temp_cond_diam = temp_cond_diam | cond
            final_condition = final_condition | temp_cond_diam
        final_df = df[final_condition]
        final_df_renombrado = renombrar_columnas(final_df)
        materiales_finales.append(("FLUJO C", final_df_renombrado))
        return redirect(url_for("flowD"))
    
    # Para la vista GET se pasan los valores únicos de DIÁMETRO y DIÁMETRO CSG para construir el formulario
    unique_diametros = sorted([x for x in df["DIÁMETRO"].unique() if x != "TODOS"])
    unique_csg = sorted([x for x in df["DIÁMETRO CSG"].unique() if x != "TODOS"])
    return render_template("flowC.html", diametros=unique_diametros, csg_options=unique_csg)


# ---------------------------
# FLUJO D: Profundiza
# ---------------------------
@app.route('/flowD', methods=["GET", "POST"])
def flowD():
    if request.method == "POST":
        profundizar = request.form.get("profundizar")
        if profundizar == "SI":
            return redirect(url_for("flowD_detail"))
        else:
            return redirect(url_for("flowE"))
    return render_template("flowD.html")


@app.route('/flowD/detail', methods=["GET", "POST"])
def flowD_detail():
    file_path = os.path.join("materiales", "profundiza.xlsx")
    try:
        df = pd.read_excel(file_path)
        df.columns = df.columns.str.strip()
        for col in df.columns:
            if df[col].dtype == object:
                df[col] = df[col].astype(str).str.strip()
    except Exception as e:
        return f"Error en Flow D: {e}"
    
    if request.method == "POST":
        selected_diametros = request.form.getlist("diametro")
        if not selected_diametros:
            return "No se seleccionaron diámetros"
        # Procesa cantidades para cada DIÁMETRO (campo "qty_<diametro>")
        for d in selected_diametros:
            qty = request.form.get(f"qty_{d}")
            if qty:
                try:
                    qty = float(qty)
                except:
                    qty = 0
                condition = (df["DIÁMETRO"].isin([d]))
                df.loc[condition, "4.CANTIDAD"] = qty
        final_df = df[df["DIÁMETRO"].isin(selected_diametros)]
        final_df_renombrado = renombrar_columnas(final_df)
        materiales_finales.append(("FLUJO D", final_df_renombrado))
        return redirect(url_for("flowE"))
    
    diametros = sorted(df["DIÁMETRO"].unique().tolist())
    return render_template("flowD_detail.html", diametros=diametros)


# ---------------------------
# FLUJO E: Baja varillas
# ---------------------------
@app.route('/flowE', methods=["GET", "POST"])
def flowE():
    if request.method == "POST":
        baja_varilla = request.form.get("baja_varilla")
        if baja_varilla == "SI":
            return redirect(url_for("flowE_filters"))
        else:
            return redirect(url_for("flowF"))
    return render_template("flowE.html")


@app.route('/flowE/filters', methods=["GET", "POST"])
def flowE_filters():
    file_path = os.path.join("materiales", "baja varillas.xlsx")
    try:
        df = pd.read_excel(file_path)
        df.columns = df.columns.str.strip()
        df["DIÁMETRO"] = df["DIÁMETRO"].astype(str).str.strip()
    except Exception as e:
        return f"Error en Flow E: {e}"
    
    unique_diametros = sorted([x for x in df["DIÁMETRO"].dropna().unique() if x.upper() != "TODOS"])
    
    if request.method == "POST":
        selected_diams = request.form.getlist("diametro")
        if not selected_diams:
            selected_diams = ["TODOS"]
        all_filters = {}
        for diam in selected_diams:
            if diam == "TODOS":
                all_filters[diam] = {
                    "tipo_list": ["TODOS"],
                    "acero_list": ["TODOS"],
                    "acero_cup_list": ["TODOS"],
                    "tipo_cup_list": ["TODOS"]
                }
            else:
                tipo_sel = request.form.getlist(f"tipo_{diam}")
                if not tipo_sel:
                    tipo_sel = ["TODOS"]
                else:
                    tipo_sel.append("TODOS")
                ac = request.form.get(f"acero_{diam}")
                acero_list = ["TODOS"] if ac == "Seleccionar" else [ac, "TODOS"]
                ac_cup = request.form.get(f"acero_cup_{diam}")
                acero_cup_list = ["TODOS"] if ac_cup == "Seleccionar" else [ac_cup, "TODOS"]
                t_cup = request.form.get(f"tipo_cup_{diam}")
                tipo_cup_list = ["TODOS"] if t_cup == "Seleccionar" else [t_cup, "TODOS"]
                all_filters[diam] = {
                    "tipo_list": tipo_sel,
                    "acero_list": acero_list,
                    "acero_cup_list": acero_cup_list,
                    "tipo_cup_list": tipo_cup_list
                }
        final_condition = pd.Series([False] * len(df))
        for diam_value, fdict in all_filters.items():
            temp_cond_diam = pd.Series([False] * len(df))
            for tipo_val in fdict["tipo_list"]:
                cond = (df["DIÁMETRO"].isin([diam_value, "TODOS"]) &
                        df["TIPO"].isin([tipo_val, "TODOS"]) &
                        df["GRADO DE ACERO"].isin(fdict["acero_list"]) &
                        df["GRADO DE ACERO CUPLA"].isin(fdict["acero_cup_list"]) &
                        df["TIPO DE CUPLA"].isin(fdict["tipo_cup_list"]))
                temp_cond_diam = temp_cond_diam | cond
            final_condition = final_condition | temp_cond_diam
        final_df = df[final_condition]
        final_df_renombrado = renombrar_columnas(final_df)
        materiales_finales.append(("FLUJO E", final_df_renombrado))
        return redirect(url_for("flowG"))
    
    return render_template("flowE_filters.html", diametros=unique_diametros)


# ---------------------------
# FLUJO F: Abandona pozo
# ---------------------------
@app.route('/flowF', methods=["GET", "POST"])
def flowF():
    file_path = os.path.join("materiales", "abandono-recupero.xlsx")
    try:
        df = pd.read_excel(file_path)
        df.columns = df.columns.str.strip()
        for col in df.columns:
            if df[col].dtype == object:
                df[col] = df[col].astype(str).str.strip()
    except Exception as e:
        return f"Error en Flow F: {e}"
    
    if request.method == "POST":
        selected_diametros = request.form.getlist("diametro")
        selected_diametro_csg = request.form.get("diametro_csg")
        filtered_df = df.copy()
        if "TODOS" not in selected_diametros:
            filtered_df = filtered_df[filtered_df["DIÁMETRO"].isin(selected_diametros)]
        if selected_diametro_csg:
            filtered_df = filtered_df[filtered_df["DIÁMETRO CSG"].isin([selected_diametro_csg, "TODOS"])]
        # Se esperan cantidades para cada DIÁMETRO específico (campo "qty_<diametro>")
        diam_especificos = [d for d in selected_diametros if d != "TODOS"]
        for d in diam_especificos:
            qty = request.form.get(f"qty_{d}")
            if qty:
                try:
                    qty = float(qty)
                except:
                    qty = 0
                mask = (filtered_df["DIÁMETRO"] == d) & filtered_df["4.CANTIDAD"].isna()
                filtered_df.loc[mask, "4.CANTIDAD"] = qty
        final_df_renombrado = renombrar_columnas(filtered_df)
        materiales_finales.append(("FLUJO F", final_df_renombrado))
        return redirect(url_for("flowH"))
    
    unique_diametros = df["DIÁMETRO"].dropna().unique().tolist()
    if "TODOS" not in unique_diametros:
        unique_diametros.insert(0, "TODOS")
    unique_diametros_csg = df["DIÁMETRO CSG"].dropna().unique().tolist()
    if "TODOS" not in unique_diametros_csg:
        unique_diametros_csg.insert(0, "TODOS")
    return render_template("flowF.html", diametros=unique_diametros, diametros_csg=unique_diametros_csg)


# ---------------------------
# FLUJO G: Instalación BM
# ---------------------------
@app.route('/flowG', methods=["GET", "POST"])
def flowG():
    file_path = os.path.join("materiales", "WO.xlsx")
    if request.method == "POST":
        wo_option = request.form.get("wo_bm")
        if wo_option == "SI":
            try:
                df = pd.read_excel(file_path)
                df_renombrado = renombrar_columnas(df)
                materiales_finales.append(("FLUJO G", df_renombrado))
            except Exception as e:
                return f"Error en Flow G: {e}"
        return redirect(url_for("flowH"))
    return render_template("flowG.html")


# ---------------------------
# FLUJO H: Material de agregación
# ---------------------------
@app.route('/flowH', methods=["GET", "POST"])
def flowH():
    file_path = os.path.join("materiales", "GENERAL(1).xlsx")
    try:
        df = pd.read_excel(file_path)
        df.columns = df.columns.str.strip()
        if "4.CANTIDAD" not in df.columns:
            df["4.CANTIDAD"] = 0
    except Exception as e:
        df = pd.DataFrame()
    
    if request.method == "POST":
        agregar = request.form.get("agregar_material")
        if agregar == "SI":
            selected_materials = request.form.getlist("materiales")
            # Procesa cantidades para cada material (campo "qty_<material>")
            for mat in selected_materials:
                qty = request.form.get(f"qty_{mat}")
                if qty:
                    try:
                        qty = float(qty)
                    except:
                        qty = 0
                    df.loc[df["2. MATERIAL"].astype(str) == mat, "4.CANTIDAD"] = qty
            assigned_df = df[
                df["2. MATERIAL"].astype(str).isin(selected_materials) &
                (df["4.CANTIDAD"] > 0)
            ]
            if not assigned_df.empty:
                assigned_df_renombrado = renombrar_columnas(assigned_df)
                materiales_finales.append(("FLUJO H", assigned_df_renombrado))
        # En cualquier caso, se redirige a la pantalla final
        return redirect(url_for("final_list"))
    
    if not df.empty and "2. MATERIAL" in df.columns:
        materiales = df["2. MATERIAL"].astype(str).unique().tolist()
    else:
        materiales = []
    return render_template("flowH.html", materiales=materiales)


# ---------------------------
# Pantalla Final: Listado de Materiales
# ---------------------------
@app.route('/final')
def final_list():
    return render_template("final.html", materiales_finales=materiales_finales)


if __name__ == '__main__':
    app.run(debug=True)



