import os
from glob import glob
import datetime
import pandas as pd
from pathlib import Path
from cabinsofinterest import CabinsOfInterest
from appsupport import fixAllOccupancyBitmaps, fixOccupancyBitmap
from sqlalchemy import create_engine, DATETIME, VARBINARY
import json
import io 
import boto3


db_host = os.environ['DB_DATABASE']
db_user = os.environ['DB_USER']
db_password = os.environ['DB_PASSWORD']
db_name = "cabins"


s3 = boto3.client('s3')

# TODO: move this into aws lambda that is triggered when file is uploaded to s3? - done!
# TODO: clean up SQL queries with Session/Transaction ORM from SQLAlchemy?
# https://docs.sqlalchemy.org/en/14/core/tutorial.html

engine = create_engine(
    f'mysql+pymysql://{db_user}:{db_password}@{db_host}/{db_name}')


# SQL QUERIES
def get_most_recent_date(table_name):
    try:
        conn = engine.connect()
        return conn.execute(f"""SELECT MAX(Date) FROM `{table_name}`""").first()['MAX(Date)']
    except (Exception) as error:
        raise error
    finally:
        conn.close()
        
# TODO: reconfigure to use ORM models provided by sql-alchemy to clean up
def query_occupancy_by_date_range(table_name:str, start_date:datetime, end_date:datetime):
    try:
        conn = engine.connect()
        print('Finding occupancy data between {} and {} for cabin {}'.format(
                        start_date, end_date, table_name))
        return conn.execute(f"""
          SELECT DATE, OCCUPANCY FROM `{table_name.strip()}` WHERE date BETWEEN '{start_date:%Y-%m-%d}' AND '{end_date:%Y-%m-%d} ORDER BY date ASC'
          """)
    except (Exception) as error:
        raise error
    finally:
        conn.close()
        engine.dispose()
        
def query_all_cabins():
    try:
        conn = engine.connect()
        res = conn.execute(f"""select table_name from INFORMATION_SCHEMA.TABLES where TABLE_TYPE='BASE TABLE' AND table_schema='cabins'""")
        cabins = []
        for cabin in res:
            cabins.append(cabin['TABLE_NAME'])
        return cabins
    except (Exception) as error:
        raise error
    finally:
        conn.close()
        
def ingest_data(bits: str, date: datetime.datetime, table_name: str):
    try:
        conn = engine.connect()
        print('Ingesting occupancy data from date {:%Y-%m-%d} for cabin {}'.format(date, table_name))
        conn.execute(
            f"""INSERT INTO `{table_name.strip()}` (date, occupancy) VALUES ('{date:%Y-%m-%d})', '{bits}')""")
    except (Exception) as error:
        print(error)
        raise error
    finally:
        conn.close()
        
# S3 QUERIES
def download_new_scrape_files(bucket_name, folder_prefix, date):
    print('Downloading new scrape files from {}'.format(bucket_name))
    scrape_files = s3.list_objects_v2(Bucket=bucket_name, Prefix=folder_prefix)['Contents']
    latest_scrape_files = list(filter(lambda x: IsValidFile(x['Key'].split('/')[-1], date), scrape_files))
    print('Found {} new scrape files'.format(len(latest_scrape_files)))
    for scrape_file in latest_scrape_files:
        io_stream = io.BytesIO()
        s3.download_fileobj(bucket_name, scrape_file['Key'], io_stream)
        io_stream.seek(0)
        yield (scrape_file['Key'].split('/')[-1], io_stream)
        


def IsValidFile(fn, prev_date):
    # Check for 2nd half of file name
    if (fn[10:].split('.')[0] != '_Data_Scraping_Output'):
        #print("Invalid file name: {}".format(fn))
        return False
    #Check for date part of the file name
    try:
        date = datetime.datetime.strptime(fn[0:10], '%Y_%m_%d')
        if date > prev_date:
            return True
        return False
    except ValueError as err:
        print("Invalid date in file name: {}".format(err))
        return False
    

# SCRAPE FILE PARSING AND INGESTION
def update_output_file(fn, file_data):
    # TODO: fix all occupancy bit maps -> not sure how much prior data is needed
    scrapeWB = pd.read_excel(file_data, sheet_name=None,
                            dtype={'monthAvailabe_1': str,
                                'monthAvailabe_2': str,
                                'monthAvailabe_3': str,
                                'monthAvailabe_4': str,
                                'monthAvailabe_5': str,
                                'monthAvailabe_6': str,
                                'monthAvailabe_7': str
                                })
    #### HACK! HACK ! HACK!
    #### For cabinsusa, remove " Cabin Rental" from cabinname
    if ('cabinsusa' in scrapeWB.keys()):
        scrapeWB['cabinsusa']['CabinName'] = scrapeWB['cabinsusa']\
            ['CabinName'].str.replace(" Cabin Rental", "")
    #### end of hack ####
    for mgmtco in scrapeWB.keys():
        if (mgmtco in CabinsOfInterest.keys()):
            scrapeWB[mgmtco].set_index('CabinName', inplace=True)
            scrapeWB[mgmtco].columns = \
                [x.replace('monthAvailabe_','month') if ('monthAvailabe_' in x) else x for x in scrapeWB[mgmtco].columns]
            cabinList = CabinsOfInterest[mgmtco]
            for cabin in cabinList:
                try:
                    cabin_info = scrapeWB[mgmtco].loc[cabin,'month1':'month7'].str.replace('\'','')              
                    cabin_info['occupancy'] = (fixOccupancyBitmap(cabin, fn[0:10],
                                        [cabin_info['month1'],
                                        cabin_info['month2'],
                                        cabin_info['month3'],
                                        cabin_info['month4'],
                                        cabin_info['month5'],
                                        cabin_info['month6'],
                                        cabin_info['month7']]))
                    ingest_data(cabin_info['occupancy'], datetime.datetime.strptime(fn[0:10], '%Y_%m_%d'), cabin)
                except KeyError:
                    print ("KeyError .. could not add cabin .. {} {}".format(cabin, fn[0:10]))
                    pass
                except ValueError as err:
                    print('\t***{} could not add {} due to overlap'.format(cabin, fn[0:10]))
    
        


def handler(event, context):
    cabins = query_all_cabins()
    latest_date = get_most_recent_date(cabins[1])
    for cabin in cabins[2:]:
        if get_most_recent_date(cabin) > latest_date:
            latest_date = get_most_recent_date(cabin) 
    print(f"Last date database was updated: {latest_date:%Y_%m_%d}")
    for (fn, file_data) in download_new_scrape_files(bucket_name="ghosalre", folder_prefix='Data', date=latest_date):
        update_output_file(fn, file_data)
    return {
        "statusCode": 200,
        "body": json.dumps({
            "message": "incremental ingestion complete!",
        }),
    }


