import os
import sqlite3
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ecosynk.db")

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def calculate_status(temp, humidity):
    """Calcula o status do bioprocesso com base nos limites definidos."""
    if temp > 55.0 or humidity > 85 or humidity < 30:
        return "Problema"
    elif temp > 50.0 or humidity > 70 or humidity < 40:
        return "Atenção"
    return "Normal"

def init_db():
    """Cria as tabelas e insere dados iniciais caso o banco esteja vazio."""
    conn = get_db()
    cursor = conn.cursor()

    # Tabela de Módulos (composteiras/recicladoras)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS modules (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        location TEXT NOT NULL,
        total_capacity REAL DEFAULT 20.0
    );
    """)

    # Tabela de Leituras / Histórico de Operação
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS readings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        module_id TEXT NOT NULL,
        date_display TEXT NOT NULL,
        residues REAL NOT NULL,
        temperature REAL NOT NULL,
        humidity REAL NOT NULL,
        status TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (module_id) REFERENCES modules (id) ON DELETE CASCADE
    );
    """)

    # Verificar se já existem módulos cadastrados
    cursor.execute("SELECT COUNT(*) as count FROM modules")
    if cursor.fetchone()["count"] == 0:
        # Inserir módulos padrão
        modules_init = [
            ("EC-001", "Módulo EC-001", "Restaurante Central (Praça A)", 20.0),
            ("EC-002", "Módulo EC-002", "Cozinha Industrial (Setor B)", 20.0),
            ("EC-003", "Módulo EC-003", "Refeitório Anexo (Bloco C)", 20.0),
        ]
        cursor.executemany("INSERT INTO modules (id, name, location, total_capacity) VALUES (?, ?, ?, ?)", modules_init)

        # Inserir dados históricos de exemplo para os 3 módulos
        readings_init = [
            # EC-001
            ("EC-001", "18/09", 8.5, 42.0, 55.0, "Normal"),
            ("EC-001", "17/09", 7.8, 41.5, 57.0, "Normal"),
            ("EC-001", "16/09", 9.2, 44.0, 62.0, "Atenção"),
            ("EC-001", "15/09", 8.1, 40.8, 53.0, "Normal"),
            ("EC-001", "14/09", 7.4, 39.5, 50.0, "Normal"),
            ("EC-001", "13/09", 6.9, 41.0, 52.0, "Normal"),
            ("EC-001", "12/09", 8.0, 42.5, 54.0, "Normal"),
            # EC-002
            ("EC-002", "18/09", 12.3, 43.5, 58.0, "Normal"),
            ("EC-002", "17/09", 11.9, 42.8, 56.0, "Normal"),
            ("EC-002", "16/09", 10.5, 41.2, 54.0, "Normal"),
            ("EC-002", "15/09", 12.0, 43.0, 59.0, "Normal"),
            ("EC-002", "14/09", 9.8, 40.0, 52.0, "Normal"),
            ("EC-002", "13/09", 10.1, 41.5, 55.0, "Normal"),
            ("EC-002", "12/09", 11.2, 42.0, 56.0, "Normal"),
            # EC-003
            ("EC-003", "18/09", 14.1, 52.8, 71.0, "Atenção"),
            ("EC-003", "17/09", 13.5, 49.2, 68.0, "Normal"),
            ("EC-003", "16/09", 12.8, 47.0, 65.0, "Normal"),
            ("EC-003", "15/09", 11.0, 44.5, 60.0, "Normal"),
            ("EC-003", "14/09", 10.5, 43.0, 58.0, "Normal"),
            ("EC-003", "13/09", 9.7, 42.0, 55.0, "Normal"),
            ("EC-003", "12/09", 10.0, 41.8, 56.0, "Normal"),
        ]
        cursor.executemany(
            "INSERT INTO readings (module_id, date_display, residues, temperature, humidity, status) VALUES (?, ?, ?, ?, ?, ?)",
            readings_init
        )

    conn.commit()
    conn.close()

def get_all_modules():
    """Retorna dicionário com os módulos e suas leituras mais recentes."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM modules ORDER BY id ASC")
    modules_rows = cursor.fetchall()
    
    modules_dict = {}
    for row in modules_rows:
        mod_id = row["id"]
        # Buscar histórico ordenado pelo ID mais recente
        cursor.execute("SELECT * FROM readings WHERE module_id = ? ORDER BY id DESC LIMIT 20", (mod_id,))
        readings_rows = cursor.fetchall()

        history = [
            {
                "id": r["id"],
                "date": r["date_display"],
                "residues": r["residues"],
                "temp": r["temperature"],
                "humidity": r["humidity"],
                "status": r["status"]
            }
            for r in readings_rows
        ]
        # Ordena histórico cronologicamente (mais antigo primeiro)
        from datetime import datetime as _dt
        # Helper to parse dates that may include a time component (e.g., "18/09 14:54")
        def _parse_date(date_str: str) -> _dt:
            for fmt in ("%d/%m %H:%M", "%d/%m"):
                try:
                    return _dt.strptime(date_str, fmt)
                except ValueError:
                    continue
            # If parsing fails, return a minimal datetime to keep ordering stable
            return _dt.min
        history.sort(key=lambda x: _parse_date(x["date"]))

        if history:
            current = history[0]
            processed_today = current["residues"]
            temp = current["temp"]
            humidity = current["humidity"]
            status = current["status"]
        else:
            processed_today = 0.0
            temp = 25.0
            humidity = 50.0
            status = "Normal"

        modules_dict[mod_id] = {
            "id": mod_id,
            "name": row["name"],
            "location": row["location"],
            "total_capacity": row["total_capacity"],
            "processed_today": processed_today,
            "temperature": temp,
            "humidity": humidity,
            "status": status,
            "history": history
        }

    conn.close()
    return modules_dict

def insert_reading(module_id, residues, temp, humidity, date_display=None):
    """Insere nova medição/leitura no banco de dados SQLite."""
    conn = get_db()
    cursor = conn.cursor()

    if not date_display:
        date_display = datetime.now().strftime("%d/%m")

    status = calculate_status(temp, humidity)

    cursor.execute("""
        INSERT INTO readings (module_id, date_display, residues, temperature, humidity, status)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (module_id, date_display, residues, temp, humidity, status))

    conn.commit()
    new_id = cursor.lastrowid
    conn.close()
    return new_id, status

def update_reading(reading_id, residues, temp, humidity, date_display):
    """Edita uma leitura existente no banco de dados."""
    conn = get_db()
    cursor = conn.cursor()
    status = calculate_status(temp, humidity)
    cursor.execute("""
        UPDATE readings 
        SET residues = ?, temperature = ?, humidity = ?, date_display = ?, status = ?
        WHERE id = ?
    """, (residues, temp, humidity, date_display, status, reading_id))
    conn.commit()
    conn.close()

def delete_reading(reading_id):
    """Remove uma leitura específica do histórico."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM readings WHERE id = ?", (reading_id,))
    conn.commit()
    conn.close()

def create_module(module_id, name, location, capacity=20.0):
    """Cadastra um novo módulo de recicladora/composteira no SQLite."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO modules (id, name, location, total_capacity)
        VALUES (?, ?, ?, ?)
    """, (module_id, name, location, capacity))
    conn.commit()
    conn.close()

def update_module(old_id, new_id, name, location, capacity):
    """Renomeia e edita as informações de um módulo/recicladora."""
    conn = get_db()
    cursor = conn.cursor()
    
    # Se o ID foi alterado, atualizar também as leituras vinculadas
    if old_id != new_id:
        cursor.execute("UPDATE modules SET id = ?, name = ?, location = ?, total_capacity = ? WHERE id = ?",
                       (new_id, name, location, capacity, old_id))
        cursor.execute("UPDATE readings SET module_id = ? WHERE module_id = ?", (new_id, old_id))
    else:
        cursor.execute("UPDATE modules SET name = ?, location = ?, total_capacity = ? WHERE id = ?",
                       (name, location, capacity, old_id))
        
    conn.commit()
    conn.close()

def delete_module(module_id):
    """Exclui um módulo e todos os seus históricos associados."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM readings WHERE module_id = ?", (module_id,))
    cursor.execute("DELETE FROM modules WHERE id = ?", (module_id,))
    conn.commit()
    conn.close()

def get_total_processed():
    """Calcula a soma total de resíduos processados gravados no banco de dados."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT SUM(residues) as total FROM readings")
    total = cursor.fetchone()["total"]
    conn.close()
    return round(total, 1) if total else 0.0
