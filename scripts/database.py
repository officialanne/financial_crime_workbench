import sqlite3

from config import DATABASE_PATH

def get_connection():
    connection = sqlite3.connect(DATABASE_PATH)
    
    # enforce foreign-key constaints
    connection.execute("PRAGMA foreign_keys = ON;")
    
    return connection