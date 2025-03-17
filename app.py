import os
import pandas as pd
from flask import Flask, request, render_template_string, redirect, url_for

app = Flask(__name__)
app.secret_key = 'tu_secret_key_aqui'

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
    columnas = ["Cód.SAP", "MATERIAL", "Descripción", "4.CANTIDAD", "CONDICIÓN"]
    columnas_presentes = [col for col in columnas if col in df_renombrado.columns]
    return df_renombrado[columnas_presentes]

# -----------------------------------------------------------
# RUTAS DE LA APLICACIÓN: cada flujo es un endpoint separado
# -----------------------------------------------------------

@app.route('/')
def index():
    # Inicia el proceso en FLUJO A
    return redirect(url_for('flujoA'))

# ===============================
# FLUJO A: Ajuste de medida
# ===============================
@app.route('/flujoA', methods=['GET', 'POST'])
def flujoA():
    if request.method == 'POST':
        ajuste = request.form.get('ajuste')
        # Si se responde SI, se muestra el formulario de filtros;
        # en caso de NO se salta al FLUJO B.
        if ajuste == 'SI':
            return redirect(url_for('flujoA_filters'))
        else:
            return redirect(url_for('flujoB'))
    html = '''
    <h2>FLUJO A: Ajuste de medida</h2>
    <form method="post">
        <label>¿Ajuste de medida?</label><br>
        <input type="radio" name="ajuste" value="SI" required> SI<br>
        <input type="radio" name="ajuste" value="NO"> NO<br><br>
        <input type="submit" value="Continuar">
    </form>
    '''
    return render_template_string(html)

@app.route('/flujoA/filters', methods=['GET', 'POST'])
def flujoA_filters():
    # Se carga el Excel para el flujo A (ruta relativa en la carpeta "materiales")
    file_path = os.path.join('materiales', 'ajuste de medida(2).xlsx')
    try:
        df = pd.read_excel(file_path)
        df.columns = df.columns.str.strip()
        df["DIÁMETRO"] = df["DIÁMETRO"].astype(str).str.strip()
    except Exception as e:
        return f"Error al cargar el archivo Excel: {e}"
    
    if request.method == 'POST':
        # Se reciben los valores seleccionados para cada DIÁMETRO
        selected_diams = request.form.getlist('diametros')
        all_filters = {}
        for diam in selected_diams:
            tipo_list = request.form.getlist(f'tipo_{diam}')
            acero = request.form.get(f'acero_{diam}')
            acero_list = [acero] if acero and acero != "Seleccionar" else []
            acero_list.append("TODOS")
            acero_cup = request.form.get(f'acero_cup_{diam}')
            acero_cup_list = [acero_cup] if acero_cup and acero_cup != "Seleccionar" else []
            acero_cup_list.append("TODOS")
            tipo_cup = request.form.get(f'tipo_cup_{diam}')
            tipo_cup_list = [tipo_cup] if tipo_cup and tipo_cup != "Seleccionar" else []
            tipo_cup_list.append("TODOS")
            if not tipo_list:
                tipo_list = ["TODOS"]
            else:
                tipo_list.append("TODOS")
            all_filters[diam] = {"tipo_list": tipo_list, "acero_list": acero_list,
                                 "acero_cup_list": acero_cup_list, "tipo_cup_list": tipo_cup_list}
        # Se aplica la lógica de filtrado sobre el DataFrame
        final_condition = pd.Series([False] * len(df))
        for diam, fdict in all_filters.items():
            temp_cond = pd.Series([False] * len(df))
            for tipo_val in fdict["tipo_list"]:
                cond = (df["DIÁMETRO"].isin([diam, "TODOS"]) &
                        df["TIPO"].isin([tipo_val, "TODOS"]) &
                        df["GRADO DE ACERO"].isin(fdict["acero_list"]) &
                        df["GRADO DE ACERO CUPLA"].isin(fdict["acero_cup_list"]) &
                        df["TIPO DE CUPLA"].isin(fdict["tipo_cup_list"]))
                temp_cond = temp_cond | cond
            final_condition = final_condition | temp_cond
        final_df = df[final_condition]
        final_df_renombrado = renombrar_columnas(final_df)
        materiales_finales.append(("FLUJO A", final_df_renombrado))
        # Se salta directamente al FLUJO H (según la lógica original)
        return redirect(url_for('flujoH'))
    
    # GET: Se muestra el formulario para seleccionar DIÁMETRO y los filtros asociados.
    all_diams = sorted([x for x in df["DIÁMETRO"].dropna().unique() if x.upper() != "TODOS"])
    form_html = '''
    <h2>FLUJO A: Filtros Ajuste de medida</h2>
    <form method="post">
        <label>Seleccione DIÁMETRO (múltiple):</label><br>
        <select name="diametros" multiple size="5">
    '''
    for diam in all_diams:
        form_html += f'<option value="{diam}">{diam}</option>'
    form_html += '</select><br><br>'
    
    # Se generan campos de filtro para cada opción de DIÁMETRO (estos campos se envían solo si el DIÁMETRO fue seleccionado)
    for diam in all_diams:
        subset = df[df["DIÁMETRO"] == diam]
        tipos = sorted([x for x in subset["TIPO"].dropna().unique() if x.upper() != "TODOS"])
        grados_acero = sorted([x for x in subset["GRADO DE ACERO"].dropna().unique() if str(x).upper() != "TODOS"])
        grados_acero_cup = sorted([x for x in subset["GRADO DE ACERO CUPLA"].dropna().unique() if str(x).upper() != "TODOS"])
        tipos_cup = sorted([x for x in subset["TIPO DE CUPLA"].dropna().unique() if str(x).upper() != "TODOS"])
        form_html += f'<fieldset><legend>Filtros para DIÁMETRO: {diam}</legend>'
        form_html += '<label>TIPO (múltiple):</label><br>'
        form_html += f'<select name="tipo_{diam}" multiple size="3">'
        for t in tipos:
            form_html += f'<option value="{t}">{t}</option>'
        form_html += '</select><br><br>'
        form_html += '<label>GRADO ACERO:</label><br>'
        form_html += '<select name="acero_' + diam + '">'
        form_html += '<option value="Seleccionar">Seleccionar</option>'
        for ac in grados_acero:
            form_html += f'<option value="{ac}">{ac}</option>'
        form_html += '</select><br><br>'
        form_html += '<label>GRADO ACERO CUPLA:</label><br>'
        form_html += '<select name="acero_cup_' + diam + '">'
        form_html += '<option value="Seleccionar">Seleccionar</option>'
        for ac in grados_acero_cup:
            form_html += f'<option value="{ac}">{ac}</option>'
        form_html += '</select><br><br>'
        form_html += '<label>TIPO CUPLA:</label><br>'
        form_html += '<select name="tipo_cup_' + diam + '">'
        form_html += '<option value="Seleccionar">Seleccionar</option>'
        for tc in tipos_cup:
            form_html += f'<option value="{tc}">{tc}</option>'
        form_html += '</select><br><br>'
        form_html += '</fieldset><br>'
    form_html += '<input type="submit" value="Aplicar Filtros">'
    form_html += '</form>'
    return render_template_string(form_html)

# ===============================
# FLUJO B: Tubo de saca
# ===============================
@app.route('/flujoB', methods=['GET', 'POST'])
def flujoB():
    file_path = os.path.join('materiales', 'saca tubing.xlsx')
    global df_saca_tubing
    if request.method == 'POST':
        saca = request.form.get('saca_tubing')
        if saca == 'SI':
            try:
                df_tmp = pd.read_excel(file_path)
                df_tmp.columns = df_tmp.columns.str.strip()
                for c in df_tmp.columns:
                    if df_tmp[c].dtype == object:
                        df_tmp[c] = df_tmp[c].astype(str).str.strip()
                df_saca_tubing = df_tmp.copy()
            except Exception as e:
                return f"Error al cargar el Excel de saca tubing: {e}"
            selected_diams = request.form.getlist('diametros')
            df_filtered = df_saca_tubing[
                (df_saca_tubing['DIÁMETRO'].isin(selected_diams)) |
                (df_saca_tubing['DIÁMETRO'].str.upper() == 'TODOS')
            ].copy()
            for diam in selected_diams:
                qty = request.form.get(f'qty_{diam}', type=float)
                mask = (df_filtered['DIÁMETRO'] == diam)
                df_filtered.loc[mask, '4.CANTIDAD'] = qty
            df_filtered_renombrado = renombrar_columnas(df_filtered)
            materiales_finales.append(("FLUJO B", df_filtered_renombrado))
            return redirect(url_for('flujoC'))
        else:
            return redirect(url_for('flujoC'))
    # GET: Se muestra un formulario para "Saca Tubing"
    try:
        df_tmp = pd.read_excel(file_path)
        df_tmp.columns = df_tmp.columns.str.strip()
        diam_options = sorted([d for d in df_tmp['DIÁMETRO'].unique() if d.upper() != 'TODOS'])
    except Exception as e:
        diam_options = []
    form_html = '''
    <h2>FLUJO B: Tubo de saca</h2>
    <form method="post">
        <label>¿Saca Tubing?</label><br>
        <select name="saca_tubing" required>
            <option value="">Seleccione opción</option>
            <option value="SI">SI</option>
            <option value="NO">NO</option>
        </select><br><br>
        <div id="saca_options" style="display:none;">
            <label>Seleccione DIÁMETRO (múltiple):</label><br>
            <select name="diametros" multiple size="5">
    '''
    for d in diam_options:
        form_html += f'<option value="{d}">{d}</option>'
    form_html += '''
            </select><br><br>
            <label>Ingrese cantidad para cada DIÁMETRO seleccionado:</label><br>
    '''
    for d in diam_options:
        form_html += f'{d}: <input type="number" step="any" name="qty_{d}" value="0"><br>'
    form_html += '''
        </div>
        <input type="submit" value="Enviar">
        <script>
            document.querySelector('select[name="saca_tubing"]').addEventListener('change', function() {
                if(this.value == "SI"){
                    document.getElementById("saca_options").style.display = "block";
                } else {
                    document.getElementById("saca_options").style.display = "none";
                }
            });
        </script>
    </form>
    '''
    return render_template_string(form_html)

# ===============================
# FLUJO C: Tubería de Baja
# ===============================
@app.route('/flujoC', methods=['GET', 'POST'])
def flujoC():
    file_path = os.path.join('materiales', 'baja tubing.xlsx')
    global df_baja_tubing
    if request.method == 'POST':
        baja = request.form.get('baja_tubing')
        if baja == 'SI':
            try:
                df = pd.read_excel(file_path)
                df.columns = df.columns.str.strip()
                for col in df.columns:
                    if df[col].dtype == object:
                        df[col] = df[col].astype(str).str.strip()
                df_baja_tubing = df.copy()
            except Exception as e:
                return f"Error al cargar el Excel de baja tubing: {e}"
            selected_diams = request.form.getlist('diametros')
            selected_tipos = {}
            for diam in selected_diams:
                tipos = request.form.getlist(f'tipo_{diam}')
                if not tipos:
                    tipos = ["TODOS"]
                selected_tipos[diam] = tipos
            selected_csg = request.form.get('diam_csg')
            # Se aplica un filtrado simplificado basado en lo seleccionado
            union_tipos = set()
            for tlist in selected_tipos.values():
                union_tipos.update(tlist)
                union_tipos.add("TODOS")
            diam_filter = selected_diams if "TODOS" not in selected_diams else ["TODOS"]
            df_filtered = df_baja_tubing[df_baja_tubing['DIÁMETRO'].isin(diam_filter) &
                                         df_baja_tubing['TIPO'].isin(list(union_tipos))]
            qty = request.form.get('quantity', type=float)
            if qty is not None:
                df_filtered.loc[df_filtered['4.CANTIDAD'].isna(), '4.CANTIDAD'] = qty
            df_filtered_renombrado = renombrar_columnas(df_filtered)
            materiales_finales.append(("FLUJO C", df_filtered_renombrado))
            return redirect(url_for('flujoD'))
        else:
            return redirect(url_for('flujoD'))
    # GET: Formulario básico para Baja Tubing
    try:
        df = pd.read_excel(file_path)
        df.columns = df.columns.str.strip()
        diam_options = sorted([x for x in df['DIÁMETRO'].unique() if x != "TODOS"])
    except Exception as e:
        diam_options = []
    form_html = '''
    <h2>FLUJO C: Tubería de Baja</h2>
    <form method="post">
        <label>¿Baja Tubing?</label><br>
        <select name="baja_tubing" required>
            <option value="">Seleccione opción</option>
            <option value="SI">SI</option>
            <option value="NO">NO</option>
        </select><br><br>
        <div id="baja_options" style="display:none;">
            <label>Seleccione DIÁMETRO (múltiple):</label><br>
            <select name="diametros" multiple size="5">
    '''
    for d in diam_options:
        form_html += f'<option value="{d}">{d}</option>'
    form_html += '''
            </select><br><br>
            Para cada DIÁMETRO, seleccione TIPO (múltiple):<br>
    '''
    for d in diam_options:
        # Se leen los tipos para cada DIÁMETRO
        subset = pd.read_excel(file_path)
        subset.columns = subset.columns.str.strip()
        subset = subset[subset["DIÁMETRO"]==d]
        tipos = sorted([x for x in subset['TIPO'].dropna().unique() if x != "TODOS"])
        form_html += f'<label>{d} - TIPO:</label><br>'
        form_html += f'<select name="tipo_{d}" multiple size="3">'
        for t in tipos:
            form_html += f'<option value="{t}">{t}</option>'
        form_html += '</select><br><br>'
    form_html += '''
            <label>Seleccione DIÁMETRO CSG:</label><br>
            <select name="diam_csg">
    '''
    try:
        df = pd.read_excel(file_path)
        df.columns = df.columns.str.strip()
        csg_options = sorted([x for x in df['DIÁMETRO CSG'].dropna().unique() if x != "TODOS"])
    except Exception as e:
        csg_options = []
    for c in csg_options:
        form_html += f'<option value="{c}">{c}</option>'
    form_html += '''
            </select><br><br>
            <label>Ingrese cantidad (aplicada a celdas vacías):</label>
            <input type="number" step="any" name="quantity" value="0"><br><br>
        </div>
        <input type="submit" value="Enviar">
        <script>
            document.querySelector('select[name="baja_tubing"]').addEventListener('change', function() {
                if(this.value == "SI"){
                    document.getElementById("baja_options").style.display = "block";
                } else {
                    document.getElementById("baja_options").style.display = "none";
                }
            });
        </script>
    </form>
    '''
    return render_template_string(form_html)

# ===============================
# FLUJO D: Profundiza
# ===============================
@app.route('/flujoD', methods=['GET', 'POST'])
def flujoD():
    file_path = os.path.join('materiales', 'profundiza.xlsx')
    global df_prof
    if request.method == 'POST':
        profundizar = request.form.get('profundizar')
        if profundizar == 'SI':
            try:
                df = pd.read_excel(file_path)
                df.columns = df.columns.str.strip()
                for col in df.columns:
                    if df[col].dtype == object:
                        df[col] = df[col].astype(str).str.strip()
                df_prof = df.copy()
            except Exception as e:
                return f"Error al cargar el Excel de profundiza: {e}"
            selected_diams = request.form.getlist('diametros')
            quantities = {}
            for d in selected_diams:
                qty = request.form.get(f'qty_{d}', type=float)
                quantities[d] = qty
            filtered_df = df_prof[df_prof['DIÁMETRO'].isin(selected_diams)].copy()
            for d in selected_diams:
                filtered_df.loc[filtered_df['DIÁMETRO'] == d, '4.CANTIDAD'] = quantities.get(d, 0)
            final_df_renombrado = renombrar_columnas(filtered_df)
            materiales_finales.append(("FLUJO D", final_df_renombrado))
            return redirect(url_for('flujoE'))
        else:
            return redirect(url_for('flujoE'))
    # GET: Formulario para profundizar
    try:
        df = pd.read_excel(file_path)
        df.columns = df.columns.str.strip()
        col_diam = "DIÁMETRO" if "DIÁMETRO" in df.columns else "DIÁMETRO CSG"
        diam_options = df[col_diam].dropna().unique().tolist()
    except Exception as e:
        diam_options = []
    form_html = '''
    <h2>FLUJO D: Profundiza</h2>
    <form method="post">
        <label>Profundizar:</label><br>
        <select name="profundizar" required>
            <option value="">seleccionar</option>
            <option value="SI">SI</option>
            <option value="NO">NO</option>
        </select><br><br>
        <div id="profundiza_options" style="display:none;">
            <label>Seleccione DIÁMETRO (múltiple):</label><br>
            <select name="diametros" multiple size="5">
    '''
    for d in diam_options:
        form_html += f'<option value="{d}">{d}</option>'
    form_html += '''
            </select><br><br>
            Para cada DIÁMETRO, ingrese cantidad:<br>
    '''
    for d in diam_options:
        form_html += f'{d}: <input type="number" step="any" name="qty_{d}" value="0"><br>'
    form_html += '''
        </div>
        <input type="submit" value="Enviar">
        <script>
            document.querySelector('select[name="profundizar"]').addEventListener('change', function() {
                if(this.value == "SI"){
                    document.getElementById("profundiza_options").style.display = "block";
                } else {
                    document.getElementById("profundiza_options").style.display = "none";
                }
            });
        </script>
    </form>
    '''
    return render_template_string(form_html)

# ===============================
# FLUJO E: Baja varillas
# ===============================
@app.route('/flujoE', methods=['GET', 'POST'])
def flujoE():
    file_path = os.path.join('materiales', 'baja varillas.xlsx')
    global df_baja_varillas
    if request.method == 'POST':
        baja_varilla = request.form.get('baja_varilla')
        if baja_varilla == 'SI':
            try:
                df = pd.read_excel(file_path)
                df.columns = df.columns.str.strip()
                df["DIÁMETRO"] = df["DIÁMETRO"].astype(str).str.strip()
                df_baja_varillas = df.copy()
            except Exception as e:
                return f"Error al cargar el Excel de baja varillas: {e}"
            selected_diams = request.form.getlist('diametros')
            all_filters = {}
            for diam in selected_diams:
                tipo_list = request.form.getlist(f'tipo_{diam}')
                if not tipo_list:
                    tipo_list = ["TODOS"]
                else:
                    tipo_list.append("TODOS")
                ac = request.form.get(f'acero_{diam}')
                acero_list = [ac] if ac and ac != "Seleccionar" else []
                acero_list.append("TODOS")
                ac_cup = request.form.get(f'acero_cup_{diam}')
                acero_cup_list = [ac_cup] if ac_cup and ac_cup != "Seleccionar" else []
                acero_cup_list.append("TODOS")
                t_cup = request.form.get(f'tipo_cup_{diam}')
                tipo_cup_list = [t_cup] if t_cup and t_cup != "Seleccionar" else []
                tipo_cup_list.append("TODOS")
                all_filters[diam] = {"tipo_list": tipo_list, "acero_list": acero_list,
                                     "acero_cup_list": acero_cup_list, "tipo_cup_list": tipo_cup_list}
            df = pd.read_excel(file_path)
            df.columns = df.columns.str.strip()
            final_condition = pd.Series([False]*len(df))
            for diam, fdict in all_filters.items():
                temp_cond = pd.Series([False]*len(df))
                for tipo_val in fdict["tipo_list"]:
                    cond = (df["DIÁMETRO"].isin([diam, "TODOS"]) &
                            df["TIPO"].isin([tipo_val, "TODOS"]) &
                            df["GRADO DE ACERO"].isin(fdict["acero_list"]) &
                            df["GRADO DE ACERO CUPLA"].isin(fdict["acero_cup_list"]) &
                            df["TIPO DE CUPLA"].isin(fdict["tipo_cup_list"]))
                    temp_cond = temp_cond | cond
                final_condition = final_condition | temp_cond
            final_df = df[final_condition]
            final_df_renombrado = renombrar_columnas(final_df)
            materiales_finales.append(("FLUJO E", final_df_renombrado))
            return redirect(url_for('flujoF'))
        else:
            return redirect(url_for('flujoF'))
    # GET: Formulario para Baja Varilla
    try:
        df = pd.read_excel(file_path)
        df.columns = df.columns.str.strip()
        diam_options = sorted([x for x in df["DIÁMETRO"].dropna().unique() if x.upper() != "TODOS"])
    except Exception as e:
        diam_options = []
    form_html = '''
    <h2>FLUJO E: Baja varillas</h2>
    <form method="post">
        <label>¿Baja Varilla?</label><br>
        <select name="baja_varilla" required>
            <option value="">seleccionar</option>
            <option value="SI">SI</option>
            <option value="NO">NO</option>
        </select><br><br>
        <div id="varilla_options" style="display:none;">
            <label>Seleccione DIÁMETRO (múltiple):</label><br>
            <select name="diametros" multiple size="5">
    '''
    for d in diam_options:
        form_html += f'<option value="{d}">{d}</option>'
    form_html += '</select><br><br>'
    for d in diam_options:
        subset = pd.read_excel(file_path)
        subset.columns = subset.columns.str.strip()
        subset = subset[subset["DIÁMETRO"]==d]
        tipos = sorted([x for x in subset["TIPO"].dropna().unique() if x.upper() != "TODOS"])
        grados_acero = sorted([x for x in subset["GRADO DE ACERO"].dropna().unique() if str(x).upper() != "TODOS"])
        grados_acero_cup = sorted([x for x in subset["GRADO DE ACERO CUPLA"].dropna().unique() if str(x).upper() != "TODOS"])
        tipos_cup = sorted([x for x in subset["TIPO DE CUPLA"].dropna().unique() if str(x).upper() != "TODOS"])
        form_html += f'<fieldset><legend>Filtros para DIÁMETRO: {d}</legend>'
        form_html += '<label>TIPO (múltiple):</label><br>'
        form_html += f'<select name="tipo_{d}" multiple size="3">'
        for t in tipos:
            form_html += f'<option value="{t}">{t}</option>'
        form_html += '</select><br><br>'
        form_html += '<label>GRADO ACERO:</label><br>'
        form_html += '<select name="acero_' + d + '">'
        form_html += '<option value="Seleccionar">Seleccionar</option>'
        for ac in grados_acero:
            form_html += f'<option value="{ac}">{ac}</option>'
        form_html += '</select><br><br>'
        form_html += '<label>GRADO ACERO CUPLA:</label><br>'
        form_html += '<select name="acero_cup_' + d + '">'
        form_html += '<option value="Seleccionar">Seleccionar</option>'
        for ac in grados_acero_cup:
            form_html += f'<option value="{ac}">{ac}</option>'
        form_html += '</select><br><br>'
        form_html += '<label>TIPO CUPLA:</label><br>'
        form_html += '<select name="tipo_cup_' + d + '">'
        form_html += '<option value="Seleccionar">Seleccionar</option>'
        for tc in tipos_cup:
            form_html += f'<option value="{tc}">{tc}</option>'
        form_html += '</select><br><br>'
        form_html += '</fieldset><br>'
    form_html += '''
        </div>
        <input type="submit" value="Aplicar Filtros">
        <script>
            document.querySelector('select[name="baja_varilla"]').addEventListener('change', function() {
                if(this.value == "SI"){
                    document.getElementById("varilla_options").style.display = "block";
                } else {
                    document.getElementById("varilla_options").style.display = "none";
                }
            });
        </script>
    </form>
    '''
    return render_template_string(form_html)

# ===============================
# FLUJO F: Abandona pozo
# ===============================
@app.route('/flujoF', methods=['GET', 'POST'])
def flujoF():
    file_path = os.path.join('materiales', 'abandono-recupero.xlsx')
    global df_abandono
    if request.method == 'POST':
        abandono = request.form.get('abandono')
        if abandono == 'SI':
            try:
                df = pd.read_excel(file_path)
                df.columns = df.columns.str.strip()
                for col in df.columns:
                    if df[col].dtype == object:
                        df[col] = df[col].astype(str).str.strip()
                df_abandono = df.copy()
            except Exception as e:
                return f"Error al cargar el Excel de abandono-recupero: {e}"
            selected_diams = request.form.getlist('diametros')
            diametro_csg = request.form.get('diam_csg')
            def filter_by_todos(df, column, selected_values):
                if "TODOS" in selected_values:
                    return df
                else:
                    allowed_values = list(selected_values) + ["TODOS"]
                    return df[df[column].isin(allowed_values)]
            filtered_df = filter_by_todos(df_abandono, "DIÁMETRO", selected_diams)
            filtered_df = filter_by_todos(filtered_df, "DIÁMETRO CSG", [diametro_csg])
            diam_especificos = [d for d in selected_diams if d != "TODOS"]
            for d in diam_especificos:
                qty = request.form.get(f'qty_{d}', type=float)
                mask = (filtered_df["DIÁMETRO"] == d) & (filtered_df["4.CANTIDAD"].isna())
                filtered_df.loc[mask, "4.CANTIDAD"] = qty
            filtered_final = filter_by_todos(filtered_df, "DIÁMETRO", selected_diams)
            filtered_final = filter_by_todos(filtered_final, "DIÁMETRO CSG", [diametro_csg])
            final_df_renombrado = renombrar_columnas(filtered_final)
            materiales_finales.append(("FLUJO F", final_df_renombrado))
            return redirect(url_for('flujoH'))
        else:
            return redirect(url_for('flujoH'))
    # GET: Formulario para Abandono/Recupero
    try:
        df = pd.read_excel(file_path)
        df.columns = df.columns.str.strip()
        diam_options = df["DIÁMETRO"].dropna().unique().tolist()
        if "TODOS" not in diam_options:
            diam_options.insert(0, "TODOS")
    except Exception as e:
        diam_options = []
    try:
        df = pd.read_excel(file_path)
        df.columns = df.columns.str.strip()
        csg_options = df["DIÁMETRO CSG"].dropna().unique().tolist()
        if "TODOS" not in csg_options:
            csg_options.insert(0, "TODOS")
    except Exception as e:
        csg_options = []
    form_html = '''
    <h2>FLUJO F: Abandona pozo</h2>
    <form method="post">
        <label>¿Abandono/recupero?</label><br>
        <select name="abandono" required>
            <option value="">Seleccione</option>
            <option value="SI">SI</option>
            <option value="NO">NO</option>
        </select><br><br>
        <div id="abandono_options" style="display:none;">
            <label>Seleccione DIÁMETRO (múltiple):</label><br>
            <select name="diametros" multiple size="5">
    '''
    for d in diam_options:
        form_html += f'<option value="{d}">{d}</option>'
    form_html += '''
            </select><br><br>
            <label>Seleccione DIÁMETRO CSG:</label><br>
            <select name="diam_csg">
    '''
    for c in csg_options:
        form_html += f'<option value="{c}">{c}</option>'
    form_html += '''
            </select><br><br>
            <label>Ingrese cantidad para cada DIÁMETRO seleccionado (solo para celdas vacías):</label><br>
    '''
    for d in diam_options:
        if d != "TODOS":
            form_html += f'{d}: <input type="number" step="any" name="qty_{d}" value="0"><br>'
    form_html += '''
        </div>
        <input type="submit" value="Enviar">
        <script>
            document.querySelector('select[name="abandono"]').addEventListener('change', function() {
                if(this.value == "SI"){
                    document.getElementById("abandono_options").style.display = "block";
                } else {
                    document.getElementById("abandono_options").style.display = "none";
                }
            });
        </script>
    </form>
    '''
    return render_template_string(form_html)

# ===============================
# FLUJO G: Instalación BM
# ===============================
@app.route('/flujoG', methods=['GET', 'POST'])
def flujoG():
    file_path = os.path.join('materiales', 'WO.xlsx')
    if request.method == 'POST':
        wo = request.form.get('wo_bm')
        if wo == 'SI':
            try:
                df = pd.read_excel(file_path)
                df_renombrado = renombrar_columnas(df)
                materiales_finales.append(("FLUJO G", df_renombrado))
            except Exception as e:
                return f"Error al cargar WO.xlsx: {e}"
            return redirect(url_for('flujoH'))
        else:
            return redirect(url_for('flujoH'))
    form_html = '''
    <h2>FLUJO G: Instalación BM</h2>
    <form method="post">
        <label>¿WO a BM?</label><br>
        <input type="radio" name="wo_bm" value="SI" required> SI<br>
        <input type="radio" name="wo_bm" value="NO"> NO<br><br>
        <input type="submit" value="Enviar">
    </form>
    '''
    return render_template_string(form_html)

# ===============================
# FLUJO H: Material de agregación
# ===============================
@app.route('/flujoH', methods=['GET', 'POST'])
def flujoH():
    file_path = os.path.join('materiales', 'GENERAL(1).xlsx')
    global df_H
    try:
        df = pd.read_excel(file_path)
        df.columns = df.columns.str.strip()
        if "4.CANTIDAD" not in df.columns:
            df["4.CANTIDAD"] = 0
        df_H = df.copy()
    except Exception as e:
        df_H = pd.DataFrame()
    
    if request.method == 'POST':
        agregar = request.form.get('agregar_material')
        if agregar == 'SI':
            selected_materials = request.form.getlist('materiales')
            qtys = {}
            for mat in selected_materials:
                qty = request.form.get(f'qty_{mat}', type=float)
                qtys[mat] = qty
            for mat, qty in qtys.items():
                df_H.loc[df_H["2. MATERIAL"].astype(str) == mat, "4.CANTIDAD"] = qty
            assigned_df = df_H[
                (df_H["2. MATERIAL"].astype(str).isin(selected_materials)) &
                (df_H["4.CANTIDAD"] > 0)
            ]
            if not assigned_df.empty:
                assigned_df_renombrado = renombrar_columnas(assigned_df)
                materiales_finales.append(("FLUJO H", assigned_df_renombrado))
        return redirect(url_for('final_list'))
    
    if not df_H.empty and "2. MATERIAL" in df_H.columns:
        materiales = df_H["2. MATERIAL"].astype(str).unique().tolist()
    else:
        materiales = []
    form_html = '''
    <h2>FLUJO H: Material de agregación</h2>
    <form method="post">
        <label>¿Agregar más material?</label><br>
        <select name="agregar_material" required>
            <option value="">Seleccione</option>
            <option value="SI">SI</option>
            <option value="NO">NO</option>
        </select><br><br>
        <div id="material_options" style="display:none;">
            <label>Seleccione materiales (múltiple):</label><br>
            <select name="materiales" multiple size="5">
    '''
    for mat in materiales:
        form_html += f'<option value="{mat}">{mat}</option>'
    form_html += '''
            </select><br><br>
            Para cada material seleccionado, ingrese cantidad:<br>
    '''
    for mat in materiales:
        form_html += f'{mat}: <input type="number" step="any" name="qty_{mat}" value="0"><br>'
    form_html += '''
        </div>
        <input type="submit" value="Enviar">
        <script>
            document.querySelector('select[name="agregar_material"]').addEventListener('change', function() {
                if(this.value == "SI"){
                    document.getElementById("material_options").style.display = "block";
                } else {
                    document.getElementById("material_options").style.display = "none";
                }
            });
        </script>
    </form>
    <br>
    <a href="/final_list">Mostrar Listado Final de Materiales</a>
    '''
    return render_template_string(form_html)

# ===============================
# Pantalla Final: Listado de Materiales
# ===============================
@app.route('/final_list')
def final_list():
    html = '<h2>Listado final de materiales</h2>'
    for flow, df in materiales_finales:
        html += f'<h3>{flow}</h3>'
        html += df.to_html()
    return render_template_string(html)

# -----------------------------------------------------------
# Ejecuta la aplicación
# -----------------------------------------------------------
if __name__ == '__main__':
    app.run(debug=True)


