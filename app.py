import random
from datetime import datetime
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, send_from_directory
import database

app = Flask(__name__)
app.secret_key = "ecosynk_secure_session_key_2026"

# Inicializa o banco de dados na primeira execução
database.init_db()

@app.route("/sw.js")
def service_worker():
    """Serve o Service Worker na raiz para escopo PWA global."""
    return send_from_directory("static", "sw.js", mimetype="application/javascript")

@app.route("/manifest.json")
def manifest():
    """Serve o arquivo manifest.json na raiz."""
    return send_from_directory("static", "manifest.json", mimetype="application/manifest+json")

@app.route("/favicon.ico")
def favicon():
    """Serve o favicon padrão na raiz."""
    return send_from_directory("static", "favicon.ico", mimetype="image/vnd.microsoft.icon")

def get_alerts(modules):
    """Gera lista de alertas ativos do sistema com base nos limites dos módulos."""
    alerts = []
    for mod_id, data in modules.items():
        if data["temperature"] > 50.0:
            alerts.append({
                "type": "warning",
                "module_id": mod_id,
                "message": f"Temperatura acima do limite no módulo {mod_id} ({data['temperature']} °C)."
            })
        if data["humidity"] > 70:
            alerts.append({
                "type": "info",
                "module_id": mod_id,
                "message": f"Umidade acima do ideal no módulo {mod_id} ({data['humidity']}%)."
            })
        if data["status"] == "Problema":
            alerts.append({
                "type": "danger",
                "module_id": mod_id,
                "message": f"Falha operacional detectada no módulo {mod_id}."
            })
    return alerts

def get_overall_system_status(modules):
    has_problem = any(m["status"] == "Problema" for m in modules.values())
    has_attention = any(m["status"] == "Atenção" for m in modules.values())
    if has_problem:
        return "Problema", "rose"
    elif has_attention:
        return "Atenção", "amber"
    return "Normal", "emerald"

@app.route("/")
def index():
    modules = database.get_all_modules()
    
    selected_module_id = request.args.get("module")
    if not selected_module_id or selected_module_id not in modules:
        selected_module_id = list(modules.keys())[0] if modules else None
        
    current_module = modules.get(selected_module_id)
    alerts = get_alerts(modules)
    
    total_active_modules = len(modules)
    general_status, general_color = get_overall_system_status(modules)
    total_processed = database.get_total_processed()

    # Preparar dados para o gráfico de evolução de resíduos (ordem cronológica)
    if current_module and current_module["history"]:
        chart_dates = [item["date"] for item in reversed(current_module["history"])]
        chart_values = [item["residues"] for item in reversed(current_module["history"])]
    else:
        chart_dates = []
        chart_values = []

    return render_template(
        "index.html",
        modules=modules,
        current_module=current_module,
        alerts=alerts,
        total_processed=total_processed,
        active_modules=total_active_modules,
        general_status=general_status,
        general_color=general_color,
        chart_dates=chart_dates,
        chart_values=chart_values
    )

@app.route("/add-reading", methods=["POST"])
def add_reading():
    """Salva nova medição manual no banco de dados."""
    module_id = request.form.get("module_id")
    residues = float(request.form.get("residues", 0))
    temperature = float(request.form.get("temperature", 0))
    humidity = float(request.form.get("humidity", 0))
    date_display = request.form.get("date_display")

    if not date_display:
        date_display = datetime.now().strftime("%d/%m")

    database.insert_reading(module_id, residues, temperature, humidity, date_display)
    flash(f"Nova medição registrada com sucesso no módulo {module_id}!", "success")
    return redirect(url_for("index", module=module_id))

@app.route("/edit-reading", methods=["POST"])
def edit_reading():
    """Edita uma medição existente no histórico."""
    reading_id = int(request.form.get("reading_id"))
    module_id = request.form.get("module_id")
    residues = float(request.form.get("residues", 0))
    temperature = float(request.form.get("temperature", 0))
    humidity = float(request.form.get("humidity", 0))
    date_display = request.form.get("date_display")

    database.update_reading(reading_id, residues, temperature, humidity, date_display)
    flash("Medição atualizada com sucesso no banco de dados!", "success")
    return redirect(url_for("index", module=module_id))

@app.route("/delete-reading/<int:reading_id>", methods=["POST"])
def delete_reading(reading_id):
    """Exclui uma leitura específica do histórico."""
    module_id = request.form.get("module_id", "EC-001")
    database.delete_reading(reading_id)
    flash("Registro removido com sucesso do banco de dados.", "info")
    return redirect(url_for("index", module=module_id))

@app.route("/add-module", methods=["POST"])
def add_module():
    """Cadastra um novo módulo/recicladora."""
    module_id = request.form.get("module_id", "").strip().upper()
    name = request.form.get("name", "").strip()
    location = request.form.get("location", "").strip()
    capacity = float(request.form.get("capacity", 20.0))

    if not module_id or not name:
        flash("Código e Nome do Módulo são obrigatórios.", "danger")
        return redirect(url_for("index"))

    try:
        database.create_module(module_id, name, location, capacity)
        database.insert_reading(module_id, 0.0, 25.0, 50.0, datetime.now().strftime("%d/%m"))
        flash(f"Módulo {module_id} cadastrado com sucesso!", "success")
    except Exception as e:
        flash(f"Erro: Já existe um módulo cadastrado com o código {module_id}.", "danger")

    return redirect(url_for("index", module=module_id))

@app.route("/edit-module", methods=["POST"])
def edit_module():
    """Renomeia e edita localização e capacidade de um módulo."""
    old_id = request.form.get("old_id", "").strip().upper()
    new_id = request.form.get("new_id", "").strip().upper()
    name = request.form.get("name", "").strip()
    location = request.form.get("location", "").strip()
    capacity = float(request.form.get("capacity", 20.0))

    if not new_id or not name:
        flash("Código e Nome não podem ficar vazios.", "danger")
        return redirect(url_for("index", module=old_id))

    try:
        database.update_module(old_id, new_id, name, location, capacity)
        flash(f"Módulo {new_id} renomeado e atualizado com sucesso!", "success")
        return redirect(url_for("index", module=new_id))
    except Exception as e:
        flash(f"Erro ao atualizar módulo: Código {new_id} já em uso.", "danger")
        return redirect(url_for("index", module=old_id))

@app.route("/delete-module/<module_id>", methods=["POST"])
def delete_module(module_id):
    """Exclui completamente um módulo e todo seu histórico."""
    database.delete_module(module_id)
    flash(f"Módulo {module_id} e todo seu histórico foram excluídos permanentemente.", "info")
    return redirect(url_for("index"))

@app.route("/api/module/<module_id>")
def api_module(module_id):
    """Return JSON data for a specific module (used for AJAX updates)."""
    modules = database.get_all_modules()
    if module_id not in modules:
        return {"error": "Module not found"}, 404
    mod = modules[module_id]
    # Prepare chart data in chronological order (oldest to newest)
    chart_dates = [item["date"] for item in reversed(mod["history"])]
    chart_values = [item["residues"] for item in reversed(mod["history"])]
    return {
        "id": mod["id"],
        "name": mod["name"],
        "location": mod["location"],
        "processed_today": mod["processed_today"],
        "temperature": mod["temperature"],
        "humidity": mod["humidity"],
        "status": mod["status"],
        "history": mod["history"],
        "chart_dates": chart_dates,
        "chart_values": chart_values,
    }

if __name__ == "__main__":
    print("Iniciando EcoSynk Web Server na porta 5000...")
    app.run(debug=True, host="127.0.0.1", port=5000)
