import json
import sqlite3

import settings
from settings import ApiError


def execute_sql(statement, parameters=()):
    # Run one SQL statement and return its rows and last inserted id
    connection = sqlite3.connect(settings.DB_PATH)
    connection.row_factory = sqlite3.Row
    try:
        connection.execute(
            """CREATE TABLE IF NOT EXISTS searches(
            id INTEGER PRIMARY KEY AUTOINCREMENT, query TEXT, name TEXT, lat REAL, lon REAL,
            start_date TEXT, end_date TEXT, temps TEXT, note TEXT DEFAULT '', created_at TEXT)"""
        )
        cursor = connection.execute(statement, parameters)
        rows = cursor.fetchall()
        connection.commit()
        return rows, cursor.lastrowid
    finally:
        connection.close()


def search_record_from_row(row):
    record = dict(row)
    record["temps"] = json.loads(record["temps"])
    return record


def get_search_record(search_id):
    rows, _ = execute_sql("SELECT * FROM searches WHERE id=?", (search_id,))
    if not rows:
        raise ApiError("Record not found.", 404)
    return search_record_from_row(rows[0])
