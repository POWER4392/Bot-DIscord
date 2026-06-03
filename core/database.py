import os
import sqlite3
import psycopg2
from psycopg2 import pool
from core.shared import db_lock, DB_URL, USE_PG

if USE_PG:
    db_pool = psycopg2.pool.SimpleConnectionPool(1, 10, DB_URL)
    
    class CloudDBCursor:
        def __init__(self):
            self.description = None
            self.rowcount = 0
            self._last_result = None
            
        def execute(self, query, params=()):
            query = query.replace("?", "%s")
            query = query.replace("INTEGER PRIMARY KEY AUTOINCREMENT", "SERIAL PRIMARY KEY")
            query = query.replace("REAL", "DOUBLE PRECISION")
            
            if "INSERT OR REPLACE INTO warnings" in query:
                query = "INSERT INTO warnings (guild_id, user_id, warn_count) VALUES (%s, %s, %s) ON CONFLICT (guild_id, user_id) DO UPDATE SET warn_count = EXCLUDED.warn_count"
            elif "INSERT OR REPLACE INTO timed_roles" in query:
                query = "INSERT INTO timed_roles (guild_id, user_id, role_id, expires_at) VALUES (%s, %s, %s, %s) ON CONFLICT (guild_id, user_id, role_id) DO UPDATE SET expires_at = EXCLUDED.expires_at"
            elif "INSERT OR REPLACE INTO social_tracker" in query:
                query = "INSERT INTO social_tracker (guild_id, platform, target_id, channel_id, ping_role, last_post_id) VALUES (%s, %s, %s, %s, %s, %s) ON CONFLICT (guild_id, platform, target_id) DO UPDATE SET channel_id=EXCLUDED.channel_id, ping_role=EXCLUDED.ping_role, last_post_id=EXCLUDED.last_post_id"
            elif "INSERT OR IGNORE INTO blacklists" in query:
                query = "INSERT INTO blacklists (guild_id, word) VALUES (%s, %s) ON CONFLICT (guild_id, word) DO NOTHING"
            
            pg_conn = db_pool.getconn()
            try:
                with pg_conn.cursor() as cur:
                    cur.execute(query, params)
                    self.description = cur.description
                    self.rowcount = cur.rowcount
                    try:
                        self._last_result = cur.fetchall()
                    except:
                        self._last_result = None
                    pg_conn.commit()
            except Exception as e:
                pg_conn.rollback()
                raise e
            finally:
                db_pool.putconn(pg_conn)
                
        def fetchall(self):
            return self._last_result or []
            
        def fetchone(self):
            return self._last_result[0] if self._last_result else None
            
        def executemany(self, query, params_list):
            query = query.replace("?", "%s")
            pg_conn = db_pool.getconn()
            try:
                with pg_conn.cursor() as cur:
                    cur.executemany(query, params_list)
                    pg_conn.commit()
            except Exception as e:
                pg_conn.rollback()
                raise e
            finally:
                db_pool.putconn(pg_conn)

    class CloudDBConn:
        def commit(self): pass
        def close(self): pass

    conn = CloudDBConn()
    cursor = CloudDBCursor()
else:
    os.makedirs("databases", exist_ok=True)
    from core.shared import config
    db_name = config.get("database_name", "bot_core")
    conn = sqlite3.connect(f"databases/{db_name}.db", check_same_thread=False)
    cursor = conn.cursor()

# Initialize tables
cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                    guild_id TEXT, user_id TEXT,
                    xp INTEGER, level INTEGER,
                    PRIMARY KEY (guild_id, user_id)
                )''')
cursor.execute('''CREATE TABLE IF NOT EXISTS social_tracker (
                    guild_id TEXT, platform TEXT, 
                    target_id TEXT, channel_id TEXT, 
                    ping_role TEXT, last_post_id TEXT,
                    PRIMARY KEY (guild_id, platform, target_id)
                )''')
cursor.execute('''CREATE TABLE IF NOT EXISTS warnings (
                    guild_id TEXT, user_id TEXT,
                    warn_count INTEGER,
                    PRIMARY KEY (guild_id, user_id)
                )''')
cursor.execute('''CREATE TABLE IF NOT EXISTS timed_roles (
                    guild_id TEXT, user_id TEXT, role_id TEXT,
                    expires_at REAL,
                    PRIMARY KEY (guild_id, user_id, role_id)
                )''')
cursor.execute('''CREATE TABLE IF NOT EXISTS reaction_panels (
                    message_id TEXT PRIMARY KEY,
                    guild_id TEXT,
                    roles_json TEXT
                )''')
cursor.execute('''CREATE TABLE IF NOT EXISTS gui_tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    action TEXT, payload TEXT
                )''')
cursor.execute('''CREATE TABLE IF NOT EXISTS blacklists (
                    guild_id TEXT, word TEXT,
                    PRIMARY KEY (guild_id, word)
                )''')
cursor.execute('''CREATE TABLE IF NOT EXISTS quiz_questions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    guild_id TEXT,
                    question TEXT,
                    option_a TEXT,
                    option_b TEXT,
                    option_c TEXT,
                    option_d TEXT,
                    correct_option TEXT
                )''')
conn.commit()

def db_get_user(guild_id, user_id):
    with db_lock:
        cursor.execute("SELECT xp, level FROM users WHERE guild_id=? AND user_id=?", (guild_id, user_id))
        row = cursor.fetchone()
        if not row:
            cursor.execute("INSERT INTO users (guild_id, user_id, xp, level) VALUES (?, ?, 0, 1)", (guild_id, user_id))
            conn.commit()
            return (0, 1)
        return row

def db_update_xp(guild_id, user_id, xp_add):
    with db_lock:
        cursor.execute("SELECT xp, level FROM users WHERE guild_id=? AND user_id=?", (guild_id, user_id))
        row = cursor.fetchone()
        if row:
            nxp, clvl = row[0] + xp_add, row[1]
            nlvl = max(1, int((nxp / 100) ** (1/1.5)))
            if nlvl < clvl: nlvl = clvl
            cursor.execute("UPDATE users SET xp=?, level=? WHERE guild_id=? AND user_id=?", (nxp, nlvl, guild_id, user_id))
            conn.commit()
            return clvl, nlvl
        return 1, 1
