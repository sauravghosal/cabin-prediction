import shutil
import os, platform
from glob import glob
import datetime
import inspect
import pandas as pd
from sauravsupport import getCabinNumbers
import cabinsofinterest
import logging, sys
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


def get_most_recent_date(table_name):
    command = (f"""SELECT MAX (Date) AS \"Max Date\" FROM `{table_name}`""")
    try:
        conn = engine.connect()
        conn.execute(command)
        # commit the changes
    except (Exception) as error:
        raise error
    finally:
        conn.close()

def download_new_scrape_files(bucket_name, folder_prefix, date):
    print('Downloading new scrape files from {}'.format(bucket_name))
    scrape_files = s3.list_objects_v2(Bucket=bucket_name, Prefix=folder_prefix)['Contents']
    latest_scrape_files = list(filter(lambda x: IsValidFile(x['Key'].split('/')[-1], date), scrape_files))
    print('Found {} new scrape files'.format(len(latest_scrape_files)))
    for scrape_file in latest_scrape_files:
        io_stream = io.BytesIO()
        s3.download_fileobj(bucket_name, scrape_file['Key'], io_stream)
        io_stream.seek(0)
        yield io_stream

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
    
def get_most_recent_date(table_name):
    try:
        conn = engine.connect()
        return conn.execute(f"""SELECT MAX(Date) FROM `{table_name}`""").first()['MAX(Date)']
    except (Exception) as error:
        raise error
    finally:
        conn.close()
        
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


def update_output_file(file):
    #################################################################
    #   Reading 'output.xlsx' file
    #################################################################
    

    #################################
    #   If no 'Occupancy' row
    #   then create this row and save it HERE
    #################################

    #
    #
    #


    ##############################################################
    #   Reading new input files ... and appending data to old file
    scrapeWB = pd.read_excel(file, sheet_name=None,
                            dtype={'monthAvailabe_1': str,
                                'monthAvailabe_2': str,
                                'monthAvailabe_3': str,
                                'monthAvailabe_4': str,
                                'monthAvailabe_5': str,
                                'monthAvailabe_6': str,
                                'monthAvailabe_7': str
                                })
    #         #### HACK! HACK ! HACK!
    #### For cabinsusa, remove " Cabin Rental" from cabinname
    if ('cabinsusa' in scrapeWB.keys()):
        scrapeWB['cabinsusa']['CabinName'] = scrapeWB['cabinsusa']\
            ['CabinName'].str.replace(" Cabin Rental", "")
    print(scrapeWB)
    #### end of hack ####
    #         myseries = pd.Series(getCabinNumbers(scrapeWB), name=fn[0:10])
    #         try:
    #             cc_dict['__number_cabins'] = cc_dict.setdefault('__number_cabins', pd.DataFrame(columns=[])).append(myseries, verify_integrity=True)
    #         except ValueError as err:
    #             print('__number_cabins overlapping index {} .. not inserting'.
    #                   format(fn[0:10]))
    #         print('Reading {}'.format(fn[0:10]))
    #         for mgmtco in scrapeWB.keys():
    #             if (mgmtco in CabinsOfInterest.keys()):
    #                 scrapeWB[mgmtco].set_index('CabinName', inplace=True)
    #                 scrapeWB[mgmtco].columns = \
    #                     [x.replace('monthAvailabe_','month') if ('monthAvailabe_' in x) else x for x in scrapeWB[mgmtco].columns]
    #                 cabinList = CabinsOfInterest[mgmtco]
    #                 for cabin in cabinList:
    #                     #print('1. Cabin being checked .... ', cabin)
    #                     try:
    #                         cabin_info = scrapeWB[mgmtco].loc[cabin,'month1':'month7'].str.replace('\'','')
    #                         #
    #                         #   Calculate and add the 'occupancy'
    #                         #
    #                         #
    #                         #print('2. Cabin being checked .... ', cabin)
    #                         cabin_info.name = fn[0:10]
    #                         cabin_info['occupancy'] = (fixOccupancyBitmap(cabin, cabin_info.name,
    #                                            [cabin_info['month1'],
    #                                             cabin_info['month2'],
    #                                             cabin_info['month3'],
    #                                             cabin_info['month4'],
    #                                             cabin_info['month5'],
    #                                             cabin_info['month6'],
    #                                             cabin_info['month7']]))
    #                         cc_dict[cabin] = cc_dict.setdefault(cabin, pd.DataFrame(columns=[])).append(cabin_info, verify_integrity=True)
    #                         print('\t{} {}'.format(cabin, mgmtco))
    #                         dirtyFlag = True
    #                     except KeyError:
    #                         print ("KeyError .. could not add cabin .. {} {}".format(cabin, fn[0:10]))
    #                         pass
    #                     except ValueError as err:
    #                         print('\t***{} could not add {} due to overlap'.format(cabin, fn[0:10]))
    
    # TODO: ingest into database
    
    # if (not dirtyFlag):
    #     print("No new entries, lastDate={} .. skipping write".format(lastDate))
    # else:
    #     with pd.ExcelWriter(WriteTestFileName) as writer:
    #         print('Opening to write {}'.format(WriteTestFileName))
    #         for cabinName, data in cc_dict.items():
    #             print('\tWriting {:25}{:4} lines'.
    #                   format(cabinName, len(data.index)))
    #             data = data.astype(str)
    #             data.to_excel(writer, sheet_name=cabinName, index_label='Date')
    #         cc_dict['__number_cabins'].to_excel(writer,
    #                         sheet_name='__number_cabins', index_label='Date')
            
        


def handler(event, context):
    cabins = query_all_cabins()
    latest_date = get_most_recent_date(cabins[1])
    for cabin in cabins[2:]:
        if get_most_recent_date(cabin) > latest_date:
            latest_date = get_most_recent_date(cabin) 
    print(latest_date)
    for scrape_file in download_new_scrape_files(bucket_name="ghosalre", folder_prefix='Data', date=latest_date):
        update_output_file(scrape_file)
    return {
        "statusCode": 200,
        "body": json.dumps({
            "message": "incremental ingestion complete!",
            # "location": ip.text.replace("\n", "")
        }),
    }


