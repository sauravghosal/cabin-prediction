from datetime import date, datetime
from random import randint
import boto3
import pandas as pd
import logging
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, DATETIME, VARBINARY

# change to aws lambda environment variables
load_dotenv()

s3 = boto3.resource('s3')


logging.basicConfig(
    level=logging.DEBUG)

db_host = os.getenv('DB_DATABASE')
db_user = os.getenv('DB_USER')
db_password = os.getenv('DB_PASSWORD')
db_name = "Cabins"


# TODO: move this into aws lambda that is triggered when file is uploaded to s3?
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
    create_database(db_name)
    # fetch objects from s3 bucket
    # ingest the excel file
    xls = pd.ExcelFile('test_output_2.xlsx')
    for cabin in xls.sheet_names:
        df = pd.read_excel('test_output_2.xlsx', sheet_name=cabin)
        df['date'] = pd.to_datetime(
            arg=df['date'], format="%Y_%m_%d", errors='ignore')
        df = df.iloc[:, 1:]
        df.loc[:, 'occupancy'] = df.loc[:,
                                        'occupancy'].str.encode(encoding='utf-8')
        df.to_sql(cabin, engine, index=False,
                  schema=db_name, if_exists="replace", dtype={'date': DATETIME, 'occupancy': VARBINARY(180)})
    engine.dispose()
