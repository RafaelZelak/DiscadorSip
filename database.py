# -*- coding: utf-8 -*-
# database.py

import sqlite3

DB_PATH = "config.db"

def initialize_db():
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS sip_config (
            id INTEGER PRIMARY KEY,
            sip_server TEXT NOT NULL,
            username TEXT NOT NULL,
            extension TEXT NOT NULL,
            password TEXT NOT NULL,
            name TEXT DEFAULT NULL
        )
        """)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS atendimentos (
            id INTEGER PRIMARY KEY,
            Atendido BOOLEAN,
            Numero TEXT,
            inicio_ligacao DATETIME,
            fim_ligacao DATETIME,
        )
        """)
        conn.commit()
        cursor.execute("SELECT COUNT(*) FROM sip_config")
        if cursor.fetchone()[0] == 0:
            # Valores padrão
            name = "Null"  # Alteração aqui
            SIP_SERVER = "Null"
            USERNAME = "Null"
            EXTENSION = "Null"
            PASSWORD = "Null"
            cursor.execute("""
            INSERT INTO sip_config (name, sip_server, username, extension, password) 
            VALUES (?, ?, ?, ?, ?)
            """, (name, SIP_SERVER, USERNAME, EXTENSION, PASSWORD))
        conn.commit()
        
def save_config(name, sip_server, username, extension, password, selected_user):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("""
        UPDATE sip_config SET name=?, sip_server=?, username=?, extension=?, password=?
        WHERE username=?
        """, (name, sip_server, username, extension, password, selected_user))
        conn.commit()

def load_config():
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT sip_server, username, extension, password FROM sip_config LIMIT 1")
        result = cursor.fetchone()
        return result if result else None


def load_users():
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT username FROM sip_config")
        return cursor.fetchall()

def load_config_by_user(username):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT name, sip_server, username, extension, password FROM sip_config WHERE username=?", (username,))
        return cursor.fetchone()

initialize_db()
