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


db_host = os.environ['DB_DATABASE']
db_user = os.environ['DB_USER']
db_password = os.environ['DB_PASSWORD']
db_name = "Cabins"

# TODO: move this into aws lambda that is triggered when file is uploaded to s3? - done!
# TODO: clean up SQL queries with Session/Transaction ORM from SQLAlchemy?
# https://docs.sqlalchemy.org/en/14/core/tutorial.html

engine = create_engine(
    f'mysql+pymysql://{db_user}:{db_password}@{db_host}/{db_name}')

DirName = str((Path.cwd()).joinpath('scrape'))
NDName = str((Path.cwd()).joinpath('output'))
WriteFileName = str((Path.cwd()).joinpath('output.xlsx'))
WriteTestFileName = str((Path.cwd()).joinpath('test.xlsx'))
desktop = ''


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

logging.basicConfig(fn=desktop+'output.log',
                    filemode='w',
                    level=logging.DEBUG)

def IsValidFile(fn):

    # Check for 2nd half of file name
    if (fn[10:].split('.')[0] != '_Data_Scraping_Output'):
        #print("Invalid file name: {}".format(fn))
        return(False)

    #Check for date part of the file name
    try:
        date = datetime.datetime.strptime(fn[0:10], '%Y_%m_%d')
        return (True)
    except ValueError as err:
        print("Invalid date in file name: {}".format(err))
        return (False)
 


def update_output_file():
    print('Inside {} .....'.format(inspect.currentframe().f_code.co_name))
    #################################################################
    #   Reading 'output.xlsx' file
    #################################################################
    lastDate='0000_00_00'
    try:
        print('Opening to read {}'.format(WriteFileName))
        try:
            #cc_dict = pd.read_excel('output.xlsx')
            cc_dict = pd.read_excel('output.xlsx', sheet_name=None,
                                dtype={ 'month1': str, 'month2': str,
                                        'month3': str, 'month4': str,
                                        'month5': str, 'month6': str,
                                        'month7': str
                                        }
                                )
        except Exception as ex:
            print ('Unexpected Error in pd.read_excel: ', inspect.getframeinfo(inspect.currentframe()).function, ex)
            exit()

        # Find the last date -> query database for this
        # remove code for _number_cabins
        cabinList = list(cc_dict.keys())
        for tab in cabinList:
            # overall cabin view
            if (tab == '__number_cabins'):
                cachedNumCabin_dict = cc_dict[tab]
                cachedNumCabin_dict.set_index('Date', inplace=True)
                print('\tReading {:25}{:4} lines'.format(tab,
                                    len(cc_dict[tab].index)))
            # all the other cabin pages
            else:
                try:
                    lastDate = cc_dict[tab].iloc[-1,:]['Date']
                    cc_dict[tab].set_index('Date',inplace=True)
                    cc_dict[tab] = cc_dict[tab].loc[:,'month1':'month7']
                    print('\tReading {:25}{:4} lines'.format(tab,
                                    len(cc_dict[tab].index)))
                    # Adding the fixedOccupancy column as well.
                    if (1):
                        print("\t\tCleaning up ... {}".format(tab))
                        mypd = fixAllOccupancyBitmaps(tab, cc_dict[tab])
                        # Convert index from datetime to string
                        mypd.index = mypd.index.strftime('%Y_%m_%d')
                        cc_dict[tab]['occupancy'] = mypd
                        cc_dict[tab]['occupancy'] = cc_dict[tab]['occupancy'].str.slice(stop=180)
                except KeyError as err:
                    print(err)
                    print('Incorrect tab: {}  .. deleting '.format(tab))
                    cc_dict.pop(tab, None)
    except FileNotFoundError as err:
        print("Input file not found .. continuing ....{}".format(err))
        cc_dict = {}
    except PermissionError as err:
        print("Unable to openfile .. permission error {}".format(err))

    print('Last date from previous file: {}'.format(lastDate))
    dirtyFlag = False

    #################################
    #   If no 'Occupancy' row
    #   then create this row and save it HERE
    #################################

    #
    #
    #


    ##############################################################
    #   Reading new input files ... and appending data to old file
    
    # take this from s3 or EFS
    for fn in os.listdir(NDName):
        if (IsValidFile(fn) & (fn[0:10] > lastDate)):
            scrapeWB = pd.read_excel(NDName+"\\"+fn, sheet_name=None,
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
            myseries = pd.Series(getCabinNumbers(scrapeWB), name=fn[0:10])
            try:
                cc_dict['__number_cabins'] = cc_dict.setdefault('__number_cabins', pd.DataFrame(columns=[])).append(myseries, verify_integrity=True)
            except ValueError as err:
                print('__number_cabins overlapping index {} .. not inserting'.
                      format(fn[0:10]))
            print('Reading {}'.format(fn[0:10]))
            for mgmtco in scrapeWB.keys():
                if (mgmtco in CabinsOfInterest.keys()):
                    scrapeWB[mgmtco].set_index('CabinName', inplace=True)
                    scrapeWB[mgmtco].columns = \
                        [x.replace('monthAvailabe_','month') if ('monthAvailabe_' in x) else x for x in scrapeWB[mgmtco].columns]
                    cabinList = CabinsOfInterest[mgmtco]
                    for cabin in cabinList:
                        #print('1. Cabin being checked .... ', cabin)
                        try:
                            cabin_info = scrapeWB[mgmtco].loc[cabin,'month1':'month7'].str.replace('\'','')
                            #
                            #   Calculate and add the 'occupancy'
                            #
                            #
                            #print('2. Cabin being checked .... ', cabin)
                            cabin_info.name = fn[0:10]
                            cabin_info['occupancy'] = (fixOccupancyBitmap(cabin, cabin_info.name,
                                               [cabin_info['month1'],
                                                cabin_info['month2'],
                                                cabin_info['month3'],
                                                cabin_info['month4'],
                                                cabin_info['month5'],
                                                cabin_info['month6'],
                                                cabin_info['month7']]))
                            cc_dict[cabin] = cc_dict.setdefault(cabin, pd.DataFrame(columns=[])).append(cabin_info, verify_integrity=True)
                            print('\t{} {}'.format(cabin, mgmtco))
                            dirtyFlag = True
                        except KeyError:
                            print ("KeyError .. could not add cabin .. {} {}".format(cabin, fn[0:10]))
                            pass
                        except ValueError as err:
                            print('\t***{} could not add {} due to overlap'.format(cabin, fn[0:10]))

    if (not dirtyFlag):
        print("No new entries, lastDate={} .. skipping write".format(lastDate))
    else:
        with pd.ExcelWriter(WriteTestFileName) as writer:
            print('Opening to write {}'.format(WriteTestFileName))
            for cabinName, data in cc_dict.items():
                print('\tWriting {:25}{:4} lines'.
                      format(cabinName, len(data.index)))
                data = data.astype(str)
                data.to_excel(writer, sheet_name=cabinName, index_label='Date')
            cc_dict['__number_cabins'].to_excel(writer,
                            sheet_name='__number_cabins', index_label='Date')


def lambda_handler(event, context):
    """Sample pure Lambda function

    Parameters
    ----------
    event: dict, required
        API Gateway Lambda Proxy Input Format

        Event doc: https://docs.aws.amazon.com/apigateway/latest/developerguide/set-up-lambda-proxy-integrations.html#api-gateway-simple-proxy-for-lambda-input-format

    context: object, required
        Lambda Context runtime methods and attributes

        Context doc: https://docs.aws.amazon.com/lambda/latest/dg/python-context-object.html

    Returns
    ------
    """

    for fn in sorted(glob(DirName+ "\\" + 'Data_Scraping_Output_*.xlsx')):
        parsed_string = fn.split('Data_Scraping_Output_')[-1].split('.xlsx')[0]
        try:
            mydate = datetime.datetime.strptime(parsed_string, "%m_%d_%Y")
        except ValueError as err:
            print("Incorrect date format; ignoring file ", fn, err)

            continue

        date_str = '{:4}_{:02}_{:02}'.format(mydate.year, mydate.month, mydate.day)
        newfn=NDName + "\\" + date_str + "_Data_Scraping_Output.xlsx"

        # Copy only if file does NOT exist
        if (os.path.exists(newfn) == False):
            print("Copying ", fn, "to", newfn)
            shutil.copyfile(fn, newfn)

    # Update the output.xlsx file
    update_output_file()
    return {
        "statusCode": 200,
        "body": json.dumps({
            "message": "completed!",
            # "location": ip.text.replace("\n", "")
        }),
    }



