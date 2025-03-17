ffrom flask import Flask, render_template_string, request, redirect, url_for, session, flash
import os
import pandas as pd
from jinja2 import DictLoader

app = Flask(__name__)
app.secret_key = 'tu_clave_secreta'  # Cambia esta clave por una segura

# ==============================================================
# VARIABLE GLOBAL PARA ALMACENAR LOS DATAFRAMES FINALES DE CADA FLUJO
# (Misma lógica que: materiales_finales = [])
# ==============================================================

materiales_finales = []

# ==============================================================
# FUNCIÓN PARA RENOMBRAR COLUMNAS (SIN CAMBIAR LA LÓGICA ORIGINAL)
# ==============================================================

def renombrar_columnas(df):
    df_renombrado = df.rename(
        columns={
            "1. Cód.SAP": "Cód.SAP",
            "2. MATERIAL": "MATERIAL",
            "3. Descripción": "Descripción",
            "5.CONDICIÓN": "CONDICIÓN"
        }
    )
    # Se asegura que queden solo las columnas requeridas
    columnas = ["Cód.SAP", "MATERIAL", "Descripción", "4.CANTIDAD", "CONDICIÓN"]
    columnas_presentes = [col for col in columnas if col in df_renombrado.columns]
    return df_renombrado[columnas_presentes]

# ==============================================================
# PLANTILLA BASE: INTERFAZ MODERNA (AZUL Y GRIS)
# ==============================================================

base_template = """
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>{{ title }}</title>
  <style>
    body {
      font-family: Arial, sans-serif;
      background-color: #f0f4f8;
      color: #333;
      margin: 0;
      padding: 0;
    }
    header {
      background-color: #1e3d59;
      color: #fff;
      padding: 10px 0;
      text-align: center;
    }
    .container {
      width: 80%%;
      margin: auto;
      padding: 20px;
    }
    .btn {
      background-color: #1e3d59;
      border: none;
      color: white;
      padding: 10px 20px;
      text-align: center;
      margin: 4px 2px;
      cursor: pointer;
    }
    .btn-info { background-color: #4a90e2; }
    .btn-success { background-color: #28a745; }
    .btn-warning { background-color: #ffc107; color: black; }
    .form-group {
      margin-bottom: 15px;
    }
    label {
      display: block;
      margin-bottom: 5px;
    }
    select, input[type="text"], input[type="number"] {
      width: 100%%;
      padding: 8px;
      box-sizing: border-box;
    }
    table {
      width: 100%%;
      border-collapse: collapse;
      margin-top: 20px;
    }
    table, th, td { border: 1px solid #ccc; }
    th, td { padding: 10px; text-align: left; }
  </style>
</head>
<body>
  <header>
    <h1>{{ title }}</h1>
  </header>
  <div class="container">
    {% with messages = get_flashed_messages() %}
      {% if messages %}
        <ul>
          {% for message in messages %}
            <li>{{ message }}</li>
          {% endfor %}
        </ul>
      {% endif %}
    {% endwith %}
    {% block content %}{% endblock %}
  </div>
</body>
</html>
"""

app.jinja_loader = DictLoader({'base.html': base_template})

# VARIABLE GLOBAL PARA ALMACENAR LOS DATAFRAMES FINALES
# (Equivalente a: materiales_finales = [])
# =============================================================
materiales_finales = []

# =============================================================
# FUNCIÓN PARA RENOMBRAR COLUMNAS (SIN CAMBIAR LA LÓGICA ORIGINAL)
# =============================================================
def renombrar_columnas(df):
    df_renombrado = df.rename(
        columns={
            "1. Cód.SAP": "Cód.SAP",
            "2. MATERIAL": "MATERIAL",
            "3. Descripción": "Descripción",
            "5.CONDICIÓN": "CONDICIÓN"
        }
    )
    # Se asegura que queden solo las columnas requeridas
    columnas = ["Cód.SAP", "MATERIAL", "Descripción", "4.CANTIDAD", "CONDICIÓN"]
    columnas_presentes = [col for col in columnas if col in df_renombrado.columns]
    return df_renombrado[columnas_presentes]

# =============================================================
# PASO 1: PREGUNTA INICIAL – ¿Ajuste de medida? 
# (Equivalente a la parte inicial de flujo_A)
# =============================================================
@app.route('/flujo_b', methods=['GET', 'POST'])
def flujo_b():
    # Aquí se usa el nombre "flujo_b" para adecuarlo al requerimiento,
    # aunque el código original es de "Ajuste de medida"
    if request.method == 'POST':
        respuesta = request.form.get('ajuste')
        if respuesta == "SI":
            return redirect(url_for('flujo_b_select_diameters'))
        elif respuesta == "NO":
            # Aquí se redirige al siguiente flujo (por ejemplo, flujo C)
            return redirect(url_for('proximo_flujo'))
    template = """
    <html>
      <head>
        <title>Flujo B: Ajuste de medida</title>
      </head>
      <body>
         <h2>Flujo B: Ajuste de medida</h2>
         <form method="post">
             <label>¿Ajuste de medida?</label><br>
             <input type="radio" name="ajuste" value="SI" required> SI<br>
             <input type="radio" name="ajuste" value="NO" required> NO<br>
             <button type="submit">Continuar</button>
         </form>
      </body>
    </html>
    """
    return render_template_string(template)

# =============================================================
# PASO 2: SELECCIÓN DE DIÁMETRO
# Se carga el Excel y se extraen los DIÁMETRO (excluyendo "TODOS")
# =============================================================
@app.route('/flujo_b_select_diameters', methods=['GET', 'POST'])
def flujo_b_select_diameters():
    try:
        file_path = os.path.join("materiales", "ajuste de medida(2).xlsx")
        df = pd.read_excel(file_path)
        df.columns = df.columns.str.strip()
        df["DIÁMETRO"] = df["DIÁMETRO"].astype(str).str.strip()
    except Exception as e:
        flash("Error al cargar el archivo Excel: " + str(e))
        return redirect(url_for('flujo_b'))
    # Guardamos el DataFrame en sesión (convertido a JSON)
    session['flujo_b_df'] = df.to_json(orient='split')
    # Extraemos la lista de DIÁMETRO, excluyendo "TODOS"
    all_diams = sorted([x for x in df["DIÁMETRO"].dropna().unique() if x.upper() != "TODOS"])
    template = """
    <html>
      <head>
        <title>Flujo B: Selección de DIÁMETRO</title>
      </head>
      <body>
         <h2>Flujo B: Selección de DIÁMETRO</h2>
         <form method="post">
             <label>Seleccione DIÁMETRO(s):</label><br>
             <select name="selected_diam" multiple size="10" required>
             {% for diam in diametros %}
                <option value="{{ diam }}">{{ diam }}</option>
             {% endfor %}
             </select><br>
             <button type="submit">Siguiente</button>
         </form>
      </body>
    </html>
    """
    return render_template_string(template, diametros=all_diams)

# =============================================================
# PASO 3: GENERACIÓN DE FILTROS DINÁMICOS
# Por cada DIÁMETRO seleccionado se muestran:
#   - Un multi-select para TIPO.
#   - Un dropdown para GRADO DE ACERO.
#   - Un dropdown para GRADO DE ACERO CUPLA.
#   - Un dropdown para TIPO DE CUPLA.
# =============================================================
@app.route('/flujo_b_dynamic_filters', methods=['GET', 'POST'])
def flujo_b_dynamic_filters():
    if request.method == 'POST':
        # Se recogen las selecciones de filtros para cada DIÁMETRO
        filtros = {}
        selected_diams = request.form.getlist('selected_diam')
        for diam in selected_diams:
            # Para cada DIÁMETRO se recogen los valores
            tipo_list = request.form.getlist('tipo_' + diam)
            # Si no se selecciona nada, se asigna ["TODOS"]
            if not tipo_list:
                tipo_list = ["TODOS"]
            else:
                tipo_list.append("TODOS")
            acero = request.form.get('acero_' + diam)
            acero_list = ["TODOS"] if (acero == "Seleccionar" or not acero) else [acero, "TODOS"]
            acero_cup = request.form.get('acero_cup_' + diam)
            acero_cup_list = ["TODOS"] if (acero_cup == "Seleccionar" or not acero_cup) else [acero_cup, "TODOS"]
            tipo_cup = request.form.get('tipo_cup_' + diam)
            tipo_cup_list = ["TODOS"] if (tipo_cup == "Seleccionar" or not tipo_cup) else [tipo_cup, "TODOS"]
            filtros[diam] = {
                "tipo_list": tipo_list,
                "acero_list": acero_list,
                "acero_cup_list": acero_cup_list,
                "tipo_cup_list": tipo_cup_list
            }
        session['flujo_b_filters'] = filtros
        return redirect(url_for('flujo_b_apply_filters'))
    else:
        # En GET se espera recibir los DIÁMETRO seleccionados en la anterior ruta
        selected_diams = request.args.getlist('selected_diam')
        if not selected_diams:
            # Si no se han pasado, se recuperan de la sesión (si ya se guardaron)
            selected_diams = session.get('selected_diam', [])
        # Guardamos la selección para usarla en el POST (si no lo hicimos aún)
        session['selected_diam'] = selected_diams

        # Recuperamos el DataFrame de la sesión
        df_json = session.get('flujo_b_df')
        if not df_json:
            flash("Datos no encontrados. Reinicie el proceso.")
            return redirect(url_for('flujo_b'))
        df = pd.read_json(df_json, orient='split')
        # Para cada DIÁMETRO seleccionado, se generan las opciones dinámicas
        filtros_dinamicos = {}
        for diam in selected_diams:
            subset = df[df["DIÁMETRO"] == diam]
            # Opciones para TIPO (excluyendo "TODOS")
            tipos = sorted([x for x in subset["TIPO"].dropna().unique() if x.upper() != "TODOS"])
            # Opciones para GRADO DE ACERO
            acero_opts = sorted([x for x in subset["GRADO DE ACERO"].dropna().unique() if str(x).upper() != "TODOS"])
            # Opciones para GRADO DE ACERO CUPLA
            acero_cup_opts = sorted([x for x in subset["GRADO DE ACERO CUPLA"].dropna().unique() if str(x).upper() != "TODOS"])
            # Opciones para TIPO DE CUPLA
            tipo_cup_opts = sorted([x for x in subset["TIPO DE CUPLA"].dropna().unique() if str(x).upper() != "TODOS"])
            filtros_dinamicos[diam] = {
                "tipos": tipos,
                "acero_opts": ["Seleccionar"] + acero_opts,
                "acero_cup_opts": ["Seleccionar"] + acero_cup_opts,
                "tipo_cup_opts": ["Seleccionar"] + tipo_cup_opts
            }
        template = """
        <html>
          <head>
            <title>Flujo B: Filtros Dinámicos</title>
          </head>
          <body>
            <h2>Flujo B: Filtros Dinámicos</h2>
            <form method="post">
              {% for diam, opts in filtros_dinamicos.items() %}
                <fieldset>
                  <legend>DIÁMETRO: {{ diam }}</legend>
                  <label>TIPO (seleccione uno o varios):</label><br>
                  <select name="tipo_{{ diam }}" multiple size="5">
                    {% for t in opts.tipos %}
                      <option value="{{ t }}">{{ t }}</option>
                    {% endfor %}
                  </select><br>
                  <label>GRADO ACERO:</label>
                  <select name="acero_{{ diam }}">
                    {% for opt in opts.acero_opts %}
                      <option value="{{ opt }}">{{ opt }}</option>
                    {% endfor %}
                  </select><br>
                  <label>ACERO CUPLA:</label>
                  <select name="acero_cup_{{ diam }}">
                    {% for opt in opts.acero_cup_opts %}
                      <option value="{{ opt }}">{{ opt }}</option>
                    {% endfor %}
                  </select><br>
                  <label>TIPO CUPLA:</label>
                  <select name="tipo_cup_{{ diam }}">
                    {% for opt in opts.tipo_cup_opts %}
                      <option value="{{ opt }}">{{ opt }}</option>
                    {% endfor %}
                  </select><br>
                </fieldset>
                <br>
              {% endfor %}
              {% for diam in selected_diams %}
                <input type="hidden" name="selected_diam" value="{{ diam }}">
              {% endfor %}
              <button type="submit">Aplicar Filtros</button>
            </form>
          </body>
        </html>
        """
        return render_template_string(template, filtros_dinamicos=filtros_dinamicos, selected_diams=selected_diams)

# =============================================================
# PASO 4: PROCESAR FILTROS Y APLICAR LA LÓGICA DE FILTRADO
# Se genera el DataFrame final, se renombran las columnas y se almacena
# =============================================================
@app.route('/flujo_b_apply_filters', methods=['GET'])
def flujo_b_apply_filters():
    filtros = session.get('flujo_b_filters')
    df_json = session.get('flujo_b_df')
    if not filtros or not df_json:
        flash("Datos o filtros no encontrados.")
        return redirect(url_for('flujo_b'))
    df = pd.read_json(df_json, orient='split')
    # Se crea la condición final combinando los filtros para cada DIÁMETRO
    final_condition = pd.Series([False] * len(df))
    for diam_value, fdict in filtros.items():
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
    materiales_finales.append(("Flujo B", final_df_renombrado))
    template = """
    <html>
      <head>
        <title>Flujo B: Filtros Aplicados</title>
      </head>
      <body>
         <h2>Filtros Aplicados</h2>
         <p>Los materiales del flujo B han sido guardados.</p>
         <!-- En el código original se muestra un botón para continuar a FLUJO H -->
         <a href="{{ url_for('proximo_flujo') }}">Continuar a Flujo H</a>
      </body>
    </html>
    """
    return render_template_string(template)

# =============================================================
# Ruta de ejemplo para el siguiente flujo (Flujo H o similar)
# =============================================================
@app.route('/proximo_flujo')
def proximo_flujo():
    template = """
    <html>
      <head>
        <title>Siguiente Flujo</title>
      </head>
      <body>
         <h2>Continuación del Proceso</h2>
         <p>Aquí se continuaría con el siguiente flujo (por ejemplo, Flujo H).</p>
      </body>
    </html>
    """
    return render_template_string(template)

if __name__ == '__main__':
    app.run(debug=True)
# ==============================================================
# FLUJO B: TUBO DE SACA
# (Equivalente a la función flujo_B del código original)
# ==============================================================

@app.route('/flujo_b', methods=['GET', 'POST'])
def flujo_b():
    if request.method == 'POST':
        saca_tubing = request.form.get('saca_tubing')
        if saca_tubing == "SI":
            return redirect(url_for('flujo_b_select'))
        elif saca_tubing == "NO":
            flash("No se saca tubing.")
            return redirect(url_for('flujo_c'))
    flujo_b_template = """
    {% extends "base.html" %}
    {% block content %}
    <h2>FLUJO B: Tubo de saca</h2>
    <form method="post">
      <div class="form-group">
        <label>¿Saca Tubing?</label>
        <input type="radio" name="saca_tubing" value="SI" required> SI
        <input type="radio" name="saca_tubing" value="NO" required> NO
      </div>
      <button type="submit" class="btn btn-info">Continuar</button>
    </form>
    {% endblock %}
    """
    return render_template_string(flujo_b_template, title="FLUJO B: Tubo de saca")

# Aquí se carga el Excel de “saca tubing” y se solicita la selección de DIÁMETRO
@app.route('/flujo_b_select', methods=['GET', 'POST'])
def flujo_b_select():
    try:
        folder_path = "materiales"  # La carpeta donde se encuentra el Excel
        filename_saca = "saca_tubing.xlsx"
        file_path_saca = os.path.join(folder_path, filename_saca)
        if not os.path.exists(file_path_saca):
            flash("El archivo de saca tubing no se encontró.")
            return redirect(url_for('flujo_b'))
        df = pd.read_excel(file_path_saca)
        df.columns = df.columns.str.strip()
        for c in df.columns:
            if df[c].dtype == object:
                df[c] = df[c].astype(str).str.strip()
    except Exception as e:
        flash("Error al cargar el Excel: " + str(e))
        return redirect(url_for('flujo_b'))
    diametros = sorted([d for d in df['DIÁMETRO'].unique() if d.upper() != 'TODOS'])
    session['flujo_b_df'] = df.to_json(orient='split')
    flujo_b_select_template = """
    {% extends "base.html" %}
    {% block content %}
    <h2>FLUJO B: Selección Tubing</h2>
    <form method="post" action="{{ url_for('flujo_b_apply') }}">
      <div class="form-group">
        <label>Seleccione DIÁMETRO(s):</label>
        <select name="diametros" multiple required>
          {% for diam in diametros %}
            <option value="{{ diam }}">{{ diam }}</option>
          {% endfor %}
        </select>
      </div>
      <!-- Aquí se solicitarían las cantidades para cada DIÁMETRO, de forma similar a la función on_confirm_diameter_button_clicked -->
      <button type="submit" class="btn btn-success">Aplicar Filtros</button>
    </form>
    {% endblock %}
    """
    return render_template_string(flujo_b_select_template, diametros=diametros, title="FLUJO B: Selección Tubing")

@app.route('/flujo_b_apply', methods=['POST'])
def flujo_b_apply():
    df_json = session.get('flujo_b_df')
    if not df_json:
        flash("Error: datos no encontrados para flujo B.")
        return redirect(url_for('flujo_b'))
    df = pd.read_json(df_json, orient='split')
    selected_diam = request.form.getlist('diametros')
    df_filtered = df[df['DIÁMETRO'].isin(selected_diam) | (df['DIÁMETRO'].str.upper() == 'TODOS')]
    final_df_renombrado = renombrar_columnas(df_filtered)
    materiales_finales.append(("FLUJO B", final_df_renombrado))
    flash("Materiales del FLUJO B guardados.")
    return redirect(url_for('flujo_c'))

# ==============================================================
# FLUJO C: TUBERÍA DE BAJA
# (Equivalente a la función flujo_C del código original)
# ==============================================================

@app.route('/flujo_c', methods=['GET', 'POST'])
def flujo_c():
    if request.method == 'POST':
        baja_tubing = request.form.get('baja_tubing')
        if baja_tubing == "SI":
            return redirect(url_for('flujo_c_select'))
        else:
            flash("No se procede con Baja Tubing.")
            return redirect(url_for('flujo_d'))
    flujo_c_template = """
    {% extends "base.html" %}
    {% block content %}
    <h2>FLUJO C: Tubería de Baja</h2>
    <form method="post">
      <div class="form-group">
        <label>¿Baja Tubing?</label>
        <input type="radio" name="baja_tubing" value="SI" required> SI
        <input type="radio" name="baja_tubing" value="NO" required> NO
      </div>
      <button type="submit" class="btn btn-info">Continuar</button>
    </form>
    {% endblock %}
    """
    return render_template_string(flujo_c_template, title="FLUJO C: Tubería de Baja")

# Se carga el Excel para baja tubing y se solicita la selección de DIÁMETRO
@app.route('/flujo_c_select', methods=['GET', 'POST'])
def flujo_c_select():
    try:
        file_path_baja = os.path.join("materiales", "baja_tubing.xlsx")
        if not os.path.exists(file_path_baja):
            flash("Archivo baja tubing no encontrado.")
            return redirect(url_for('flujo_c'))
        df = pd.read_excel(file_path_baja)
        df.columns = df.columns.str.strip()
        for col in df.columns:
            if df[col].dtype == object:
                df[col] = df[col].astype(str).str.strip()
    except Exception as e:
        flash("Error al cargar el Excel: " + str(e))
        return redirect(url_for('flujo_c'))
    diametros = sorted([x for x in df['DIÁMETRO'].unique() if x != "TODOS"])
    session['flujo_c_df'] = df.to_json(orient='split')
    flujo_c_select_template = """
    {% extends "base.html" %}
    {% block content %}
    <h2>FLUJO C: Selección Baja Tubing</h2>
    <form method="post" action="{{ url_for('flujo_c_apply') }}">
      <div class="form-group">
        <label>Seleccione DIÁMETRO(s):</label>
        <select name="diametros" multiple required>
          {% for diam in diametros %}
            <option value="{{ diam }}">{{ diam }}</option>
          {% endfor %}
        </select>
      </div>
      <button type="submit" class="btn btn-success">Aplicar Selección</button>
    </form>
    {% endblock %}
    """
    return render_template_string(flujo_c_select_template, diametros=diametros, title="FLUJO C: Selección Baja Tubing")

@app.route('/flujo_c_apply', methods=['POST'])
def flujo_c_apply():
    df_json = session.get('flujo_c_df')
    if not df_json:
        flash("Error: datos no encontrados para flujo C.")
        return redirect(url_for('flujo_c'))
    df = pd.read_json(df_json, orient='split')
    selected_diam = request.form.getlist('diametros')
    if not selected_diam:
        selected_diam = ["TODOS"]
    df_filtered = df[df['DIÁMETRO'].isin(selected_diam)]
    final_df_renombrado = renombrar_columnas(df_filtered)
    materiales_finales.append(("FLUJO C", final_df_renombrado))
    flash("Materiales del FLUJO C guardados.")
    return redirect(url_for('flujo_d'))

# ==============================================================
# FLUJO D: PROFUNDIZA
# (Equivalente a la función flujo_D del código original)
# ==============================================================

@app.route('/flujo_d', methods=['GET', 'POST'])
def flujo_d():
    if request.method == 'POST':
        profundizar = request.form.get('profundizar')
        if profundizar == "SI":
            return redirect(url_for('flujo_d_select'))
        else:
            flash("No se profundizará en la información.")
            return redirect(url_for('flujo_e'))
    flujo_d_template = """
    {% extends "base.html" %}
    {% block content %}
    <h2>FLUJO D: Profundiza</h2>
    <form method="post">
      <div class="form-group">
        <label>Profundizar:</label>
        <input type="radio" name="profundizar" value="SI" required> SI
        <input type="radio" name="profundizar" value="NO" required> NO
      </div>
      <button type="submit" class="btn btn-info">Continuar</button>
    </form>
    {% endblock %}
    """
    return render_template_string(flujo_d_template, title="FLUJO D: Profundiza")

# Ruta para seleccionar DIÁMETRO y cantidad en el Excel “profundiza”
@app.route('/flujo_d_select', methods=['GET', 'POST'])
def flujo_d_select():
    try:
        file_path_prof = os.path.join("materiales", "profundiza.xlsx")
        if not os.path.exists(file_path_prof):
            flash("Archivo profundiza no encontrado.")
            return redirect(url_for('flujo_d'))
        df = pd.read_excel(file_path_prof)
        df.columns = df.columns.str.strip()
        for col in df.columns:
            if df[col].dtype == object:
                df[col] = df[col].astype(str).str.strip()
    except Exception as e:
        flash("Error al cargar el Excel: " + str(e))
        return redirect(url_for('flujo_d'))
    # Se asume que la columna “DIÁMETRO” existe
    diametros = df["DIÁMETRO"].unique().tolist() if "DIÁMETRO" in df.columns else []
    session['flujo_d_df'] = df.to_json(orient='split')
    flujo_d_select_template = """
    {% extends "base.html" %}
    {% block content %}
    <h2>FLUJO D: Profundiza - Selección</h2>
    <form method="post" action="{{ url_for('flujo_d_apply') }}">
      <div class="form-group">
        <label>Seleccione DIÁMETRO(s):</label>
        <select name="diametros" multiple required>
          {% for diam in diametros %}
            <option value="{{ diam }}">{{ diam }}</option>
          {% endfor %}
        </select>
      </div>
      <div class="form-group">
        <label>Ingrese cantidad (se aplicará a todos los seleccionados):</label>
        <input type="number" name="cantidad" step="any" required>
      </div>
      <button type="submit" class="btn btn-success">Aplicar</button>
    </form>
    {% endblock %}
    """
    return render_template_string(flujo_d_select_template, diametros=diametros, title="FLUJO D: Profundiza - Selección")

@app.route('/flujo_d_apply', methods=['POST'])
def flujo_d_apply():
    df_json = session.get('flujo_d_df')
    if not df_json:
        flash("Error: datos no encontrados para flujo D.")
        return redirect(url_for('flujo_d'))
    df = pd.read_json(df_json, orient='split')
    selected_diam = request.form.getlist('diametros')
    cantidad = request.form.get('cantidad', type=float)
    if not selected_diam:
        flash("No se seleccionaron diámetros.")
        return redirect(url_for('flujo_d'))
    df_filtered = df[df["DIÁMETRO"].isin(selected_diam)]
    df_filtered["4.CANTIDAD"] = cantidad
    final_df_renombrado = renombrar_columnas(df_filtered)
    materiales_finales.append(("FLUJO D", final_df_renombrado))
    flash("Materiales del FLUJO D guardados.")
    return redirect(url_for('flujo_e'))

# ==============================================================
# FLUJO E: BAJA VARILLAS
# (Equivalente a la función flujo_E del código original)
# ==============================================================

@app.route('/flujo_e', methods=['GET', 'POST'])
def flujo_e():
    if request.method == 'POST':
        baja_varilla = request.form.get('baja_varilla')
        if baja_varilla == "SI":
            return redirect(url_for('flujo_e_filters'))
        else:
            return redirect(url_for('flujo_f'))
    flujo_e_template = """
    {% extends "base.html" %}
    {% block content %}
    <h2>FLUJO E: Baja varillas</h2>
    <form method="post">
      <div class="form-group">
        <label>¿Baja Varilla?</label>
        <input type="radio" name="baja_varilla" value="SI" required> SI
        <input type="radio" name="baja_varilla" value="NO" required> NO
      </div>
      <button type="submit" class="btn btn-info">Continuar</button>
    </form>
    {% endblock %}
    """
    return render_template_string(flujo_e_template, title="FLUJO E: Baja varillas")

# Se carga el Excel “baja varillas” y se solicitan los filtros (similar a flujo_A_filters)
@app.route('/flujo_e_filters', methods=['GET', 'POST'])
def flujo_e_filters():
    try:
        file_path = os.path.join("materiales", "baja_varillas.xlsx")
        df = pd.read_excel(file_path)
        df.columns = df.columns.str.strip()
        df["DIÁMETRO"] = df["DIÁMETRO"].astype(str).str.strip()
    except Exception as e:
        flash("Error al cargar Excel: " + str(e))
        return redirect(url_for('flujo_e'))
    diametros = sorted([x for x in df["DIÁMETRO"].dropna().unique() if x.upper() != "TODOS"])
    session['flujo_e_df'] = df.to_json(orient='split')
    flujo_e_filters_template = """
    {% extends "base.html" %}
    {% block content %}
    <h2>FLUJO E: Filtros - Baja varillas</h2>
    <form method="post" action="{{ url_for('flujo_e_apply') }}">
      <div class="form-group">
        <label>Seleccione DIÁMETRO(s):</label>
        <select name="diametros" multiple required>
          {% for diam in diametros %}
            <option value="{{ diam }}">{{ diam }}</option>
          {% endfor %}
        </select>
      </div>
      <!-- Aquí se pueden agregar más filtros (TIPO, GRADO ACERO, etc.) de acuerdo a la lógica original -->
      <button type="submit" class="btn btn-success">Aplicar Filtros</button>
    </form>
    {% endblock %}
    """
    return render_template_string(flujo_e_filters_template, diametros=diametros, title="FLUJO E: Filtros")

@app.route('/flujo_e_apply', methods=['POST'])
def flujo_e_apply():
    df_json = session.get('flujo_e_df')
    if not df_json:
        flash("Error: datos no encontrados para flujo E.")
        return redirect(url_for('flujo_e'))
    df = pd.read_json(df_json, orient='split')
    selected_diam = request.form.getlist('diametros')
    if not selected_diam:
        selected_diam = ["TODOS"]
    df_filtered = df[df["DIÁMETRO"].isin(selected_diam)]
    final_df_renombrado = renombrar_columnas(df_filtered)
    materiales_finales.append(("FLUJO E", final_df_renombrado))
    flash("Materiales del FLUJO E guardados.")
    return redirect(url_for('flujo_g'))

# ==============================================================
# FLUJO F: ABANDONA POZO
# (Equivalente a la función flujo_F del código original)
# ==============================================================

@app.route('/flujo_f', methods=['GET', 'POST'])
def flujo_f():
    if request.method == 'POST':
        abandono = request.form.get('abandono')
        if abandono == "SI":
            return redirect(url_for('flujo_f_filters'))
        else:
            return redirect(url_for('flujo_h'))
    flujo_f_template = """
    {% extends "base.html" %}
    {% block content %}
    <h2>FLUJO F: Abandona pozo</h2>
    <form method="post">
      <div class="form-group">
        <label>¿Abandono/recupero?</label>
        <input type="radio" name="abandono" value="SI" required> SI
        <input type="radio" name="abandono" value="NO" required> NO
      </div>
      <button type="submit" class="btn btn-info">Continuar</button>
    </form>
    {% endblock %}
    """
    return render_template_string(flujo_f_template, title="FLUJO F: Abandona pozo")

# Se carga el Excel “abandono-recupero” y se solicitan filtros y cantidades
@app.route('/flujo_f_filters', methods=['GET', 'POST'])
def flujo_f_filters():
    try:
        file_path = os.path.join("materiales", "abandono-recupero.xlsx")
        df = pd.read_excel(file_path)
        df.columns = df.columns.str.strip()
        for col in df.columns:
            if df[col].dtype == object:
                df[col] = df[col].astype(str).strip()
    except Exception as e:
        flash("Error al cargar Excel: " + str(e))
        return redirect(url_for('flujo_f'))
    # Se obtienen los valores únicos para DIÁMETRO y DIÁMETRO CSG
    diametros = df["DIÁMETRO"].dropna().unique().tolist()
    if "TODOS" not in diametros: diametros.insert(0, "TODOS")
    diametros_csg = df["DIÁMETRO CSG"].dropna().unique().tolist()
    if "TODOS" not in diametros_csg: diametros_csg.insert(0, "TODOS")
    session['flujo_f_df'] = df.to_json(orient='split')
    flujo_f_filters_template = """
    {% extends "base.html" %}
    {% block content %}
    <h2>FLUJO F: Filtros - Abandono pozo</h2>
    <form method="post" action="{{ url_for('flujo_f_apply') }}">
      <div class="form-group">
        <label>Seleccione DIÁMETRO(s):</label>
        <select name="diametros" multiple required>
          {% for diam in diametros %}
            <option value="{{ diam }}">{{ diam }}</option>
          {% endfor %}
        </select>
      </div>
      <div class="form-group">
        <label>Seleccione DIÁMETRO CSG:</label>
        <select name="diametro_csg" required>
          {% for csg in diametros_csg %}
            <option value="{{ csg }}">{{ csg }}</option>
          {% endfor %}
        </select>
      </div>
      <!-- Aquí se solicitarían las cantidades para cada DIÁMETRO específico (cuando no sea "TODOS") -->
      <button type="submit" class="btn btn-success">Aplicar Filtros y Cantidades</button>
    </form>
    {% endblock %}
    """
    return render_template_string(flujo_f_filters_template, diametros=diametros, diametros_csg=diametros_csg, title="FLUJO F: Filtros")

@app.route('/flujo_f_apply', methods=['POST'])
def flujo_f_apply():
    df_json = session.get('flujo_f_df')
    if not df_json:
        flash("Error: datos no encontrados para flujo F.")
        return redirect(url_for('flujo_f'))
    df = pd.read_json(df_json, orient='split')
    selected_diam = request.form.getlist('diametros')
    diametro_csg = request.form.get('diametro_csg')
    df_filtered = df.copy()
    df_filtered = df_filtered[df_filtered["DIÁMETRO"].isin(selected_diam)]
    df_filtered = df_filtered[df_filtered["DIÁMETRO CSG"] == diametro_csg]
    final_df_renombrado = renombrar_columnas(df_filtered)
    materiales_finales.append(("FLUJO F", final_df_renombrado))
    flash("Materiales del FLUJO F guardados.")
    return redirect(url_for('flujo_h'))

# ==============================================================
# FLUJO G: INSTALACIÓN BM
# (Equivalente a la función flujo_G del código original)
# ==============================================================

@app.route('/flujo_g', methods=['GET', 'POST'])
def flujo_g():
    if request.method == 'POST':
        wo_bm = request.form.get('wo_bm')
        if wo_bm == "SI":
            try:
                file_path = os.path.join("materiales", "WO.xlsx")
                df = pd.read_excel(file_path)
                df_renombrado = renombrar_columnas(df)
                materiales_finales.append(("FLUJO G", df_renombrado))
                flash("Materiales del FLUJO G guardados.")
            except Exception as e:
                flash("Error al cargar Excel: " + str(e))
        else:
            flash("No se mostrarán los materiales en FLUJO G.")
        return redirect(url_for('flujo_h'))
    flujo_g_template = """
    {% extends "base.html" %}
    {% block content %}
    <h2>FLUJO G: Instalación BM</h2>
    <form method="post">
      <div class="form-group">
        <label>¿WO a BM?</label>
        <input type="radio" name="wo_bm" value="SI" required> SI
        <input type="radio" name="wo_bm" value="NO" required> NO
      </div>
      <button type="submit" class="btn btn-info">Continuar</button>
    </form>
    {% endblock %}
    """
    return render_template_string(flujo_g_template, title="FLUJO G: Instalación BM")

# ==============================================================
# FLUJO H: MATERIAL DE AGREGACIÓN
# (Equivalente a la función flujo_H del código original)
# ==============================================================

@app.route('/flujo_h', methods=['GET', 'POST'])
def flujo_h():
    try:
        file_path_H = os.path.join("materiales", "GENERAL.xlsx")
        df_H = pd.read_excel(file_path_H)
        df_H.columns = df_H.columns.str.strip()
        if "4.CANTIDAD" not in df_H.columns:
            df_H["4.CANTIDAD"] = 0
    except Exception as e:
        flash("Error al cargar GENERAL.xlsx: " + str(e))
        df_H = pd.DataFrame()
    # Extraer lista de materiales
    materiales = df_H["2. MATERIAL"].astype(str).unique().tolist() if not df_H.empty and "2. MATERIAL" in df_H.columns else []
    flujo_h_template = """
    {% extends "base.html" %}
    {% block content %}
    <h2>FLUJO H: Material de agregación</h2>
    <form method="post" action="{{ url_for('flujo_h_apply') }}">
      <div class="form-group">
        <label>¿Agregar más material?</label>
        <input type="radio" name="agregar" value="SI" required> SI
        <input type="radio" name="agregar" value="NO" required> NO
      </div>
      <button type="submit" class="btn btn-info">Continuar</button>
    </form>
    <br>
    <h3>Lista completa de materiales (Excel GENERAL):</h3>
    {{ table|safe }}
    <br>
    <form method="post" action="{{ url_for('flujo_h_select') }}">
      <div class="form-group">
        <label>Seleccione Materiales:</label>
        <select name="materiales" multiple required>
          {% for mat in materiales %}
            <option value="{{ mat }}">{{ mat }}</option>
          {% endfor %}
        </select>
      </div>
      <button type="submit" class="btn btn-success">Aplicar Selección</button>
    </form>
    {% endblock %}
    """
    return render_template_string(flujo_h_template, materiales=materiales, table=df_H.to_html(classes="table") if not df_H.empty else "", title="FLUJO H: Material de agregación")

# Ruta para seleccionar materiales y luego asignar cantidades
@app.route('/flujo_h_select', methods=['POST'])
def flujo_h_select():
    selected_materiales = request.form.getlist('materiales')
    if not selected_materiales:
        flash("No se seleccionó ningún material.")
        return redirect(url_for('flujo_h'))
    session['flujo_h_materiales'] = selected_materiales
    flujo_h_select_template = """
    {% extends "base.html" %}
    {% block content %}
    <h2>FLUJO H: Asignar Cantidades</h2>
    <form method="post" action="{{ url_for('flujo_h_apply') }}">
      {% for mat in materiales %}
      <div class="form-group">
        <label>Cantidad para {{ mat }}:</label>
        <input type="number" name="qty_{{ mat }}" step="any" required>
      </div>
      {% endfor %}
      <button type="submit" class="btn btn-success">Aplicar Cantidades</button>
    </form>
    {% endblock %}
    """
    return render_template_string(flujo_h_select_template, materiales=selected_materiales, title="FLUJO H: Asignar Cantidades")

@app.route('/flujo_h_apply', methods=['POST'])
def flujo_h_apply():
    try:
        file_path_H = os.path.join("materiales", "GENERAL.xlsx")
        df_H = pd.read_excel(file_path_H)
        df_H.columns = df_H.columns.str.strip()
        if "4.CANTIDAD" not in df_H.columns:
            df_H["4.CANTIDAD"] = 0
    except Exception as e:
        flash("Error al cargar GENERAL.xlsx: " + str(e))
        return redirect(url_for('flujo_h'))
    selected_materiales = session.get('flujo_h_materiales', [])
    for mat in selected_materiales:
        qty = request.form.get(f"qty_{mat}", type=float)
        df_H.loc[df_H["2. MATERIAL"].astype(str) == mat, "4.CANTIDAD"] = qty
    assigned_df = df_H[(df_H["2. MATERIAL"].astype(str).isin(selected_materiales)) & (df_H["4.CANTIDAD"] > 0)]
    if not assigned_df.empty:
        assigned_df_renombrado = renombrar_columnas(assigned_df)
        materiales_finales.append(("FLUJO H", assigned_df_renombrado))
        flash("Materiales del FLUJO H guardados.")
    else:
        flash("No se asignaron cantidades (o todas fueron 0).")
    return redirect(url_for('final_list'))

# ==============================================================
# LISTADO FINAL DE MATERIALES
# ==============================================================

@app.route('/final_list')
def final_list():
    final_html = "<h2>Listado final de materiales de todos los flujos ejecutados:</h2>"
    for flow, df in materiales_finales:
        final_html += f"<h3>{flow}</h3>"
        final_html += df.to_html(classes='table')
    final_list_template = """
    {% extends "base.html" %}
    {% block content %}
    {{ final_html|safe }}
    {% endblock %}
    """
    return render_template_string(final_list_template, final_html=final_html, title="Listado Final")

# ==============================================================
# PÁGINA PRINCIPAL: INICIA EN FLUJO A
# ==============================================================

@app.route('/')
def index():
    return redirect(url_for('flujo_a'))

if __name__ == '__main__':
    app.run(debug=True)

