
from db_connection import get_db_connection, close_db_connection
import csv
from datetime import datetime, timezone, timedelta
import psycopg2
from pathlib import Path

SPRINT_DATA_PATH = "/tmp/sprint_data/"

def convert_row(row):
    group_name = row[0]
    try:
        sprint_number = int(row[1])
    except ValueError:
        return None, "sprint_number"
    try:
        start_date = datetime.strptime(row[2], '%Y-%m-%d').date()
    except ValueError:
        return None, "start_date"
    try:
        end_date = datetime.strptime(row[3], '%Y-%m-%d').date()
    except ValueError:
        return None, "end_date"

    return {'group_name': group_name, 'sprint_number': sprint_number, 'start_date': start_date, 'end_date': end_date}, None

def fetch_group_id(group_name):
    """Fetch the group ID from the 'groups' table based on the given group name."""

    try:
        conn, cur = get_db_connection()
        query = "SELECT id FROM groups WHERE name = %s"
        cur.execute(query, (group_name,))
        result = cur.fetchone()
        if result:
            return result[0], None
        else:
            return None, f"Group ID not found for group name {group_name}"
    except psycopg2.Error as e:
        return None, f"Error fetching the group ID: {e}"
    finally:
        close_db_connection(conn, cur)

def check_if_row_exists(group_id, sprint_number):
    conn, cur = get_db_connection()
    try:
        query = """
        SELECT EXISTS (
            SELECT 1 FROM sprints 
            WHERE group_id = %s AND sprint = %s
        )
        """
        cur.execute(query, (group_id, sprint_number))
        result = cur.fetchone()
        return result[0]
    finally:
        close_db_connection(conn, cur)

def insert_into_database(row, group_id):
    try:
        conn, cur = get_db_connection()
        now = datetime.now(timezone.utc)

        start_date = row[2] +timedelta(hours=3)
        end_date = row[3] +timedelta(hours=3)

        query = """
        INSERT INTO sprints (group_id, sprint, start_date, end_date, created_at, updated_at)
        VALUES (%s, %s, %s, %s, %s, %s)
        """
        cur.execute(query, (group_id, row[1], start_date, end_date, now, now))
        conn.commit()
    except psycopg2.Error as e:
        return False, f"Database insertion error: {e}"
    finally:
        close_db_connection(conn, cur)

def process_file(filepath):
    with open(filepath, mode='r', encoding='utf-8') as file:
        reader = csv.reader(file, delimiter=';')
        invalid_rows = []

        for row in reader:
            conversion_success, error_conversion = convert_row(row)
            if conversion_success:
                group_id, error_group_id = fetch_group_id(conversion_success['group_name'])
                if group_id:
                    if check_if_row_exists(group_id, conversion_success['sprint_number']):
                        invalid_rows.append((row, "Sprint already exists in the database"))
                    else:
                        insert_into_database(row, group_id)
                else:
                    invalid_rows.append((row, error_group_id))
            else:
                invalid_rows.append((row, error_conversion))
        
        if invalid_rows:
            print(f"INVALID ROWS IN FILE '{filepath}':\n")
            for row, error in invalid_rows:
                print(row)
                print(f"Error: {error}\n")

def main():
    folder = Path(SPRINT_DATA_PATH)
    for file in folder.glob('*.csv'):
        process_file(file)
    print('\nSprint import execution finished\n')

if __name__ == "__main__":
    main()


