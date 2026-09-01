import http.server
import socketserver
import json
import os
import re
import time
import urllib.parse
import sqlite3
from datetime import datetime

PORT = 8000
DB_PATH = os.path.join(os.path.dirname(__file__), 'data', 'database.db')

def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 1. Characters Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS characters (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            layer TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 2. Blueprints Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS blueprints (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            characters_json TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # 3. Blueprint Steps Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS blueprint_steps (
            id TEXT PRIMARY KEY,
            blueprint_id TEXT NOT NULL,
            step_order INTEGER NOT NULL,
            layer TEXT NOT NULL,
            character TEXT NOT NULL,
            title TEXT NOT NULL,
            description TEXT,
            evidence TEXT,
            pain_points TEXT,
            duration TEXT,
            time_unit TEXT,
            FOREIGN KEY (blueprint_id) REFERENCES blueprints(id) ON DELETE CASCADE
        )
    ''')

    # 4. Step Connections Table (Stores arrows pointing to target to_step_id)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS step_connections (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            blueprint_id TEXT NOT NULL,
            step_id TEXT NOT NULL,
            to_step_id TEXT NOT NULL,
            FOREIGN KEY (blueprint_id) REFERENCES blueprints(id) ON DELETE CASCADE
        )
    ''')

    conn.commit()
    conn.close()

def get_all_characters():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT name, layer FROM characters ORDER BY id ASC')
    rows = cursor.fetchall()
    conn.close()
    return [{"name": row[0], "layer": row[1]} for row in rows]

def save_character_to_db(name, layer):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('INSERT OR REPLACE INTO characters (name, layer) VALUES (?, ?)', (name, layer))
    conn.commit()
    conn.close()
    return {"name": name, "layer": layer}

def delete_character_from_db(name):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM characters WHERE name = ?', (name,))
    conn.commit()
    conn.close()

def get_all_blueprints():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT b.id, b.title, b.updated_at, COUNT(s.id) as step_count
        FROM blueprints b
        LEFT JOIN blueprint_steps s ON b.id = s.blueprint_id
        GROUP BY b.id
        ORDER BY b.updated_at DESC
    ''')
    rows = cursor.fetchall()
    conn.close()
    return [{
        'id': row[0],
        'title': row[1],
        'updatedAt': row[2],
        'stepCount': row[3]
    } for row in rows]

def get_blueprint_by_id(bp_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT id, title, characters_json, updated_at FROM blueprints WHERE id = ?', (bp_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return None
    
    chars_json = row[2]
    characters = json.loads(chars_json) if chars_json else []

    cursor.execute('''
        SELECT id, layer, character, title, description, evidence, pain_points, duration, time_unit
        FROM blueprint_steps
        WHERE blueprint_id = ?
        ORDER BY step_order ASC
    ''', (bp_id,))
    step_rows = cursor.fetchall()

    cursor.execute('''
        SELECT step_id, to_step_id
        FROM step_connections
        WHERE blueprint_id = ?
    ''', (bp_id,))
    conn_rows = cursor.fetchall()
    conn.close()

    connections_map = {}
    for s_id, to_id in conn_rows:
        if s_id not in connections_map:
            connections_map[s_id] = []
        connections_map[s_id].append(to_id)

    steps = [{
        'id': r[0],
        'layer': r[1],
        'character': r[2],
        'title': r[3],
        'description': r[4] or '',
        'evidence': r[5] or '',
        'painPoints': r[6] or '',
        'duration': r[7] or '',
        'timeUnit': r[8] or '',
        'to_step_id': connections_map.get(r[0], [''])[0] if connections_map.get(r[0]) else '',
        'toStepIds': connections_map.get(r[0], [])
    } for r in step_rows]

    return {
        'id': row[0],
        'title': row[1],
        'characters': characters,
        'steps': steps,
        'updatedAt': row[3]
    }

def save_blueprint_to_db(data):
    bp_id = data.get('id')
    if not bp_id:
        bp_id = f"bp_{int(datetime.now().timestamp() * 1000)}"
        data['id'] = bp_id

    title = data.get('title', '').strip()
    if not title:
        random_num = int(datetime.now().timestamp()) % 9000 + 1000
        title = f"Blueprint no. {random_num}"
        data['title'] = title

    updated_at = datetime.now().isoformat()
    data['updatedAt'] = updated_at

    chars_json = json.dumps(data.get('characters', []), ensure_ascii=False)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute('''
        INSERT OR REPLACE INTO blueprints (id, title, characters_json, updated_at)
        VALUES (?, ?, ?, ?)
    ''', (bp_id, title, chars_json, updated_at))

    cursor.execute('DELETE FROM blueprint_steps WHERE blueprint_id = ?', (bp_id,))
    cursor.execute('DELETE FROM step_connections WHERE blueprint_id = ?', (bp_id,))

    steps = data.get('steps', [])
    for idx, step in enumerate(steps):
        step_id = step.get('id', f"step_{idx}_{int(datetime.now().timestamp()*1000)}")
        cursor.execute('''
            INSERT OR REPLACE INTO blueprint_steps (id, blueprint_id, step_order, layer, character, title, description, evidence, pain_points, duration, time_unit)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            step_id,
            bp_id,
            idx,
            step.get('layer', ''),
            step.get('character', ''),
            step.get('title', ''),
            step.get('description', ''),
            step.get('evidence', ''),
            step.get('painPoints', ''),
            step.get('duration', ''),
            step.get('timeUnit', '')
        ))

        to_ids = []
        if step.get('to_step_id'):
            to_ids.append(step.get('to_step_id'))
        if step.get('toStepIds') and isinstance(step.get('toStepIds'), list):
            to_ids.extend(step.get('toStepIds'))

        for to_id in set(to_ids):
            if to_id:
                cursor.execute('''
                    INSERT OR IGNORE INTO step_connections (blueprint_id, step_id, to_step_id)
                    VALUES (?, ?, ?)
                ''', (bp_id, step_id, to_id))

    conn.commit()
    conn.close()
    return data

def delete_blueprint_from_db(bp_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM step_connections WHERE blueprint_id = ?', (bp_id,))
    cursor.execute('DELETE FROM blueprint_steps WHERE blueprint_id = ?', (bp_id,))
    cursor.execute('DELETE FROM blueprints WHERE id = ?', (bp_id,))
    conn.commit()
    conn.close()

class BlueprintHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
        self.send_header('Pragma', 'no-cache')
        self.send_header('Expires', '0')
        super().end_headers()

    def send_json(self, data, status=200):
        body = json.dumps(data, ensure_ascii=False).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_GET(self):
        parsed_url = urllib.parse.urlparse(self.path)
        path = parsed_url.path

        if path in ['/', '/index.html']:
            file_path = os.path.join(os.path.dirname(__file__), 'index.html')
            if os.path.exists(file_path):
                with open(file_path, 'rb') as f:
                    content = f.read()
                self.send_response(200)
                self.send_header('Content-Type', 'text/html; charset=utf-8')
                self.send_header('Content-Length', str(len(content)))
                self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
                self.send_header('Pragma', 'no-cache')
                self.send_header('Expires', '0')
                self.end_headers()
                self.wfile.write(content)
                return

        if path == '/api/characters':
            chars = get_all_characters()
            self.send_json(chars)
            return

        if path == '/api/blueprints':
            blueprints_list = get_all_blueprints()
            self.send_json(blueprints_list)
            return

        match = re.match(r'^/api/blueprints/([a-zA-Z0-9_-]+)$', path)
        if match:
            bp_id = match.group(1)
            bp_data = get_blueprint_by_id(bp_id)
            if bp_data:
                self.send_json(bp_data)
                return
            else:
                self.send_json({'error': 'Blueprint not found'}, 404)
                return

        super().do_GET()

    def do_POST(self):
        parsed_url = urllib.parse.urlparse(self.path)
        path = parsed_url.path

        if path == '/api/characters':
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            try:
                data = json.loads(post_data.decode('utf-8'))
                name = data.get('name', '').strip()
                layer = data.get('layer', 'Customer Actions').strip()
                if not name:
                    self.send_json({'error': 'Name is required'}, 400)
                    return
                saved_char = save_character_to_db(name, layer)
                self.send_json({'success': True, 'character': saved_char})
                return
            except Exception as e:
                self.send_json({'error': str(e)}, 500)
                return

        if path == '/api/blueprints':
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)

            try:
                data = json.loads(post_data.decode('utf-8'))
                saved_data = save_blueprint_to_db(data)
                self.send_json({
                    'success': True,
                    'id': saved_data['id'],
                    'title': saved_data['title'],
                    'blueprint': saved_data
                })
                return
            except Exception as e:
                import traceback
                traceback.print_exc()
                self.send_json({'error': str(e)}, 400)
                return

        self.send_json({'error': 'Endpoint not found'}, 404)

    def do_DELETE(self):
        parsed_url = urllib.parse.urlparse(self.path)
        path = parsed_url.path

        if path == '/api/characters':
            query = urllib.parse.parse_qs(parsed_url.query)
            char_name = query.get('name', [''])[0].strip()
            if char_name:
                delete_character_from_db(char_name)
                self.send_json({'success': True, 'name': char_name})
                return
            self.send_json({'error': 'Character name required'}, 400)
            return

        match = re.match(r'^/api/blueprints/([a-zA-Z0-9_-]+)$', path)
        if match:
            bp_id = match.group(1)
            delete_blueprint_from_db(bp_id)
            self.send_json({'success': True, 'id': bp_id})
            return

        self.send_json({'error': 'Endpoint not found'}, 404)

if __name__ == "__main__":
    os.chdir(os.path.dirname(__file__))
    init_db()
    for attempt in range(5):
        try:
            with http.server.ThreadingHTTPServer(("", PORT), BlueprintHandler) as httpd:
                print(f"Serving Blueprint DXO on http://localhost:{PORT}")
                httpd.serve_forever()
                break
        except Exception as e:
            print(f"Port {PORT} retry {attempt+1}/5: {e}")
            time.sleep(1)
