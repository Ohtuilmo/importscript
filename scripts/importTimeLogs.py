from db_connection import get_db_connection, close_db_connection
import csv
from datetime import datetime, timezone
import psycopg2
from pathlib import Path

TIMELOGS_DATA_PATH = "/tmp/timelogs_data"

def convert_hours_to_minutes(hours_str):
    try:
        hours_float = float(hours_str.replace(',', '.'))
        return int(hours_float * 60), None
    except ValueError:
        return None, f"Invalid hour format: {hours_str}"

def validate_and_format_date(date_str):
    try:
        return datetime.strptime(date_str, '%Y-%m-%d'), None
    except ValueError:
        return None, f"Invalid date format: {date_str}"
    
def convert_sprint_to_int(sprint_str):
    try:
        return int(sprint_str), None
    except ValueError:
        return None, f"Invalid sprint format: {sprint_str}"


def fetch_group_id(student_number):
    if not student_number:
        return None, "Student number is empty"
    try:
        conn, cur = get_db_connection()
        query = "SELECT group_id FROM group_students WHERE user_student_number = %s"
        cur.execute(query, (student_number,))
        result = cur.fetchone()
        if result:
            return result[0], None
        else:
            return None, f"Group ID not found for student number {student_number}"
    except psycopg2.Error as e:
        return None, f"Error fetching the group ID: {e}"
    finally:
        close_db_connection(conn, cur)

def fetch_sprint_id(group_id, sprint):

    """Fetch the sprint ID from the 'sprints' table based on the given group ID and start date."""

    conn, cur = get_db_connection()
    if conn is None or cur is None:
        return None, "Database connection error"
    
    try:
        query = "SELECT id FROM sprints WHERE group_id = %s AND sprint = %s"
        cur.execute(query, (group_id, sprint))
        result = cur.fetchone()
        if result:
            return result[0], None
        else:
            return None, "Sprint not found with the provided group ID and sprint number"
    except psycopg2.Error as e:
        return None, f"Error fetching the sprint ID: {e}"
    finally:
        close_db_connection(conn, cur)

def check_if_row_exists(date, minutes, description, student_number, sprint_id):
    conn, cur = get_db_connection()
    query = """
    SELECT EXISTS (
        SELECT 1 FROM time_logs
        WHERE date = %s AND minutes = %s AND description = %s AND student_number = %s AND sprint_id = %s
    )
    """
    cur.execute(query, (date, minutes, description, student_number, sprint_id))
    result = cur.fetchone()
    return result[0]


def add_time_log(date, minutes, description, student_number, sprint_id):

    """Add a new time log entry to the 'time_logs' table. Returns a tuple (success, error_message)"""
    
    conn, cur = get_db_connection()  
    created_at = datetime.now(timezone.utc)
    updated_at = datetime.now(timezone.utc)

    if check_if_row_exists(date, minutes, description, student_number, sprint_id):
        return False, "Timelog already exists in the database"

    try:
        query = """
        INSERT INTO time_logs (date, minutes, description, student_number, sprint_id, created_at, updated_at) 
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        cur.execute(query, (date, minutes, description, student_number, sprint_id, created_at, updated_at))
        conn.commit()
        return True, None
    except psycopg2.Error as e:
        return False, f"Error adding time log to the database: {e}"
    finally:
        close_db_connection(conn, cur)


def process_file(filepath):
    with open(filepath, mode='r', encoding='utf-8') as file:
        reader = csv.reader(file, delimiter=';')
        invalid_rows = []

        for row in reader:
            if len(row) < 6:
                invalid_rows.append((row, "Missing values"))
                continue

            student_number = row[1]
            sprint_str = row[2]
            hours_str = row[3]
            date_str = row[4]
            description = row[5]

            minutes, error_minutes = convert_hours_to_minutes(hours_str)
            date, error_date = validate_and_format_date(date_str)
            sprint, error_sprint = convert_sprint_to_int(sprint_str)
            
            if error_minutes or error_date or error_sprint:
                error_message = error_minutes or error_date or error_sprint
                invalid_rows.append((row, error_message))
                continue
            
            group_id, error_group_id = fetch_group_id(student_number)
            if not group_id:
                invalid_rows.append((row, error_group_id))
                continue

            sprint_id, error_sprint_id = fetch_sprint_id(group_id, sprint)
            if not sprint_id:
                invalid_rows.append((row, error_sprint_id))
                continue
            
            inserted_row, error_db = add_time_log(date, minutes, description, student_number, sprint_id)
            if not inserted_row:
                invalid_rows.append((row, error_db))
                continue

        if invalid_rows:
            print(f"INVALID ROWS IN FILE '{filepath}':\n")
            for row, error in invalid_rows:
                print(row)
                print(f"Error: {error}\n")
            
def main():
    folder = Path(TIMELOGS_DATA_PATH)
    for file in folder.glob('*.csv'):
        process_file(file)
    print('\nTimelogs import execution finished\n')

if __name__ == "__main__":
    main()
