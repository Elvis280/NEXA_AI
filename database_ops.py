import mysql.connector as m
from mysql.connector import Error

def get_db_connection():
    connection = m.connect(
        host="localhost",
        user="root",
        password="dev@nsh28",
        database="todo_db"
    )
    return connection

def get_all_tasks():
    con = get_db_connection()
    if not con:
        return []

    try:
        cursor = con.cursor()
        cursor.execute("SELECT id, task_name FROM tasks ORDER BY id ASC;")
        return cursor.fetchall()  # returns [(1, 'task1'), (2, 'task2'), ...]
    except:
        return []
    finally:
        if cursor:
            cursor.close()
        if con:
            con.close()

def delete_task_by_position(position):
    tasks = get_all_tasks()
    if not tasks:
        return "Todo list is empty."
    if position > 0 and position <= len(tasks):
        task_id = tasks[position-1][0]
        return delete_from_list_by_id(task_id)
    else:
        return f"No task found at position {position}."

def delete_task_by_reverse_position(position):
    tasks = get_all_tasks()
    if not tasks:
        return "Todo list is empty."

    if position > 0 and position <= len(tasks):
        task_id = tasks[-position][0]  # negative index
        return delete_from_list_by_id(task_id)
    else:
        return f"No task found at position {position} from the end."


def delete_from_list_by_id(task_id):
    con = get_db_connection()
    if not con:
        return "Connection Failed to Database..."
    try:
        cursor = con.cursor()
        cursor.execute("DELETE FROM tasks WHERE id = %s;", (task_id,))
        con.commit()
        return "Task deleted successfully."
    except Error as e:
        return f"Error message: {e}"
    finally:
        if cursor:
            cursor.close()
        if con:
            con.close()




def insert_into_list(msg):
    con=get_db_connection()
    if con:
        try:
            cursor=con.cursor()
            cursor.execute("insert into tasks(task_name) values(%s)",(msg,))
            con.commit()
            return "Task updated successfully"
        except Error as e:
            return f"Error message : {e}"
        finally:
            if cursor:
                cursor.close()
            if con:
                con.close()
    else:
        return "Connection Failed to Database..."

def delete_from_list(id_db):
    con=get_db_connection()
    if con:
        try:
            cursor=con.cursor()
            cursor.execute("delete from tasks where id = %s;",(id_db,))
            con.commit()
            return "Task deleted successfully"
        except Error as e:
            return f"Error message : {e}"
        finally:
            if cursor:
                cursor.close()
            if con:
                con.close()
    else:
        return "Connection Failed to Database..."

def delete_from_list_by_name(task_name):
    con = get_db_connection()
    if not con:
        return "Connection Failed to Database..."
    try:
        cursor = con.cursor()
        cursor.execute("DELETE FROM tasks WHERE task_name = %s LIMIT 1;", (task_name,))
        con.commit()
        return "Task deleted successfully."
    except Error as e:
        return f"Error message: {e}"
    finally:
        if cursor:
            cursor.close()
        if con:
            con.close()

    
def display_list():
    con = get_db_connection()
    if con:
        try:
            cursor = con.cursor()
            cursor.execute("SELECT * FROM tasks;")
            response = cursor.fetchall()
            return response
        except Error as e:
            return f"Error message : {e}"
        finally:
            if cursor:
                cursor.close()
            if con:
                con.close()
    else:
        return "Connection Failed to Database..."

# Chat History Functions
def create_chat_table():
    """Create chat_history table if it doesn't exist"""
    con = get_db_connection()
    if not con:
        return False
    
    try:
        cursor = con.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS chat_history (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_query TEXT NOT NULL,
                nexa_response TEXT NOT NULL,
                action_type VARCHAR(50),
                action_taken TEXT,
                note TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        con.commit()
        return True
    except Error as e:
        print(f"Error creating chat table: {e}")
        return False
    finally:
        if cursor:
            cursor.close()
        if con:
            con.close()

def save_chat_conversation(user_query, nexa_response, action_type="chat", action_taken="", note=""):
    """Save a chat conversation to the database"""
    con = get_db_connection()
    if not con:
        return False
    
    try:
        cursor = con.cursor()
        cursor.execute("""
            INSERT INTO chat_history (user_query, Nexa_reponse, action_type, action_taken, note)
            VALUES (%s, %s, %s, %s, %s)
        """, (user_query, nexa_response, action_type, action_taken, note))
        con.commit()
        return True
    except Error as e:
        print(f"Error saving chat: {e}")
        return False
    finally:
        if cursor:
            cursor.close()
        if con:
            con.close()

def get_chat_history(limit=50, offset=0):
    con = get_db_connection()
    if not con:
        return []
    
    try:
        cursor = con.cursor()
        cursor.execute("""
            SELECT id, user_query, Nexa_reponse, action_type, action_taken, note, timestamp
            FROM chat_history 
            ORDER BY timestamp DESC 
            LIMIT %s OFFSET %s
        """, (limit, offset))
        return cursor.fetchall()
    except Error as e:
        print(f"Error fetching chat history: {e}")
        return []
    finally:
        if cursor:
            cursor.close()
        if con:
            con.close()

def get_chat_stats():
    """Get chat statistics"""
    con = get_db_connection()
    if not con:
        return {"total": 0, "today": 0, "this_week": 0, "this_month": 0}
    
    try:
        cursor = con.cursor()
        
        # Total conversations
        cursor.execute("SELECT COUNT(*) FROM chat_history")
        total = cursor.fetchone()[0]
        
        # Today's conversations
        cursor.execute("SELECT COUNT(*) FROM chat_history WHERE DATE(timestamp) = CURDATE()")
        today = cursor.fetchone()[0]
        
        # This week's conversations
        cursor.execute("SELECT COUNT(*) FROM chat_history WHERE timestamp >= DATE_SUB(NOW(), INTERVAL 7 DAY)")
        this_week = cursor.fetchone()[0]
        
        # This month's conversations
        cursor.execute("SELECT COUNT(*) FROM chat_history WHERE timestamp >= DATE_SUB(NOW(), INTERVAL 30 DAY)")
        this_month = cursor.fetchone()[0]
        
        return {
            "total": total,
            "today": today,
            "this_week": this_week,
            "this_month": this_month
        }
    except Error as e:
        print(f"Error fetching chat stats: {e}")
        return {"total": 0, "today": 0, "this_week": 0, "this_month": 0}
    finally:
        if cursor:
            cursor.close()
        if con:
            con.close()

def delete_chat_conversation(chat_id):
    con = get_db_connection()
    if not con:
        return False
    
    try:
        cursor = con.cursor()
        cursor.execute("DELETE FROM chat_history WHERE id = %s", (chat_id,))
        con.commit()
        return cursor.rowcount > 0
    except Error as e:
        print(f"Error deleting chat: {e}")
        return False
    finally:
        if cursor:
            cursor.close()
        if con:
            con.close()


def contact_info():
    pass