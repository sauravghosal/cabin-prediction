import pandas as pd
from glob import glob
import datetime as datetime
import os, platform
import inspect
import numpy as np
from appsupport import getCorrectiveOffsets, new_load_cabin_info

if (platform.node() == 'Anjan-New-Asus-Laptop'):
    Dir = r'C:\Users\aghos\Dropbox\GhosalRE\Tennessee_Scrape_Data_New'
    desktop = 'C:\\Users\\aghos\\OneDrive\\desktop\\'
    fileName = r'C:\Users\aghos\OneDrive\Desktop\output.xlsx'
else:
    Dir = ''
    fileName = 'output.xlsx'

def getLastFilename(number=1):
    wholeFileName = Dir + "\\" + '*_Data_Scraping_Output.xlsx'
    fileList = []
    counter = 0
    for filename in reversed(sorted(glob(wholeFileName))):
        parsed_string = filename.split('\\')[-1][0:10]
        try:
            datetime.datetime.strptime(parsed_string, "%Y_%m_%d")
            fileList.append(filename)
            counter = counter + 1
            if (counter >= number):
                return (fileList)
        except ValueError as err:
            print("Incorrect date format; ignoring file ", filename, err)
            continue
    return(fileList)


def readFile(fileName):
    try:
        fileHandle = pd.read_excel(fileName, sheet_name=None)
    except FileNotFoundError as err:
        print("Input file not found .. continuing ....{}".format(err))
        return(False)
    except PermissionError:
        print("Unable to openfile .. permission error")
        return(False)
    
    return(fileHandle)


def getFileSize(fileName):
    return(os.path.getsize(fileName)/1000)

def getFileDate(fileName):
    return (datetime.datetime.fromtimestamp(os.path.getmtime(fileName)))
    return('Inside {} .....'.format(inspect.currentframe().f_code.co_name))

def getMgmtCompanyList(fileHandle):
    return(list(fileHandle.keys())[1:-1])
    return('Inside {} .....'.format(inspect.currentframe().f_code.co_name))

def getCabinNumbers(fileHandle):
    numCabinDirectory = {}
    for mgmtCompany in getMgmtCompanyList(fileHandle):
        cabinList = fileHandle[mgmtCompany]
        cabinList.dropna(how='all', inplace=True)
        numCabinDirectory.setdefault(mgmtCompany, len(cabinList.index))
    return(numCabinDirectory)
    return('Inside {} .....'.format(inspect.currentframe().f_code.co_name))

def getMonthlyOffsets(fileHandle, mydate):
    offset_list = {}
    for mgmtCompany in getMgmtCompanyList(fileHandle):
        cabinList = fileHandle[mgmtCompany]
        cabinList.dropna(how='all', inplace=True)
        if (cabinList.empty):
            offset_list.setdefault(mgmtCompany, [])
        else:
            ## Here we get the 1st cabins and use that as a basis for
            ## calculating the monthly offsets for all cabins under the
            ## management company.
            cabin_df = cabinList.head(1).set_index('CabinName').\
                           loc[:,'monthAvailabe_1':'monthAvailabe_7']
            cabin_df = cabin_df.replace("\'", "", regex=True)
            bitmaps = cabin_df.values.flatten().tolist()
            offset = getCorrectiveOffsets(cabin_df.index.values[0], mydate, bitmaps)
            offset_list.setdefault(mgmtCompany, offset)
    return (offset_list)
    return('Inside {} .....'.format(inspect.currentframe().f_code.co_name))




def getDaysOccupiedByMonth(filehandle, filename):
    #print('Inside {} .....'.format(inspect.currentframe().f_code.co_name))
    if (not filename in filehandle.keys()):
        return (False)
    else:
        myseries = filehandle[filename]['month1'].str[0].copy()
        myseries.fillna('X', inplace=True)
        # Return occupancy bitmap grouped by month
        return (myseries.groupby(pd.Grouper(freq='M')).sum())

if __name__ == '__main__':
    pd.set_option('display.max_rows', 2000)
    pd.set_option('display.max_columns', 2000)
    pd.set_option('display.max_colwidth', -1)
    pd.set_option('max_rows', 5000)
    pd.set_option('display.colheader_justify', 'left')
    pd.set_option('display.width', 1000)

    cabin_info = new_load_cabin_info(fileName, FixOccupancyBitmap=True)

    cabin_df = pd.DataFrame(columns=[])
    cabin_df.columns = [x[0:4] for x in cabin_df.columns]

    ## Print # of days occupied by month for each Cabin
    for cabin in cabin_info:
        monthlyBookings = getDaysOccupiedByMonth(cabin_info, cabin).\
            str.count('1')
        cabin_df[cabin] = monthlyBookings
    cabin_df.fillna('X', inplace=True)
    cabin_df.columns = [x[0:8] for x in cabin_df.columns]
    print (cabin_df)

    #############################################################
    #   Print the number of cabins by management company for    #
    #   last few days. to see if anything is changing           #
    #############################################################
    cabinNumberList = {}
    fileNameList = getLastFilename(number=1)
    for fname in fileNameList:
        fileHandle = readFile(fname)
        numCabinsDict = getCabinNumbers(fileHandle)
        for mgmtCompany, numCabins in numCabinsDict.items():
            value = cabinNumberList.setdefault(mgmtCompany, [])
            value.append(numCabins)
            cabinNumberList[mgmtCompany] = value

    print('\nPrinting # cabins by company for last {} days'.format('8'))
    for mgmtCompany, numCabins in cabinNumberList.items():
        print('{:25}{}'.format(mgmtCompany, ' '.join('{:5}'.\
                                    format(x) for x in numCabins)))

    #################################################################
    #   Print offsets per month starting current month              #
    #                                                               #
    #################################################################
    mydate = datetime.datetime.strftime(getFileDate(fileName), '%Y_%m_%d')
    print ("***** Mydate: ", mydate, "FileName: ", fileName)

    offset_dict = getMonthlyOffsets(fileHandle, mydate)
    print('\nPrinting monthly offsets .... ')
    for mgmtCompany, offset in offset_dict.items():
        cabinNumberList.setdefault(mgmtCompany, numCabinsDict[mgmtCompany])
        print('{:25} {}'.format(mgmtCompany, ''.join('{:6}'.\
                                    format(x) for x in offset)))

