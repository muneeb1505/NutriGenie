import sqlite3
import bcrypt
import streamlit as st

# Initialize Database
def init_db():
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()

    # Create users table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        email TEXT UNIQUE,
        password TEXT
    )
    """)

    # Create searches table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS searches (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        feature TEXT,
        query TEXT,
        response TEXT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(user_id) REFERENCES users(id)
    )
    """)

    conn.commit()
    conn.close()

# def init_db():
#     conn = sqlite3.connect("users.db")
#     cursor = conn.cursor()

#     # Create users table
#     cursor.execute("""
#     CREATE TABLE IF NOT EXISTS users (
#         id INTEGER PRIMARY KEY AUTOINCREMENT,
#         username TEXT UNIQUE,
#         email TEXT UNIQUE,
#         password TEXT
#     )
#     """)

#     # Create searches table
#     cursor.execute("""
#     CREATE TABLE IF NOT EXISTS searches (
#         id INTEGER PRIMARY KEY AUTOINCREMENT,
#         user_id INTEGER,
#         query TEXT,
#         response TEXT,
#         timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
#         FOREIGN KEY(user_id) REFERENCES users(id)
#     )
#     """)

#     conn.commit()
#     conn.close()


# Register User
def register_user(username, email, password):
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()

    # Check if user exists
    cursor.execute("SELECT * FROM users WHERE email=?", (email,))
    if cursor.fetchone():
        return "User already exists!"

    # Hash password
    hashed_password = bcrypt.hashpw(password.encode(), bcrypt.gensalt())

    # Insert user
    cursor.execute("INSERT INTO users (username, email, password) VALUES (?, ?, ?)", 
    (username, email, hashed_password))
    conn.commit()
    conn.close()
    return "User registered successfully!"

# Authenticate User
def login_user(email, password):
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()

    # Fetch user data
    cursor.execute("SELECT id, username, password FROM users WHERE email=?", (email,))
    user = cursor.fetchone()
    conn.close()

    if user and bcrypt.checkpw(password.encode(), user[2]):
        return {"id": user[0], "username": user[1]}  # Return user info
    return None  # Invalid login

# Save Search
# def save_search(user_id, query, response):
#     conn = sqlite3.connect("users.db")
#     cursor = conn.cursor()
#     cursor.execute("INSERT INTO searches (user_id, query, response) VALUES (?, ?, ?)", (user_id, query, response))
#     conn.commit()
#     conn.close()
def save_search(user_id, feature, query, response):
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO searches (user_id, feature, query, response) VALUES (?, ?, ?, ?)", 
    (user_id, feature, query, response))
    conn.commit()
    conn.close()


# Retrieve Previous Searches
# @st.cache_data
# def get_previous_searches(user_id):
#     conn = sqlite3.connect("users.db")
#     cursor = conn.cursor()
#     cursor.execute("SELECT id, query, response FROM searches WHERE user_id=? ORDER BY timestamp DESC LIMIT 10", (user_id,))
#     rows = cursor.fetchall()
#     conn.close()
#     return rows

def get_previous_searches(user_id, feature):
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, query, response FROM searches WHERE user_id=? AND feature=? ORDER BY timestamp DESC LIMIT 10", 
    (user_id, feature))
    rows = cursor.fetchall()
    conn.close()
    return rows


def delete_search(search_id):
    """Deletes a specific search from the database."""
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM searches WHERE id=?", (search_id,))
    conn.commit()
    conn.close()