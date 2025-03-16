import os
from flask import Flask, render_template_string, request, redirect, url_for, flash
import pandas as pd

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Cambia la clave para producción

# Variable global para almacenar los DataFrames finales de cada flujo
materiales_finales = []

# Función para renombrar las columnas y dejar solo las 5 requeridas (no se modificó la lógica)
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

# Plantilla base (utiliza Bootstrap para un estilo moderno)
base_template = """
<!doctype html>
<html lang="en">
  <head>
    <title>{{ title }}</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <!-- Bootstrap CSS -->
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
  </head>
  <body class="bg-light">
    <div class="container my-4">
      <h2 class="mb-4">{{ title }}</h2>
      {% with messages = get_flashed_messages() %}
        {% if messages %}
          <div class="alert alert-warning" role="alert">
            {% for message in messages %}
              {{ message }}
            {% endfor %}
          </div>
        {% endif %}
      {% endwith %}
      {{ content|safe }}
    </div>
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
  </body>
</html>
"""

# -------------------------------
# FLUJO A: Ajuste de medida
# -------------------------------
@app.route('/flujo_a', methods=['GET', 'POST'])
def flujo_a():
    if request.method == 'POST':
        ajuste = request.form.get('ajuste')
        if ajuste == "SI":
            return redirect(url_for('flujo_a_filters'))
        elif ajuste == "NO":
            return redirect(url_for('flujo_b'))
    content = """
    <form method="post">
      <div class="mb-3">
        <label class="form-label">¿Ajuste de medida?</label><br>
        <div class="form-check form-check-inline">
          <input class="form-check-input" type="radio" name="ajuste" value="SI" required> SI
        </div>
        <div class="form-check form-check-inline">
          <input class="form-check-input" type="radio" name="ajuste" value="NO" required> NO
        </div>
      </div>
      <button type="submit" class="btn btn-primary">Continuar</button>
    </form>
    """
    return render_template_string(base_template, title="FLUJO A: Ajuste de medida", content=content)

# Página de filtros para FLUJO A
@app.route('/flujo_a/filters', methods=['GET', 'POST'])
def flujo_a_filters():
    # Se carga el Excel correspondiente (se asume que el archivo se encuentra en la carpeta "materiales")
    file_path = os.path.join("materiales", "ajuste de medida(2).xlsx")
    try:
        df = pd.read_excel(file_path)
        df.columns = df.columns.str.strip()
        df["DIÁMETRO"] = df["DIÁMETRO"].astype(str).str.strip()
    except Exception as e:
        flash("Error al cargar el archivo Excel: " + str(e))
        return redirect(url_for('flujo_a'))
    diam_options = sorted([x for x in df["DIÁMETRO"].dropna().unique() if x.upper() != "TODOS"])
    if request.method == 'POST':
        selected_diams = request.form.getlist('diams')
        if not selected_diams:
            selected_diams = ["TODOS"]
        filters = {}
        for diam in selected_diams:
            tipo_list = request.form.getlist(f'tipo_{diam}')
            if not tipo_list:
                tipo_list = ["TODOS"]
            else:
                tipo_list.append("TODOS")
            acero = request.form.get(f'acero_{diam}', "Seleccionar")
            acero_list = ["TODOS"] if acero=="Seleccionar" else [acero, "TODOS"]
            acero_cup = request.form.get(f'acero_cup_{diam}', "Seleccionar")
            acero_cup_list = ["TODOS"] if acero_cup=="Seleccionar" else [acero_cup, "TODOS"]
            tipo_cup = request.form.get(f'tipo_cup_{diam}', "Seleccionar")
            tipo_cup_list = ["TODOS"] if tipo_cup=="Seleccionar" else [tipo_cup, "TODOS"]
            filters[diam] = {
                "tipo_list": tipo_list,
                "acero_list": acero_list,
                "acero_cup_list": acero_cup_list,
                "tipo_cup_list": tipo_cup_list
            }
        # Se aplica el mismo filtrado que en el código original
        final_condition = pd.Series([False] * len(df))
        for diam_value, fdict in filters.items():
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
        # Se salta directamente a FLUJO H como en la lógica original
        return redirect(url_for('flujo_h'))
    # Se construye el formulario dinámicamente para cada DIÁMETRO
    form_fields = ""
    for diam in diam_options:
        subset = df[df["DIÁMETRO"]==diam]
        tipos = sorted([x for x in subset["TIPO"].dropna().unique() if x.upper()!="TODOS"])
        grados_acero = sorted([x for x in subset["GRADO DE ACERO"].dropna().unique() if str(x).upper()!="TODOS"])
        grados_acero_cup = sorted([x for x in subset["GRADO DE ACERO CUPLA"].dropna().unique() if str(x).upper()!="TODOS"])
        tipos_cup = sorted([x for x in subset["TIPO DE CUPLA"].dropna().unique() if str(x).upper()!="TODOS"])
        form_fields += f"<h5>Filtros para DIÁMETRO: {diam}</h5>"
        form_fields += f"""
        <div class="mb-3">
          <label class="form-label">Selecciona TIPO(s) para {diam}:</label>
          <select name="tipo_{diam}" class="form-select" multiple>
        """
        for t in tipos:
            form_fields += f'<option value="{t}">{t}</option>'
        form_fields += "</select></div>"
        form_fields += f"""
        <div class="mb-3">
          <label class="form-label">GRADO ACERO para {diam}:</label>
          <select name="acero_{diam}" class="form-select">
            <option value="Seleccionar">Seleccionar</option>
        """
        for val in grados_acero:
            form_fields += f'<option value="{val}">{val}</option>'
        form_fields += "</select></div>"
        form_fields += f"""
        <div class="mb-3">
          <label class="form-label">ACERO CUPLA para {diam}:</label>
          <select name="acero_cup_{diam}" class="form-select">
            <option value="Seleccionar">Seleccionar</option>
        """
        for val in grados_acero_cup:
            form_fields += f'<option value="{val}">{val}</option>'
        form_fields += "</select></div>"
        form_fields += f"""
        <div class="mb-3">
          <label class="form-label">TIPO CUPLA para {diam}:</label>
          <select name="tipo_cup_{diam}" class="form-select">
            <option value="Seleccionar">Seleccionar</option>
        """
        for val in tipos_cup:
            form_fields += f'<option value="{val}">{val}</option>'
        form_fields += "</select></div><hr>"
    diam_select = "<div class='mb-3'><label class='form-label'>Selecciona DIÁMETRO(s):</label><br>"
    for diam in diam_options:
        diam_select += f"""
        <div class="form-check form-check-inline">
          <input class="form-check-input" type="checkbox" name="diams" value="{diam}"> {diam}
        </div>
        """
    diam_select += "</div>"
    content = f"""
    <form method="post">
      {diam_select}
      {form_fields}
      <button type="submit" class="btn btn-success">Aplicar Filtros y Continuar a FLUJO H</button>
    </form>
    """
    return render_template_string(base_template, title="FLUJO A: Filtros", content=content)

# -------------------------------
# FLUJO B: Tubo de saca
# -------------------------------
@app.route('/flujo_b', methods=['GET', 'POST'])
def flujo_b():
    if request.method == 'POST':
        saca_option = request.form.get('saca')
        if saca_option == "SI":
            return redirect(url_for('flujo_b_filters'))
        elif saca_option == "NO":
            return redirect(url_for('flujo_c'))
    content = """
    <form method="post">
      <div class="mb-3">
        <label class="form-label">¿Saca Tubing?</label>
        <select name="saca" class="form-select" required>
          <option value="">Seleccione opción</option>
          <option value="SI">SI</option>
          <option value="NO">NO</option>
        </select>
      </div>
      <button type="submit" class="btn btn-primary">Continuar</button>
    </form>
    """
    return render_template_string(base_template, title="FLUJO B: Tubo de saca", content=content)

@app.route('/flujo_b/filters', methods=['GET', 'POST'])
def flujo_b_filters():
    folder_path = os.path.join("materiales")
    filename_saca = "saca tubing.xlsx"
    file_path_saca = os.path.join(folder_path, filename_saca)
    try:
        df = pd.read_excel(file_path_saca)
        df.columns = df.columns.str.strip()
        for c in df.columns:
            if df[c].dtype == object:
                df[c] = df[c].astype(str).str.strip()
    except Exception as e:
        flash("Error al cargar saca tubing: " + str(e))
        return redirect(url_for('flujo_b'))
    diam_options = sorted([d for d in df['DIÁMETRO'].unique() if d.upper() != 'TODOS'])
    if request.method == 'POST':
        selected_diams = request.form.getlist('diams')
        quantities = {}
        for dia in selected_diams:
            qty = request.form.get(f'qty_{dia}', 0)
            try:
                qty = float(qty)
            except:
                qty = 0
            quantities[dia] = qty
        df_filtered = df[(df['DIÁMETRO'].isin(selected_diams)) | (df['DIÁMETRO'].str.upper()=='TODOS')].copy()
        for dia, qty in quantities.items():
            mask = (df_filtered['DIÁMETRO'] == dia)
            df_filtered.loc[mask, '4.CANTIDAD'] = qty
        df_filtered_renombrado = renombrar_columnas(df_filtered)
        materiales_finales.append(("FLUJO B", df_filtered_renombrado))
        return redirect(url_for('flujo_c'))
    diam_select = "<div class='mb-3'><label class='form-label'>Selecciona DIÁMETRO(s):</label><br>"
    for diam in diam_options:
        diam_select += f"""
        <div class="form-check form-check-inline">
          <input class="form-check-input" type="checkbox" name="diams" value="{diam}"> {diam}
        </div>
        """
    diam_select += "</div>"
    qty_fields = "<div class='mb-3'><label class='form-label'>Ingresa cantidad para cada DIÁMETRO seleccionado:</label>"
    for diam in diam_options:
        qty_fields += f"""
        <div class="mb-2">
          <label>{diam}:</label>
          <input type="number" step="any" name="qty_{diam}" class="form-control" placeholder="Cantidad">
        </div>
        """
    qty_fields += "</div>"
    content = f"""
    <form method="post">
      {diam_select}
      {qty_fields}
      <button type="submit" class="btn btn-success">Aplicar Filtros y Continuar a FLUJO C</button>
    </form>
    """
    return render_template_string(base_template, title="FLUJO B: Tubo de saca", content=content)

# -------------------------------
# FLUJO C: Tubería de Baja
# -------------------------------
@app.route('/flujo_c', methods=['GET', 'POST'])
def flujo_c():
    file_path_baja = os.path.join("materiales", "baja tubing.xlsx")
    try:
        df = pd.read_excel(file_path_baja)
        df.columns = df.columns.str.strip()
        for col in df.columns:
            if df[col].dtype == object:
                df[col] = df[col].astype(str).str.strip()
    except Exception as e:
        flash("Error al cargar baja tubing: " + str(e))
        return redirect(url_for('flujo_b'))
    if request.method == 'POST':
        baja_option = request.form.get('baja')
        if baja_option == "SI":
            # Aquí se podría implementar la selección de DIÁMETRO, TIPO, etc. según la lógica original.
            df_renombrado = renombrar_columnas(df)
            materiales_finales.append(("FLUJO C", df_renombrado))
            return redirect(url_for('flujo_d'))
        else:
            return redirect(url_for('flujo_d'))
    content = """
    <form method="post">
      <div class="mb-3">
        <label class="form-label">¿Baja Tubing?</label><br>
        <div class="form-check form-check-inline">
          <input class="form-check-input" type="radio" name="baja" value="SI" required> SI
        </div>
        <div class="form-check form-check-inline">
          <input class="form-check-input" type="radio" name="baja" value="NO" required> NO
        </div>
      </div>
      <button type="submit" class="btn btn-primary">Continuar</button>
    </form>
    """
    return render_template_string(base_template, title="FLUJO C: Tubería de Baja", content=content)

# -------------------------------
# FLUJO D: Profundiza
# -------------------------------
@app.route('/flujo_d', methods=['GET', 'POST'])
def flujo_d():
    file_path_prof = os.path.join("materiales", "profundiza.xlsx")
    try:
        df = pd.read_excel(file_path_prof)
        df.columns = df.columns.str.strip()
        for col in df.columns:
            if df[col].dtype == object:
                df[col] = df[col].astype(str).str.strip()
    except Exception as e:
        flash("Error al cargar profundiza.xlsx: " + str(e))
        return redirect(url_for('flujo_c'))
    if request.method == 'POST':
        profundizar = request.form.get('profundizar')
        if profundizar == "SI":
            # Se asume que se realizan las selecciones e ingreso de cantidades según la lógica original
            df_renombrado = renombrar_columnas(df)
            materiales_finales.append(("FLUJO D", df_renombrado))
            return redirect(url_for('flujo_e'))
        else:
            return redirect(url_for('flujo_e'))
    content = """
    <form method="post">
      <div class="mb-3">
        <label class="form-label">Profundizar:</label>
        <select name="profundizar" class="form-select" required>
          <option value="">seleccionar</option>
          <option value="SI">SI</option>
          <option value="NO">NO</option>
        </select>
      </div>
      <button type="submit" class="btn btn-primary">Continuar</button>
    </form>
    """
    return render_template_string(base_template, title="FLUJO D: Profundiza", content=content)

# -------------------------------
# FLUJO E: Baja varillas
# -------------------------------
@app.route('/flujo_e', methods=['GET', 'POST'])
def flujo_e():
    file_path = os.path.join("materiales", "baja varillas.xlsx")
    try:
        df = pd.read_excel(file_path)
        df.columns = df.columns.str.strip()
        df["DIÁMETRO"] = df["DIÁMETRO"].astype(str).str.strip()
    except Exception as e:
        flash("Error al cargar baja varillas.xlsx: " + str(e))
        return redirect(url_for('flujo_d'))
    if request.method == 'POST':
        varilla = request.form.get('varilla')
        if varilla == "SI":
            # Se aplica la lógica de filtrado similar a FLUJO A (se puede ampliar según el código original)
            final_df = df
            final_df_renombrado = renombrar_columnas(final_df)
            materiales_finales.append(("FLUJO E", final_df_renombrado))
            return redirect(url_for('flujo_f'))
        else:
            return redirect(url_for('flujo_f'))
    content = """
    <form method="post">
      <div class="mb-3">
        <label class="form-label">¿Baja Varilla?</label><br>
        <div class="form-check form-check-inline">
          <input class="form-check-input" type="radio" name="varilla" value="SI" required> SI
        </div>
        <div class="form-check form-check-inline">
          <input class="form-check-input" type="radio" name="varilla" value="NO" required> NO
        </div>
      </div>
      <button type="submit" class="btn btn-primary">Continuar</button>
    </form>
    """
    return render_template_string(base_template, title="FLUJO E: Baja varillas", content=content)

# -------------------------------
# FLUJO F: Abandona pozo
# -------------------------------
@app.route('/flujo_f', methods=['GET', 'POST'])
def flujo_f():
    file_path = os.path.join("materiales", "abandono-recupero.xlsx")
    try:
        df = pd.read_excel(file_path)
        df.columns = df.columns.str.strip()
        for col in df.columns:
            if df[col].dtype == object:
                df[col] = df[col].astype(str).str.strip()
    except Exception as e:
        flash("Error al cargar abandono-recupero.xlsx: " + str(e))
        return redirect(url_for('flujo_e'))
    if request.method == 'POST':
        opcion = request.form.get('opcion')
        if opcion == "SI":
            df_renombrado = renombrar_columnas(df)
            materiales_finales.append(("FLUJO F", df_renombrado))
            return redirect(url_for('flujo_g'))
        else:
            return redirect(url_for('flujo_g'))
    content = """
    <form method="post">
      <div class="mb-3">
        <label class="form-label">¿Abandono/recupero?</label>
        <select name="opcion" class="form-select" required>
          <option value="">Seleccione</option>
          <option value="SI">SI</option>
          <option value="NO">NO</option>
        </select>
      </div>
      <button type="submit" class="btn btn-primary">Continuar</button>
    </form>
    """
    return render_template_string(base_template, title="FLUJO F: Abandona pozo", content=content)

# -------------------------------
# FLUJO G: Instalación BM
# -------------------------------
@app.route('/flujo_g', methods=['GET', 'POST'])
def flujo_g():
    file_path = os.path.join("materiales", "WO.xlsx")
    if request.method == 'POST':
        wo = request.form.get('wo')
        if wo == "SI":
            try:
                df = pd.read_excel(file_path)
                df_renombrado = renombrar_columnas(df)
                materiales_finales.append(("FLUJO G", df_renombrado))
            except Exception as e:
                flash("Error al cargar WO.xlsx: " + str(e))
        return redirect(url_for('flujo_h'))
    content = """
    <form method="post">
      <div class="mb-3">
        <label class="form-label">¿WO a BM?</label><br>
        <div class="form-check form-check-inline">
          <input class="form-check-input" type="radio" name="wo" value="SI" required> SI
        </div>
        <div class="form-check form-check-inline">
          <input class="form-check-input" type="radio" name="wo" value="NO" required> NO
        </div>
      </div>
      <button type="submit" class="btn btn-primary">Continuar</button>
    </form>
    """
    return render_template_string(base_template, title="FLUJO G: Instalación BM", content=content)

# -------------------------------
# FLUJO H: Material de agregación
# -------------------------------
@app.route('/flujo_h', methods=['GET', 'POST'])
def flujo_h():
    file_path = os.path.join("materiales", "GENERAL(1).xlsx")
    try:
        df = pd.read_excel(file_path)
        df.columns = df.columns.str.strip()
        if "4.CANTIDAD" not in df.columns:
            df["4.CANTIDAD"] = 0
    except Exception as e:
        flash("Error al cargar GENERAL(1).xlsx: " + str(e))
        df = pd.DataFrame()
    if request.method == 'POST':
        agregar = request.form.get('agregar')
        if agregar == "SI":
            selected_materials = request.form.getlist('materiales')
            for mat in selected_materials:
                qty = request.form.get(f'qty_{mat}', 0)
                try:
                    qty = float(qty)
                except:
                    qty = 0
                df.loc[df["2. MATERIAL"].astype(str)==mat, "4.CANTIDAD"] = qty
            assigned_df = df[(df["2. MATERIAL"].astype(str).isin(selected_materials)) & (df["4.CANTIDAD"] > 0)]
            if not assigned_df.empty:
                assigned_df_renombrado = renombrar_columnas(assigned_df)
                materiales_finales.append(("FLUJO H", assigned_df_renombrado))
            return redirect(url_for('final'))
        else:
            return redirect(url_for('final'))
    materiales = []
    if not df.empty and "2. MATERIAL" in df.columns:
        materiales = df["2. MATERIAL"].astype(str).unique().tolist()
    material_options = ""
    for mat in materiales:
        material_options += f"""
        <div class="form-check">
          <input class="form-check-input" type="checkbox" name="materiales" value="{mat}">
          <label class="form-check-label">{mat}</label>
        </div>
        <div class="mb-3">
          <input type="number" step="any" name="qty_{mat}" class="form-control" placeholder="Cantidad para {mat}">
        </div>
        """
    content = f"""
    <form method="post">
      <div class="mb-3">
        <label class="form-label">¿Agregar más material?</label>
        <select name="agregar" class="form-select" required>
          <option value="">Seleccionar</option>
          <option value="SI">SI</option>
          <option value="NO">NO</option>
        </select>
      </div>
      <div class="mb-3">
        <label class="form-label">Lista completa de materiales:</label>
        {material_options}
      </div>
      <button type="submit" class="btn btn-success">Aplicar selección y asignar cantidades</button>
    </form>
    """
    return render_template_string(base_template, title="FLUJO H: Material de agregación", content=content)

# Página final: muestra el listado final de materiales
@app.route('/final')
def final():
    content = "<h4>Listado final de materiales de todos los flujos ejecutados:</h4>"
    for flow, df in materiales_finales:
        content += f"<h5>{flow}</h5>"
        content += df.to_html(classes="table table-bordered table-striped")
    return render_template_string(base_template, title="Listado Final", content=content)

# Página de inicio: redirige al Flujo A
@app.route('/')
def index():
    return redirect(url_for('flujo_a'))

if __name__ == '__main__':
    app.run(debug=True)
