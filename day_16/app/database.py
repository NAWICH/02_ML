import sqlite3
from datetime import datetime
def create_connection():
    """create datbase connection"""
    connection = sqlite3.connect("./database.db")
    connection.row_factory = sqlite3.Row
    return connection

def create_table():
    """Create database.tables"""
    connection = create_connection()
    cursor = connection.cursor()
    cursor.execute("""CREATE TABLE IF NOT EXISTS users (
                   id INTEGER PRIMARY KEY AUTOINCREMENT,
                   fullname TEXT NOT NULL,
                   email TEXT UNIQUE NOT NULL,
                   password_hash TEXT NOT NULL,
                   is_premium BOOL DEFAULT 0,
                   created_at TEXT NOT NULL)""")
    
    cursor.execute("""CREATE TABLE IF NOT EXISTS question(
                   id TEXT PRIMARY KEY,
                   subject TEXT NOT NULL,
                   difficulty TEXT NOT NULL,
                   question_text TEXT NOT NULL,
                   option_a TEXT NOT NULL,
                   option_b TEXT NOT NULL,
                   option_c TEXT NOT NULL,
                   option_d TEXT NOT NULL,
                   correct_option TEXT NOT NULL,
                   explanation TEXT NOT NULL,
                   created_at TEXT NOT NULL
                   )""")
    cursor.execute("""CREATE TABLE IF NOT EXISTS
                   user_attempts (
                   id INTEGER PRIMARY KEY AUTOINCREMENT,
                   user_id INTEGER NOT NULL,
                   question_id TEXT NOT NULL,
                   selected_option TEXT NOT NULL,
                   is_correct INTEGER NOT NULL,    
                   attempted_at TEXT NOT NULL,
                   FOREIGN KEY (user_id) REFERENCES users(id),
                   FOREIGN KEY (question_id) REFERENCES questions(id)
                   )""")
    connection.commit()
    connection.close()

def create_user(full_name:str, email:str, password_hash:str) -> dict:
    """save a new user"""
    try:
        connection = create_connection()
        cursor = connection.cursor()
        time = datetime.now().isoformat()
        cursor.execute("INSERT INTO users(fullname,email, password_hash, is_premium, created_at) VALUES(?,?,?,?,?)", (full_name, email, password_hash, 0, time))
        new_user = {
            "full_name":full_name,
            "email": email,
            "created_at": time
        }
        connection.commit()
        connection.close()
        return new_user
    
    except sqlite3.Error as e:
        print(f"Error in creating user : {e}")
        return None
    
def find_user_by_email(email:str) -> dict:
    """search for email in database"""
    try:
        connection = create_connection()
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM users WHERE email=?", (email,))
        row = cursor.fetchone()
        connection.close()

        if row:
            return dict(row)
        return None
    
    except sqlite3.Error as e:
        print(f"couldn't find the user: {e}")
        return None
    
def upgrade_to_premium(user_id) -> bool:
    """upgrate the user for premimum"""
    try:
        connection = create_connection()
        cursor = connection.cursor()
        cursor.execute("UPDATE users SET is_premium = 1 WHERE id=?", (user_id,))
        connection.commit()
        connection.close()
        return True
    except sqlite3.Error as e:
        print(f"error upgrading to premuim: {e}")
        return False
    
def save_question(question_dict: dict):
    """save question so it will not be repeated"""
    try:
        connection = create_connection()
        cursor = connection.cursor()
        cursor.execute("""INSERT INTO question(id, subject, difficulty, question_text,option_a, option_b, option_c, option_d, correct_option, explanation, created_at)""", (question_dict['id'], question_dict['subject'], question_dict['difficulty'], question_dict['question_text'], question_dict['option_a'], question_dict['option_b'], question_dict['option_c'],question_dict['option_d'], question_dict['correct_option'], question_dict['explanation'], question_dict['created_at']))
        connection.commit()
        connection.close()

        return question_dict['id']

    except sqlite3.Error as e:
        print(f"Error saving question: {e}")
        return None
    
def get_question_by_id(question_id):
    try:
        connection = create_connection()
        cursor = connection.cursor()
        cursor.execute("""Select * from question where id=?""", (question_id, ))
        row = cursor.fetchone()
        connection.close()

        if row:
            return row
        return None
    except sqlite3.Error as e:
        print(f"Error searching for questioin: {e}")
        return None
    
def get_all_question_ids() -> list:
    try:
        connection= create_connection()
        cursor = connection.cursor()
        cursor.execute("""SELECT id FROM question""")
        rows = cursor.fetchall()
        connection.close()

        return [row['id'] for row in rows]
    except sqlite3.Error as e:
        print(f"Error in getting all question: {e}")
        return []
    
def get_question_by_subject(subject) -> list:
    try:    
        connection = create_connection()
        cursor = connection.cursor()
        cursor.execute("""SELECT * FROM question WHERE subject=?""", (subject,))
        questions = cursor.fetchall()
        connection.close()

        return questions
    except sqlite3.Error as e:
        print("Error getting question by subject: {e}")
        return []
    
def save_attempt(user_id, question_id, selected, is_correct) -> dict:
    try:
        connection = create_connection()
        cursor = connection.cursor()
        cursor.execute("""INSERT INTO user_attempts(
                       user_id, question_id, selected_option, is_correct, attempted_at) VALUES(?,?,?,?,?)""",
                       (user_id, question_id, selected, is_correct, datetime.now().isoformat()))
        attempt = {
            "question_id": question_id,
            "selected": selected,
            "is_correct": is_correct
        }
        connection.commit()
        connection.close()

        return attempt
    except sqlite3.Error as e:
        print(f"Error saving attemp: {e}")
        return None
    
def get_user_attempts(user_id: int) -> list:
    try:
        connection = create_connection()
        cursor = connection.cursor()
        cursor.execute("""SELECT * FROM user_attempts WHERE user_id=?""", (user_id,))
        data = cursor.fetchall()
        connection.close()

        return data
    except sqlite3.Error as e:
        print(f"Error getting user attemted data : {e}")
        return []
    
def get_user_stats(user_id: int) -> list:
    try:
        connection = create_connection()
        cursor = connection.cursor()
        cursor.execute("""SELECT question_id,selected_option, is_correct, attempted_at FROM user_attempts WHERE user_id=?""", (user_id,))
        rows = cursor.fetchall()
        connection.close()

        return [dict(row) for row in rows]
    
    except sqlite3.Error as e:
        print(f"Error getting user stats")
        return []
    
def get_user_attempted_question_ids(user_id) -> list:
    try:
        connection = create_connection()
        cursor = connection.cursor()
        cursor.execute("""SELECT question_id FROM user_attempts where user_id=?""", (user_id, ))
        question_id = cursor.fetchall()
        connection.close()

        return question_id
    except sqlite3.Error as e:
        print(f"Error getting attempted question ids: {e}")
        return []
    
create_table()