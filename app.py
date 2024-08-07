# app.py
# This is the main Flask application file. It imports necessary modules, initializes the database, and starts the Flask server.

from flask import Flask
from database import init_db
from views import app

if __name__ == '__main__':
    init_db()  # Initialize or reset database
    app.run(debug=True)
