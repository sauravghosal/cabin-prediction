from datetime import date
import pandas as pd
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, DATETIME, NVARCHAR
from sqlalchemy.sql.sqltypes import SMALLINT
from appsupport import updateCabinColumns
import atexit
import boto3
import io
import json

# change to aws lambda environment variables
load_dotenv()


db_host = os.environ['DB_DATABASE']
db_user = os.environ['DB_USER']
db_password = os.environ['DB_PASSWORD']
db_name = "cabins"


s3 = boto3.client('s3')

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
        
def download_output_file(bucket_name, folder_prefix):
    scrape_files = s3.list_objects_v2(Bucket=bucket_name, Prefix=folder_prefix)['Contents']
    latest_output_file = max(scrape_files, key=lambda x: x['LastModified'])
    io_stream = io.BytesIO()
    s3.download_fileobj(bucket_name, latest_output_file['Key'], io_stream)
    io_stream.seek(0)
    return io_stream
    
    
def handler(event, context):
    try: 
        file_contents = download_output_file(bucket_name="ghosalre", folder_prefix='scrape output')
        xls = pd.ExcelFile(file_contents)
        for cabin in xls.sheet_names[1:]:
            df = xls.parse(sheet_name=cabin)
            df['date'] = pd.to_datetime(
                arg=df['Date'], format="%Y_%m_%d", errors='ignore')
            df.drop(df.columns[[1, 2, 3, 4, 5, 6, 7]], axis=1, inplace=True)
            updateCabinColumns(cabin_name=cabin, cabin_df=df)
            df.drop(['Date', 'dow', 'C', 'B', 'tot_count', 'occ_delta'], axis=1, inplace=True)
            df.to_sql(cabin.strip(), engine, index=True,
                    schema=db_name, if_exists="replace", dtype={'date': DATETIME, 'occupancy': NVARCHAR(180), 'occ_count': SMALLINT, 'bmap_diff': NVARCHAR(180)})
        return {
            "statusCode": 200,
            "body": json.dumps({
            "message": "ingestion complete!",
            })
        }
    except Exception as err:
        raise err
    
   
def close_db_connection():
    print('Closing db connection')
    engine.dispose()

atexit.register(close_db_connection)