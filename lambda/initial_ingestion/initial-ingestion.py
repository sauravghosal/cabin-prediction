from datetime import date
from random import randint
import pandas as pd
import logging
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, DATETIME, NVARCHAR

# change to aws lambda environment variables
load_dotenv()


logging.basicConfig(
    level=logging.DEBUG)

db_host = os.getenv('DB_DATABASE')
db_user = os.getenv('DB_USER')
db_password = os.getenv('DB_PASSWORD')
db_name = "cabins"


# TODO: clean up SQL queries with Session/Transaction ORM from SQLAlchemy?
# https://docs.sqlalchemy.org/en/14/core/tutorial.html

engine = create_engine(
    f'mysql+pymysql://{db_user}:{db_password}@{db_host}/{db_name}')


def drop_database(db_name):
    drop_db = f"""DROP DATABASE `{db_name}`"""
    try:
        with engine.connect() as conn:
            conn.execute(drop_db)
    except (Exception) as error:
        raise error


def create_database(db_name):
    create_db = f"""CREATE DATABASE IF NOT EXISTS `{db_name}`"""
    use_db = f"""USE {db_name}"""
    try:
        conn = engine.connect()
        conn.execute(create_db)
        conn.execute(use_db)
    except (Exception) as error:
        raise error
    finally:
        conn.close()


def create_table(table_name):
    command = (
        f"""CREATE TABLE IF NOT EXISTS `{table_name}` (date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP, occupancy VARBINARY(180) NOT NULL)""")
    try:
        conn = engine.connect()
        conn.execute(command)
        # commit the changes
    except (Exception) as error:
        raise error
    finally:
        conn.close()


def drop_table(table_name):
    command = f"""DROP TABLE IF EXISTS `{table_name}`"""
    try:
        conn = engine.connect()
        conn.execute(command)
        # commit the changes
    except (Exception) as error:
        raise error
    finally:
        conn.close()


def ingest_data(bits, table_name):
    try:
        conn = engine.connect()
        conn.execute(
            f"""INSERT INTO `{table_name}` (date, occupancy) VALUES ('{date.today():%Y-%m-%d})', '{bits:b}')""")
        # commit the changes
    except (Exception) as error:
        raise error
    finally:
        conn.close()


def handler(event, context):
    xls = pd.ExcelFile('output.xlsx')
    for cabin in xls.sheet_names[1:]:
        df = xls.parse(sheet_name=cabin)
        df['Date'] = pd.to_datetime(
            arg=df['Date'], format="%Y_%m_%d", errors='ignore')
        df.drop(df.columns[[1, 2, 3, 4, 5, 6, 7]], axis=1, inplace=True)
        print(df)
        df.to_sql(cabin.strip(), engine, index=False,
                  schema=db_name, if_exists="replace", dtype={'date': DATETIME, 'occupancy': NVARCHAR(180)})
    engine.dispose()
    