import sqlite3
class Connection:
    def __init__(self):
        self.conn = None
        self.cursor = None
    
    def open_connection(self):
        self.conn = sqlite3.connect(f'shared/users.db')
        self.cursor = self.conn.cursor()
    
    def close_connection(self):
        self.conn.close()
    
    def commit_connection(self):
        self.conn.commit()
    
    def fetchall(self):
        return self.cursor.fetchall()
        

# def connection_database():
#     connection = sqlite3.connect(f'users.db')
#     cursor = connection.cursor()
#     return cursor


def insert(name_table, name_column_req, questions, query):
    db = Connection()
    db.open_connection()
    db.cursor.execute(f"INSERT INTO {name_table} ({name_column_req}) VALUES ({questions})", query)
    db.commit_connection()
    db.close_connection()
    
def update(name_table, name_column_req, name_search_value, query):
    db = Connection()
    db.open_connection()
    db.cursor.execute(f"UPDATE {name_table} SET {name_column_req} WHERE {name_search_value} = ?", query)
    db.commit_connection()
    db.close_connection()

def select(name_table, name_column_req, name_search_value, query):
    db = Connection()
    db.open_connection()
    db.cursor.execute(f"SELECT {name_column_req} FROM {name_table} WHERE {name_search_value} = ?", query)
    data = db.fetchall()
    db.close_connection()
    return data

def select_without_where(name_table, name_column_req):
    db = Connection()
    db.open_connection()
    db.cursor.execute(f"SELECT {name_column_req} FROM {name_table} ")
    data = db.fetchall()
    db.close_connection()
    return data

def select_all(name_table):
    db = Connection()
    db.open_connection()
    db.cursor.execute(f"SELECT * FROM {name_table}")
    data = db.fetchall()
    db.close_connection()
    return data
    
def delete(name_table, name_search_value, query):
    db = Connection()
    db.open_connection()
    db.cursor.execute(f"DELETE FROM {name_table} WHERE {name_search_value} = ?", query)
    db.commit_connection()
    db.close_connection()

def delete_without_where(name_table):
    db = Connection()
    db.open_connection()
    db.cursor.execute(f"DELETE FROM {name_table}")
    db.commit_connection()
    db.close_connection()