import sqlite3
from pathlib import Path

SCHEMA = '''
CREATE TABLE IF NOT EXISTS jobs (
  id TEXT PRIMARY KEY,
  source_url TEXT NOT NULL,
  source_platform TEXT NOT NULL,
  status TEXT NOT NULL,
  progress_percent INTEGER NOT NULL,
  status_message TEXT NOT NULL,
  error_code TEXT,
  error_detail TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  completed_at TEXT
);
CREATE TABLE IF NOT EXISTS artifacts (
  id TEXT PRIMARY KEY,
  job_id TEXT NOT NULL,
  filename TEXT NOT NULL,
  format TEXT NOT NULL,
  size_bytes INTEGER NOT NULL,
  duration_seconds REAL NOT NULL,
  storage_path TEXT NOT NULL,
  download_token TEXT,
  created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS presets (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  trim_start_seconds REAL NOT NULL,
  trim_end_seconds REAL,
  metadata_json TEXT NOT NULL,
  created_at TEXT NOT NULL
);
'''

class SQLiteStore:
    def __init__(self, db_path: str):
        self.path = Path(db_path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(self.path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.bootstrap()

    def bootstrap(self) -> None:
        self.conn.executescript(SCHEMA)
        self.conn.commit()

    def execute(self, query: str, params: tuple = ()):
        cur = self.conn.execute(query, params)
        self.conn.commit()
        return cur

    def fetchone(self, query: str, params: tuple = ()):
        return self.conn.execute(query, params).fetchone()

    def fetchall(self, query: str, params: tuple = ()):
        return self.conn.execute(query, params).fetchall()
