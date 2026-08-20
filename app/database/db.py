import sqlite3
import os
from flask import g, current_app
from app.config import Config

def get_db():
    if 'db' not in g:
        db_path = current_app.config.get('DATABASE_PATH', Config.DATABASE_PATH)
        g.db = sqlite3.connect(
            db_path,
            detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES,
            timeout=20.0
        )
        g.db.row_factory = sqlite3.Row
        g.db.execute('PRAGMA foreign_keys = ON;')
        g.db.execute('PRAGMA journal_mode = WAL;')
        g.db.execute('PRAGMA busy_timeout = 5000;')
        g.db.execute('PRAGMA synchronous = NORMAL;')
    return g.db


def close_db(e=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()

def query_db(query, args=(), one=False):
    cur = get_db().execute(query, args)
    rv = cur.fetchall()
    cur.close()
    return (rv[0] if rv else None) if one else rv

def execute_db(query, args=(), commit=True):
    db = get_db()
    cur = db.execute(query, args)
    last_id = cur.lastrowid
    cur.close()
    if commit:
        db.commit()
    return last_id

def init_db(app=None):
    from app.database.schema import create_schema, seed_initial_data
    if app:
        with app.app_context():
            create_schema()
            seed_initial_data()
    else:
        create_schema()
        seed_initial_data()
