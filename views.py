# views.py
# This file contains the Flask route handlers and associated logic for rendering templates and handling form submissions.

from flask import Flask, render_template, request, redirect, url_for
from database import get_db_connection
import re
import os

app = Flask(__name__)

@app.context_processor
def inject_boards():
    conn = get_db_connection()
    boards = conn.execute('SELECT * FROM boards').fetchall()
    conn.close()
    return {'boards': boards}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/faq')
def faq():
    return render_template('faq.html')

def process_post_content(content, current_board):
    # Convert `>` to green text
    content = re.sub(r'^>(.*)', r'<span class="green-text">\1</span>', content, flags=re.MULTILINE)
    
    # Hotlink `>>` references to posts on the same board
    content = re.sub(r'>>(\d+)', r'<a href="/{}/post/\1">>>\1</a>'.format(current_board), content)
    
    # Hotlink `>>>` cross-board references
    content = re.sub(r'>>>/(\w+)/(\d+)', r'<a href="/\1/post/\2">>>>\1/\2</a>', content)
    
    # Hotlink `>>>` board references
    content = re.sub(r'>>>/(\w+)/?', r'<a href="/\1">>>>\1</a>', content)
    
    return content

@app.route('/<board_name>/')
def board(board_name):
    conn = get_db_connection()
    board = conn.execute('SELECT * FROM boards WHERE name = ?', (board_name,)).fetchone()
    if board is None:
        return "Board not found", 404
    board_id = board['id']
    posts = conn.execute('SELECT * FROM posts_comments WHERE board_id = ? AND parent_id IS NULL ORDER BY last_activity DESC', (board_id,)).fetchall()
    conn.close()
    return render_template('board.html', board_id=board_id, board_name=board_name, posts=posts)

@app.route('/<board_name>/post/<int:post_id>')
def post(board_name, post_id):
    conn = get_db_connection()
    board = conn.execute('SELECT * FROM boards WHERE name = ?', (board_name,)).fetchone()
    if board is None:
        return "Board not found", 404
    post = conn.execute('SELECT * FROM posts_comments WHERE id = ? AND board_id = ? AND parent_id IS NULL', (post_id, board['id'])).fetchone()
    if post is None:
        return "Post not found", 404
    comments = conn.execute('SELECT * FROM posts_comments WHERE parent_id = ? AND board_id = ? ORDER BY id ASC', (post_id, board['id'])).fetchall()
    conn.close()
    return render_template('post.html', post=post, comments=comments, board_name=board_name)

def get_next_id_for_board(board_id):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('SELECT last_id FROM boards WHERE id = ?', (board_id,))
    last_id = c.fetchone()[0]
    new_id = last_id + 1
    c.execute('UPDATE boards SET last_id = ? WHERE id = ?', (new_id, board_id))
    conn.commit()
    conn.close()
    return new_id

@app.route('/<board_name>/add_post', methods=['POST'])
def add_post(board_name):
    title = request.form.get('title')
    content = request.form['content']
    processed_content = process_post_content(content, board_name)
    conn = get_db_connection()
    board = conn.execute('SELECT * FROM boards WHERE name = ?', (board_name,)).fetchone()
    if board is None:
        conn.close()
        return "Board not found", 404
    board_id = board['id']
    new_id = get_next_id_for_board(board_id)
    conn.execute('INSERT INTO posts_comments (id, board_id, parent_id, title, content, last_activity) VALUES (?, ?, NULL, ?, ?, CURRENT_TIMESTAMP)', 
                 (new_id, board_id, title, processed_content))
    conn.commit()
    conn.close()
    return redirect(url_for('board', board_name=board_name))

@app.route('/<board_name>/post/<int:post_id>/add_comment', methods=['POST'])
def add_comment(board_name, post_id):
    content = request.form['content']
    processed_content = process_post_content(content, board_name)
    conn = get_db_connection()
    board = conn.execute('SELECT * FROM boards WHERE name = ?', (board_name,)).fetchone()
    if board is None:
        return "Board not found", 404
    post = conn.execute('SELECT * FROM posts_comments WHERE id = ? AND board_id = ? AND parent_id IS NULL', (post_id, board['id'])).fetchone()
    if post is None:
        return "Post not found", 404
    new_id = get_next_id_for_board(board['id'])
    conn.execute('INSERT INTO posts_comments (id, board_id, parent_id, content, last_activity) VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)', 
                 (new_id, board['id'], post_id, processed_content))
    conn.execute('UPDATE posts_comments SET last_activity = CURRENT_TIMESTAMP WHERE id = ? AND board_id = ?', (post_id, board['id']))
    conn.commit()
    conn.close()
    return redirect(url_for('post', board_name=board_name, post_id=post_id))
