
from db_connection import get_db_connection, close_db_connection
import csv
from datetime import datetime, timezone
import psycopg2
from pathlib import Path


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

def check_if_row_exists(row, group_id):
    conn, cur = get_db_connection()
    query = """
    SELECT EXISTS (
        SELECT 1 FROM sprints 
        WHERE group_id = %s AND sprint = %s AND start_date = %s AND end_date = %s
    )
    """
    cur.execute(query, (group_id, row[1], row[2], row[3]))
    result = cur.fetchone()
    return result[0]

def insert_into_database(row, group_id):
    try:
        conn, cur = get_db_connection()
        now = datetime.now(timezone.utc)
        query = """
        INSERT INTO sprints (group_id, sprint, start_date, end_date, created_at, updated_at)
        VALUES (%s, %s, %s, %s, %s, %s)
        """
        cur.execute(query, (group_id, row[1], row[2], row[3], now, now))
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
                    if not check_if_row_exists(row, group_id):
                        insert_into_database(row, group_id)
                    else:
                        invalid_rows.append((row, "Sprint already exists in the database"))
                else:
                    invalid_rows.append((row, error_group_id))
            else:
                invalid_rows.append((row, error_conversion))
        
        if invalid_rows:
            for row, error in invalid_rows:
                print(f"INVALID ROWS IN FILE '{filepath}':\n")
                print(row)
                print(f"Error: {error}\n")

def main():
    folder = Path('data/sprint_data')
    for file in folder.glob('*.csv'):
        process_file(file)

if __name__ == "__main__":
    main()


