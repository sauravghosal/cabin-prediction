import psycopg2
from datetime import date
from random import randint
import sys
import os
from dotenv import load_dotenv

load_dotenv()

cabin_name = sys.argv[1]
num_days = sys.argv[2]

db_name = os.getenv('DB_DATABASE')
db_user = os.getenv('DB_USER')
db_password = os.getenv('DB_PASSWORD')


def create_table(table_name):
    command = (
        f"""
        CREATE TABLE IF NOT EXISTS \"{table_name}\" (
            date DATE DEFAULT CURRENT_TIMESTAMP,
            occupancy BIT VARYING(180) NOT NULL
        )""")
    conn = None
    try:
        conn = psycopg2.connect(
            f"dbname={db_name} user={db_user} password={db_password}")
        cur = conn.cursor()
        cur.execute(command)
        # close communication with the PostgreSQL database server
        cur.close()
        # commit the changes
        conn.commit()
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    finally:
        if conn is not None:
            conn.close()


def ingest_data(bits, table_name):
    try:
        conn = psycopg2.connect(
            f"dbname={db_name} user={db_user} password={db_password}")
        cur = conn.cursor()
        cur.execute(f"""
          INSERT INTO \"{table_name}\" (date, occupancy)
          VALUES ('{date.today():%Y-%m-%d})', '{bits:b}');
          """)
        # close communication with the PostgreSQL database server
        cur.close()
        # commit the changes
        conn.commit()
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    finally:
        if conn is not None:
            conn.close()


def query_data(table_name):
    try:
        conn = psycopg2.connect(
            "dbname=test user=postgres password=Cats@481")
        cur = conn.cursor()
        cur.execute(f"""
          SELECT * FROM \"{table_name}\"
          """)
        return cur.fetchall()
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    finally:
        cur.close()
        if conn is not None:
            conn.close()


if __name__ == "__main__":
    create_table(table_name=cabin_name)
    for i in range(0, int(num_days)):
        ingest_data(bits=randint(0, 100), table_name=cabin_name)
    rows = query_data(table_name=cabin_name)
    for row in rows:
        print(row)
