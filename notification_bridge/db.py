"""Работа с SQLite: подключение, создание таблицы, тестовые данные."""
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "database.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS notifications (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    message           TEXT NOT NULL,
    notification_type TEXT NOT NULL CHECK (notification_type IN ('Email', 'SMS', 'Telegram')),
    priority          TEXT NOT NULL CHECK (priority IN ('Normal', 'Important', 'Emergency')),
    created_at        TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
);
"""

SEED = [
    ("Завтра лекция по базам данных переносится в аудиторию 214.", "Email", "Normal"),
    ("Крайний срок сдачи лабораторной работы - пятница, 18:00.", "Telegram", "Important"),
    ("Эвакуация: покиньте корпус B через ближайший выход.", "SMS", "Emergency"),
    ("В библиотеке появились новые учебники по Python.", "Telegram", "Normal"),
]


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(with_seed=True):
    conn = get_db()
    conn.executescript(SCHEMA)
    count = conn.execute("SELECT COUNT(*) FROM notifications").fetchone()[0]
    if with_seed and count == 0:
        conn.executemany(
            "INSERT INTO notifications (message, notification_type, priority) VALUES (?, ?, ?)",
            SEED,
        )
    conn.commit()
    conn.close()
