from flask import Flask, request, render_template
from datetime import datetime
import os
from sqlalchemy import create_engine
from dotenv import load_dotenv
from pathlib import Path
import logging
import re
import atexit
import pandas

app = Flask(__name__)
app.config['JSON_SORT_KEYS'] = False

logging.basicConfig(filename=Path(__file__).parent.joinpath(
    'debug.log'), level=logging.DEBUG)
load_dotenv(dotenv_path='.env')

db_host = os.getenv('DB_DATABASE')
db_user = os.getenv('DB_USER')
db_password = os.getenv('DB_PASSWORD')
db_name = "cabins"


engine = create_engine(
    f'mysql+pymysql://{db_user}:{db_password}@{db_host}/{db_name}')

# TODO: reconfigure to use ORM models provided by sql-alchemy to clean up


def query_occupancy_by_date_range(table_name, start_date, end_date):
    try:
        conn = engine.connect()
        app.logger.info('Finding occupancy data between %s and %s for cabin %s',
                        start_date, end_date, table_name)
        return conn.execute(f"""
          SELECT * FROM `{table_name}` WHERE date BETWEEN '{start_date:%Y-%m-%d}' AND '{end_date:%Y-%m-%d} ORDER BY date ASC'
          """)
    except (Exception) as error:
        app.logger.error(error)
    finally:
        conn.close()
        engine.dispose()


def query_all_cabins():
    try:
        conn = engine.connect()
        return conn.execute(f"""select table_name from INFORMATION_SCHEMA.TABLES where TABLE_TYPE='BASE TABLE' AND table_schema='cabins'""")
    except (Exception) as error:
        app.logger.error(error)
    finally:
        conn.close()
        engine.dispose()

# home page
@app.route('/', methods=['GET'])
def home():
    return render_template('index.html')


@app.route('/cabins', methods=['GET'])
def list_all_cabins():
    cabins = []
    for cabin in query_all_cabins():
        cabins.append(re.search('([\'\"](.*)[\'\"])', str(cabin)).group(1))
    return dict(cabin=cabins)

# TODO: query string param validation on start_date, end_date, and cabin
@app.route('/occupancy', methods=["GET"])
def query_by_date():
    start_date, end_date, cabin_name = request.args.get(
        "start_date"), request.args.get("end_date"), request.args.get("cabin")
    app.logger.info("start date: %s, end date: %s, cabin: %s",
                    start_date, end_date, cabin_name)
    start_date = datetime.strptime(start_date, '%m-%d-%Y').date()
    end_date = datetime.strptime(end_date, '%m-%d-%Y').date()
    rows = query_occupancy_by_date_range(
        table_name=cabin_name, start_date=start_date, end_date=end_date)
    occupancy_data = {}
    for row in rows:
        print(row)
        if row[1]:
            occupancy_data.update(
                {row[0].strftime('%m-%d-%Y'): row[1]})
    return dict(occupancy=occupancy_data)


# def close_db_connection():
#     app.logger.info('Closing db connection')
#     engine.dispose()

# atexit.register(close_db_connection)
