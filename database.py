# database.py
# This file contains functions to initialize the database and get a database connection.

import sqlite3

def get_db_connection():
    conn = sqlite3.connect('forum.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    c = conn.cursor()
    # Create tables
    c.execute('''
        CREATE TABLE IF NOT EXISTS boards (
            id INTEGER PRIMARY KEY, 
            name TEXT,
            last_id INTEGER DEFAULT 0
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS posts_comments (
            id INTEGER, 
            board_id INTEGER, 
            parent_id INTEGER, 
            title TEXT, 
            content TEXT,
            last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (id, board_id),
            FOREIGN KEY (board_id) REFERENCES boards (id),
            FOREIGN KEY (parent_id) REFERENCES posts_comments (id)
        )
    ''')

    # Insert sample boards if the table is empty
    c.execute('SELECT COUNT(*) FROM boards')
    count = c.fetchone()[0]
    if count == 0:
        sample_boards = [
            (1, 'General', 0),
            (2, 'Games', 0),
            (3, 'Web of Trust', 0),
            (4, 'Metaverse', 0)
        ]
        c.executemany('INSERT INTO boards (id, name, last_id) VALUES (?, ?, ?)', sample_boards)
    
    conn.commit()
    conn.close()
