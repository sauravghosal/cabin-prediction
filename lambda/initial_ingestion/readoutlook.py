import os
from glob import glob
import inspect
import pandas as pd
from sauravsupport import getCabinNumbers
import logging, sys
from pathlib import Path
from cabinsofinterest import CabinsOfInterest
from appsupport import fixAllOccupancyBitmaps, fixOccupancyBitmap
import json


# TODO: clean up 
# TODO: move this into aws lambda

DirName = str((Path.cwd()).joinpath('scrape'))
NDName = str((Path.cwd()).joinpath('output'))
WriteFileName = str((Path.cwd()).joinpath('output.xlsx'))
WriteTestFileName = str((Path.cwd()).joinpath('test.xlsx'))
desktop = ''


logging.basicConfig(fn=desktop+'output.log',
                    filemode='w',
                    level=logging.DEBUG)


def update_output_file(scrape_file, fn):
    print('Inside {} .....'.format(inspect.currentframe().f_code.co_name))
    #################################################################
    #   Reading 'output.xlsx' file
    #################################################################
    # find latest date ingested into database! 
    scrapeWB = pd.read_excel(scrape_file, sheet_name=None,
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
                print('1. Cabin being checked .... ', cabin)
                try:
                    cabin_info = scrapeWB[mgmtco].loc[cabin,'month1':'month7'].str.replace('\'','')
                    #
                    # Calculate and add the 'occupancy'
                    #
                    # print('2. Cabin being checked .... ', cabin)
                    cabin_info['occupancy'] = (fixOccupancyBitmap(cabin, fn[0:10],
                                        [cabin_info['month1'],
                                        cabin_info['month2'],
                                        cabin_info['month3'],
                                        cabin_info['month4'],
                                        cabin_info['month5'],
                                        cabin_info['month6'],
                                        cabin_info['month7']]))
                    print(cabin_info)
                except KeyError as err:
                    print ("KeyError .. could not add cabin .. {} {}".format(cabin, fn[0:10]))
                    # raise err
                except ValueError as err:
                    print('\t***{} could not add {} due to overlap'.format(cabin, fn[0:10]))
                    # raise err

    # ingest into database
    # with pd.ExcelWriter(WriteTestFileName) as writer:
    #     print('Opening to write {}'.format(WriteTestFileName))
    #     for cabinName, data in cc_dict.items():
    #         print('\tWriting {:25}{:4} lines'.
    #                 format(cabinName, len(data.index)))
    #         data = data.astype(str)
    #         data.to_excel(writer, sheet_name=cabinName, index_label='Date')
    #     cc_dict['__number_cabins'].to_excel(writer,
    #                     sheet_name='__number_cabins', index_label='Date')



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
    # Update the output.xlsx file
    update_output_file()
    return {
        "statusCode": 200,
        "body": json.dumps({
            "message": "completed!",
            # "location": ip.text.replace("\n", "")
        }),
    }
    




