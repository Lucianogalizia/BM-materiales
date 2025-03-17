from flask import Flask, render_template_string, request, redirect, url_for, session, flash
import os
import pandas as pd
from jinja2 import DictLoader

app = Flask(__name__)
app.secret_key = 'LUCIANO123'  # Cambia esta clave por una segura

# Global para almacenar los DataFrames finales de cada flujo
materiales_finales = []

# Función para renombrar las columnas (sin modificar la lógica original)
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

# Plantilla base con estilos azul y gris
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
        .container {
            width: 80%%;
            margin: auto;
            padding: 20px;
        }
        header {
            background-color: #1e3d59;
            color: #fff;
            padding: 10px 0;
            text-align: center;
        }
        .btn {
            background-color: #1e3d59;
            border: none;
            color: white;
            padding: 10px 20px;
            text-align: center;
            text-decoration: none;
            margin: 4px 2px;
            cursor: pointer;
        }
        .btn-info {
            background-color: #4a90e2;
        }
        .btn-success {
            background-color: #28a745;
        }
        .btn-warning {
            background-color: #ffc107;
            color: black;
        }
        .form-group {
            margin-bottom: 15px;
        }
        label {
            display: block;
            margin-bottom: 5px;
        }
        input[type="radio"],
        input[type="checkbox"] {
            margin-right: 5px;
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
        table, th, td {
            border: 1px solid #ccc;
        }
        th, td {
            padding: 10px;
            text-align: left;
        }
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

# Indicamos a Flask que la plantilla "base.html" se cargue desde nuestro string.
app.jinja_loader = DictLoader({'base.html': base_template})

# ------------------------------------------
# FLUJO A: Ajuste de medida
# ------------------------------------------
@app.route('/flujo_a', methods=['GET', 'POST'])
def flujo_a():
    if request.method == 'POST':
        ajuste = request.form.get('ajuste')
        if ajuste == "SI":
            # Cargar Excel de ajuste de medida
            try:
                file_path = os.path.join("Materiales", "ajuste_de_medida(2).xlsx")  # Ajusta la ruta
                df = pd.read_excel(file_path)
                df.columns = df.columns.str.strip()
                df["DIÁMETRO"] = df["DIÁMETRO"].astype(str).str.strip()
            except Exception as e:
                flash("Error al cargar el archivo Excel: " + str(e))
                return redirect(url_for('flujo_a'))
            # Obtener los DIÁMETRO únicos (excluyendo "TODOS")
            diametros = sorted([x for x in df["DIÁMETRO"].dropna().unique() if x.upper() != "TODOS"])
            # Guardar df en sesión (convertido a JSON) para continuar con los filtros
            session['flujo_a_df'] = df.to_json(orient='split')
            return render_template_string(flujo_a_filters_template, diametros=diametros, title="FLUJO A: Filtros")
        elif ajuste == "NO":
            return redirect(url_for('flujo_b'))
    return render_template_string(flujo_a_template, title="FLUJO A: Ajuste de medida")

flujo_a_template = """
{% extends "base.html" %}
{% block content %}
<h2>FLUJO A: Ajuste de medida</h2>
<form method="post">
    <div class="form-group">
        <label>¿Ajuste de medida?</label>
        <input type="radio" name="ajuste" value="SI" required> SI
        <input type="radio" name="ajuste" value="NO" required> NO
    </div>
    <button type="submit" class="btn btn-info">Continuar</button>
</form>
{% endblock %}
"""

flujo_a_filters_template = """
{% extends "base.html" %}
{% block content %}
<h2>FLUJO A: Filtros - Ajuste de medida</h2>
<form method="post" action="{{ url_for('flujo_a_filters') }}">
    <div class="form-group">
        <label>Seleccione DIÁMETRO(s):</label>
        <select name="diametros" multiple required>
            {% for diam in diametros %}
            <option value="{{ diam }}">{{ diam }}</option>
            {% endfor %}
        </select>
    </div>
    <!-- Aquí se pueden agregar los demás filtros (TIPO, GRADO DE ACERO, etc.) -->
    <button type="submit" class="btn btn-success">Aplicar Filtros</button>
</form>
{% endblock %}
"""

@app.route('/flujo_a_filters', methods=['POST'])
def flujo_a_filters():
    # Recuperar el DataFrame de flujo A desde la sesión
    df_json = session.get('flujo_a_df')
    if not df_json:
        flash("Error: datos no encontrados para flujo A.")
        return redirect(url_for('flujo_a'))
    df = pd.read_json(df_json, orient='split')
    # Obtener DIÁMETRO(s) seleccionados
    selected_diam = request.form.getlist('diametros')
    if not selected_diam:
        selected_diam = ["TODOS"]
    # Aplicar lógica de filtros (se filtra por DIÁMETRO, tal como en el código original)
    final_condition = df["DIÁMETRO"].isin(selected_diam) if "TODOS" not in selected_diam else True
    final_df = df[final_condition] if final_condition is not True else df
    final_df_renombrado = renombrar_columnas(final_df)
    materiales_finales.append(("FLUJO A", final_df_renombrado))
    flash("Materiales del FLUJO A guardados.")
    # En el código original se salta directamente a FLUJO H en caso de respuesta SI
    return redirect(url_for('flujo_h'))

# ------------------------------------------
# FLUJO B: Tubo de saca
# ------------------------------------------
@app.route('/flujo_b', methods=['GET', 'POST'])
def flujo_b():
    if request.method == 'POST':
        saca_tubing = request.form.get('saca_tubing')
        if saca_tubing == "SI":
            return redirect(url_for('flujo_b_select'))
        elif saca_tubing == "NO":
            flash("No se saca tubing.")
            return redirect(url_for('flujo_c'))
    return render_template_string(flujo_b_template, title="FLUJO B: Tubo de saca")

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

@app.route('/flujo_b_select', methods=['GET', 'POST'])
def flujo_b_select():
    # Cargar Excel de saca tubing
    try:
        folder_path = "materiales"  # Ajusta la ruta
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
    return render_template_string(flujo_b_select_template, diametros=diametros, title="FLUJO B: Selección Tubing")

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
    <!-- Aquí se podrían solicitar cantidades para cada DIÁMETRO -->
    <button type="submit" class="btn btn-success">Aplicar Filtros</button>
</form>
{% endblock %}
"""

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

# ------------------------------------------
# FLUJO C: Tubería de Baja
# ------------------------------------------
@app.route('/flujo_c', methods=['GET', 'POST'])
def flujo_c():
    if request.method == 'POST':
        baja_tubing = request.form.get('baja_tubing')
        if baja_tubing == "SI":
            return redirect(url_for('flujo_c_select'))
        else:
            flash("No se procede con Baja Tubing.")
            return redirect(url_for('flujo_d'))
    return render_template_string(flujo_c_template, title="FLUJO C: Tubería de Baja")

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

@app.route('/flujo_c_select', methods=['GET', 'POST'])
def flujo_c_select():
    # Cargar Excel de baja tubing
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
    return render_template_string(flujo_c_select_template, diametros=diametros, title="FLUJO C: Selección Baja Tubing")

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

@app.route('/flujo_c_apply', methods=['POST'])
def flujo_c_apply():
    df_json = session.get('flujo_c_df')
    if not df_json:
        flash("Error: datos no encontrados para flujo C.")
        return redirect(url_for('flujo_c'))
    df = pd.read_json(df_json, orient='split')
    selected_diam = request.form.getlist('diametros')
    selected_diam = selected_diam if selected_diam else ["TODOS"]
    df_filtered = df[df['DIÁMETRO'].isin(selected_diam)]
    final_df_renombrado = renombrar_columnas(df_filtered)
    materiales_finales.append(("FLUJO C", final_df_renombrado))
    flash("Materiales del FLUJO C guardados.")
    return redirect(url_for('flujo_d'))

# ------------------------------------------
# FLUJO D: Profundiza
# ------------------------------------------
@app.route('/flujo_d', methods=['GET', 'POST'])
def flujo_d():
    if request.method == 'POST':
        profundizar = request.form.get('profundizar')
        if profundizar == "SI":
            return redirect(url_for('flujo_d_select'))
        else:
            flash("No se profundizará en la información.")
            return redirect(url_for('flujo_e'))
    return render_template_string(flujo_d_template, title="FLUJO D: Profundiza")

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

@app.route('/flujo_d_select', methods=['GET', 'POST'])
def flujo_d_select():
    # Cargar Excel de profundiza
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
    diametros = df["DIÁMETRO"].unique().tolist() if "DIÁMETRO" in df.columns else []
    session['flujo_d_df'] = df.to_json(orient='split')
    return render_template_string(flujo_d_select_template, diametros=diametros, title="FLUJO D: Profundiza - Selección")

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
        <input type="number" name="cantidad" required>
    </div>
    <button type="submit" class="btn btn-success">Aplicar</button>
</form>
{% endblock %}
"""

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

# ------------------------------------------
# FLUJO E: Baja varillas
# ------------------------------------------
@app.route('/flujo_e', methods=['GET', 'POST'])
def flujo_e():
    if request.method == 'POST':
        baja_varilla = request.form.get('baja_varilla')
        if baja_varilla == "SI":
            return redirect(url_for('flujo_e_filters'))
        else:
            return redirect(url_for('flujo_f'))
    return render_template_string(flujo_e_template, title="FLUJO E: Baja varillas")

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
    return render_template_string(flujo_e_filters_template, diametros=diametros, title="FLUJO E: Filtros")

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
    <!-- Se pueden agregar los demás filtros (TIPO, GRADO ACERO, etc.) -->
    <button type="submit" class="btn btn-success">Aplicar Filtros</button>
</form>
{% endblock %}
"""

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

# ------------------------------------------
# FLUJO F: Abandona pozo
# ------------------------------------------
@app.route('/flujo_f', methods=['GET', 'POST'])
def flujo_f():
    if request.method == 'POST':
        abandono = request.form.get('abandono')
        if abandono == "SI":
            return redirect(url_for('flujo_f_filters'))
        else:
            return redirect(url_for('flujo_h'))
    return render_template_string(flujo_f_template, title="FLUJO F: Abandona pozo")

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

@app.route('/flujo_f_filters', methods=['GET', 'POST'])
def flujo_f_filters():
    try:
        file_path = os.path.join("materiales", "abandono-recupero.xlsx")
        df = pd.read_excel(file_path)
        df.columns = df.columns.str.strip()
        for col in df.columns:
            if df[col].dtype == object:
                df[col] = df[col].astype(str).str.strip()
    except Exception as e:
        flash("Error al cargar Excel: " + str(e))
        return redirect(url_for('flujo_f'))
    diametros = df["DIÁMETRO"].dropna().unique().tolist()
    if "TODOS" not in diametros:
        diametros.insert(0, "TODOS")
    diametros_csg = df["DIÁMETRO CSG"].dropna().unique().tolist()
    if "TODOS" not in diametros_csg:
        diametros_csg.insert(0, "TODOS")
    session['flujo_f_df'] = df.to_json(orient='split')
    return render_template_string(flujo_f_filters_template, diametros=diametros, diametros_csg=diametros_csg, title="FLUJO F: Filtros")

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
    <!-- Aquí se pueden solicitar cantidades -->
    <button type="submit" class="btn btn-success">Aplicar Filtros y Cantidades</button>
</form>
{% endblock %}
"""

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

# ------------------------------------------
# FLUJO G: Instalación BM
# ------------------------------------------
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
    return render_template_string(flujo_g_template, title="FLUJO G: Instalación BM")

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

# ------------------------------------------
# FLUJO H: Material de agregación
# ------------------------------------------
@app.route('/flujo_h', methods=['GET', 'POST'])
def flujo_h():
    # Cargar Excel GENERAL
    try:
        file_path_H = os.path.join("materiales", "GENERAL.xlsx")
        df_H = pd.read_excel(file_path_H)
        df_H.columns = df_H.columns.str.strip()
        if "4.CANTIDAD" not in df_H.columns:
            df_H["4.CANTIDAD"] = 0
    except Exception as e:
        flash("Error al cargar GENERAL.xlsx: " + str(e))
        df_H = pd.DataFrame()
    materiales = df_H["2. MATERIAL"].astype(str).unique().tolist() if not df_H.empty and "2. MATERIAL" in df_H.columns else []
    return render_template_string(flujo_h_template, materiales=materiales, table=df_H.to_html(classes="table") if not df_H.empty else "", title="FLUJO H: Material de agregación")

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

@app.route('/flujo_h_select', methods=['POST'])
def flujo_h_select():
    selected_materiales = request.form.getlist('materiales')
    if not selected_materiales:
        flash("No se seleccionó ningún material.")
        return redirect(url_for('flujo_h'))
    session['flujo_h_materiales'] = selected_materiales
    return render_template_string(flujo_h_select_template, materiales=selected_materiales, title="FLUJO H: Asignar Cantidades")

flujo_h_select_template = """
{% extends "base.html" %}
{% block content %}
<h2>FLUJO H: Asignar Cantidades</h2>
<form method="post" action="{{ url_for('flujo_h_apply') }}">
    {% for mat in materiales %}
    <div class="form-group">
        <label>Cantidad para {{ mat }}:</label>
        <input type="number" name="qty_{{ mat }}" required>
    </div>
    {% endfor %}
    <button type="submit" class="btn btn-success">Aplicar Cantidades</button>
</form>
{% endblock %}
"""

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

# ------------------------------------------
# Listado final de materiales
# ------------------------------------------
@app.route('/final_list')
def final_list():
    final_html = "<h2>Listado final de materiales de todos los flujos ejecutados:</h2>"
    for flow, df in materiales_finales:
        final_html += f"<h3>{flow}</h3>"
        final_html += df.to_html(classes='table')
    return render_template_string("""
    {% extends "base.html" %}
    {% block content %}
    {{ final_html|safe }}
    {% endblock %}
    """, final_html=final_html, title="Listado Final")

# Página principal redirige a FLUJO A
@app.route('/')
def index():
    return redirect(url_for('flujo_a'))

if __name__ == '__main__':
    app.run(debug=True)


def index():
    return redirect(url_for('flujo_a'))

if __name__ == '__main__':
    app.run(debug=True)
