import pandas as pd
import numpy as np
import datetime
from calendar import monthrange
from dateutil.relativedelta import relativedelta
from fuzzywuzzy import fuzz
import platform
import logging
from cabinsofinterest import CabinsOfInterest

if (platform.node() == 'Anjan-New-Asus-Laptop'):
    desktop = 'C:\\Users\\aghos\\OneDrive\\desktop\\'
else:
    desktop = ''
    
logging.basicConfig(filename=desktop+'checkOccupancy.log',
                    filemode='w',
                    level=logging.DEBUG)



#### Helper functions

'''
DESCRIPTION


INPUT
    date: starting date

RETURN
    List containing the number of days till the end of the month for the 
    next 7 months starting the month in the 'date'. Note that the first 
    month is a partial month ONLY including days from 'date' till the end
    of the month (inclusive of 'date'). 

'''
def getDaysByMonth(date):
    split_list = []
    try:
        if (isinstance(date, datetime.datetime)):
            mydate = date
        else:
            mydate = datetime.datetime.strptime(date,'%Y_%m_%d')
    except ValueError as err:
        print("Incorrect date format {}".format(err))
        return(False)

    split_list.append(monthrange(mydate.year, mydate.month)[1] - mydate.day + 1)
    for n in range(1, 7):
        newdate = mydate+relativedelta(months=n)
        totaldays = monthrange(newdate.year, newdate.month)[1]
        split_list.append(totaldays)
    return(split_list)

'''
DESCRIPTION
    Takes occupancy bitmap for 'date' and splits that into months, starting
    with partial first month
    
INPUT
    date -
    bitmap - 180-character bitmap of Occupancy ('00111101011..')

RETURN
    bitmap split by month starting the month of 'date'
'''
def SplitListByMonth(date, bitmap):
    ml = [0] + getDaysByMonth(date)
    ml = np.cumsum(ml)
    return([bitmap[ml[i - 1]:ml[i]] for i in range(1, len(ml))])



'''
DESCRIPTION

INPUT
    startDate
    endDate
RETURN
    Number of months between start and end date
'''
def getNumMonths(startDate, endDate):
    if isinstance(startDate, datetime.datetime):
        pass
    else:
        startDate = datetime.datetime.strptime(startDate, '%Y_%m_%d')
        endDate = datetime.datetime.strptime(endDate, '%Y_%m_%d')

    r = relativedelta(endDate, startDate)
    return (r.years*12 + r.months)


def getBookingCancellationBitmap(previous, current):
    if len(previous) > len(current):
        previous = previous[0:len(current)]
    else:
        current = current[0:len(previous)]

    changes=''
    for i in range(len(current)):
        if current[i] == previous[i]:
            changes = changes + current[i]
        else:
            if current[i] == '1':
                changes = changes + 'B'
            else:
                changes = changes + 'C'
    return(changes)

    ## Tried to use bitarray .. did not work ..
    '''
        print ("P=", previous)
        print ("C=", current)
        current = bitarray.bitarray(current)
        previous = bitarray.bitarray(previous)
        B = ((~ previous) & current).to01().replace('1', 'B')
        C = ((~ current) & previous).to01().replace('1', 'C')
        return(''.join(B[i] if B[i] == 'B' else C[i] for i in range(len(B))))
    '''

'''
Helper function: 
DESCRIPTION:
    Compares the occupancy between the current day and previous day and
    marks newly booked cabins with a 'B' and cancelled cabins with 'C'.
    Note, while the previous day occupancy needs to be offset by 1 day to 
    account for the change in date:
    Prev    00011101011110 ... 
    Today    0011101010101 ....

INPUT:
Data frame that contains both the previous day (bmap_diff) and current
day (occupancy). 

RETURN VALUE:

'''
####
#### SHOULD BE A MUCH EASIER WAY TO DO THIS USING APPLY ON THE DATAFRAME
####

def strbmap_diff(mydf):

    mydf.fillna('0', inplace=True)

    #dateList = mydf.index.to_list()
    new_df = pd.DataFrame(mydf.tolist(), columns=['current'],
                    index=pd.to_datetime(mydf.index, format="%Y_%m_%d"))
    #####################################################################
    #   Causing compliler problem
    #   Passing integers to fillna is deprecated, will raise a
    #   TypeError in a future version.
    #####################################################################
    if len(new_df.index) == 1:
        return (
            pd.Series(new_df['current'].to_list(), index=mydf.index.to_list()))
    else:
        new_df['diff'] = pd.Series(new_df.index.to_series().diff().\
                                   fillna(pd.Timedelta(seconds=0)).dt.days)
        new_df['previous'] = new_df['current'].shift(periods=1, fill_value='')
        new_df['previous'] = new_df.apply(lambda row: \
                                    row['previous'][row['diff']:], axis=1)
        new_df['difflist'] = new_df.apply(lambda row: \
            getBookingCancellationBitmap(row['previous'], row['current']), axis=1)

        return(pd.Series(new_df['difflist'].to_list(),
                         index=mydf.index.to_list()))


'''
DESCRIPTION 
    *** THIS MODULE NEEDS TO BE REWRITTEN ***
    The routine modifies the input cabin_df and adds a number of columns:
        tot_count - Total # days in occupancy bitmap
        occ_count - Total # days occupied
        occ_delta - Change in numbers of days occupied 
        dow - Dow of week 
        bmap_diff - 
        C - Cancellations
        B - Bookings

INPUT


RETURN


'''
def updateCabinColumns(cabin_name, cabin_df):

    if ('bmap_diff' in cabin_df.columns):
        #print ("from updateCabinColumns..unnecessarily called .. returning ")
        return()

    if 'date' in cabin_df.columns:
        cabin_df.set_index('date', inplace=True)
    cabin_df['tot_count'] = cabin_df['occupancy'].str.len()
    cabin_df['occ_count'] = cabin_df['occupancy'].str.count('1')


    today_count_list = cabin_df['occupancy'].str.slice(start=0, stop=-1).\
        str.count('1').tolist()
    # Adjust previous day to start from the next day
    prev_day_count_list = cabin_df['occupancy'].shift(
        fill_value=180*'X').str.slice(start=1).str.count('1')
    # Change in occupancy over two consecutive days
    cabin_df['occ_delta'] = np.array([m-n for m,n in zip(today_count_list,
                                                    prev_day_count_list)])
    ### FIX USE pd.to_datetime .. and days_week() to do this in one line
    cabin_df['dow'] = pd.to_datetime(cabin_df.index,format="%Y_%m_%d").\
        day_name()

    cabin_df['bmap_diff'] = strbmap_diff(cabin_df['occupancy'])
    cabin_df['C'] = cabin_df['bmap_diff'].str.count('C')
    cabin_df['B'] = cabin_df['bmap_diff'].str.count('B')

    if (cabin_name == ''):
        print ("End of updatecolumns ....", cabin_df['C'])
        exit()

'''
DESCRIPTION 


INPUT


RETURN


'''
def applyCleanupFilters(cabin_name, cabin_df):
    filt2 = (abs(cabin_df['occ_delta']) >= 15)
    filt4 = (cabin_df['B'].gt(10) & cabin_df['C'].gt(10))
    drop_list = (cabin_df.loc[(filt2 | filt4)].index)
    cabin_df.drop(drop_list, inplace=True)
    return(drop_list.values)



'''
DESCRIPTION:
    This function takes as input, the date and the scraped monthly bitmaps
    for that date. It then computes the correct number of bits that 
    should be in the bitmap and then computes the offset (i.e. the 
    difference between the number of bits in the bitmap and the number of
    bits that should be there in the bitmap based on the number of days 
    in the month. 
    
INPUT:
    cabinname: Name of the cabin for which the bitmap is applicable. 
        ONLY needed for printing logs etc. 
    date    : date in "2020_07_01" format
    bitmap  : List of occupancy bitmaps for next seven months inclusive
        of the month ['001110101....', '111010111...' .... ]

RETURN:
offset  : This is a list of offsets for each month ie. [-1,1,0,0,..] 
    starting from the partial month in the 'date' supplied in input.
    If the value is -ve means that there are LESS days in the bitmap
    than the month. So this bitmap needed to be padded with 'X'.
    If the value is +ve then there are MORE days in the bitmap than 
    the month and hence the bitmap needs to be truncated. 
    
'''
def getCorrectiveOffsets(cabinname, date, monthly_bitmaps):
    try:
        if (isinstance(date, datetime.datetime)):
            mydate = date
        else:
            mydate = datetime.datetime.strptime(date,'%Y_%m_%d')
    except ValueError as err:
        print("Problem: {}".format(err))
        return(err)

    # Remove any nan's from the end of the list.
    if (pd.isna(monthly_bitmaps[-1])):
        monthly_bitmaps = monthly_bitmaps[0:-1]

    offset = []

    numMonths = len(monthly_bitmaps)
    #logging.info('Cabin: {} {} {}'.format(cabinname, date, monthly_bitmaps))

    for n in range(0, len(monthly_bitmaps)):
        newdate = mydate+relativedelta(months=n)
        totaldays = monthrange(newdate.year, newdate.month)[1]
        daysleft = totaldays-newdate.day+1

        if (n == 0): # First Month
            offset.append(len(monthly_bitmaps[n])-daysleft) #Include today
        elif (n==6):
            offset.append(0)
        else:
            offset.append(len(monthly_bitmaps[n])-totaldays)

        '''
        if n>0 and totaldays-len(monthly_bitmaps[n]):
            logging.info('({0.year:4},{0.month:02})  {1:02} {2:02} *** {3}'.
                        format(newdate, totaldays, len(monthly_bitmaps[n]),
                                   monthly_bitmaps[n]))
        else:
            logging.info(
                '({0.year:4},{0.month:02})  {1:02} {2:02}'.format(newdate,
                                totaldays, len(monthly_bitmaps[n])))
        '''

    if (any(offset) is True):
        logging.info('Cabin: {} Date: {} Offset = {}'.
                      format(cabinname, date, offset))

    return(offset)

'''
cabin_df: 'date' is the Index, each column is the bitmap occupancy
    for the month in the form of a string '00111000101...". There
    are a total of 7 months. However for the benefit of this we 
    ONLY check bitmaps for the first 6 months. The input dataframe 
    looks like this: 
        Index       month1     month2   ...   month6    month7
        2020_04_27  01101 ..   11010..        00110..   001110..
        2020_04_28  ....        ....          ....
        2020_04_29  ....        ....          ....
        
offset  : SEE UNDER getCorrectiveOffsets

'''
'''
def checkOccupancy(cabinname, cabin_df):
    logging.info('Null found:\n{}'.format(cabin_df.isnull().sum()))
    cabin_df.fillna('', inplace=True)
    offset_dict = {'date':[], 'offset':[]}
    for (date, row) in cabin_df.iterrows():
        #logging.info('Cabin: {} Date: {}'.format(cabinname, date))
        # Check each month to see where
        offset = getCorrectiveOffsets(cabinname, date, row.tolist())
        offset_dict['date'].append(date)
        offset_dict['offset'].append(offset)
    return(offset_dict)
'''



'''
DESCRIPTION

INPUT

RETURN

'''
def fixOccupancyBitmap(cabinName, date, bitmap_list):
    #print('Inside fixOccupancyBitmap {} {} {}'.
    #    format(cabinName, date, bitmap_list))

    if (isinstance(date, datetime.datetime)):
        date_dt = date
    else:
        date_dt = datetime.datetime.strptime(date, '%Y_%m_%d')

    if (cabinName == "It\'s A Waterful Life"):
        #print (cabinName, date)
        pass

    offset_list = getCorrectiveOffsets(cabinName, date, bitmap_list)
    #date_dt = datetime.datetime.strptime(date,'%Y_%m_%d')

    ##### This HACK only for Elk Springs Resort .. also remove the 1st
    ##### character for 2020_02_29 and 2020_03_02 ...
    if (cabinName in CabinsOfInterest['elkspringsresort']):
        if (date == '2020_03_02' or date_dt.day >= 29):
            if (date in ('2020_02_29','2020_03_02')):
                ## Remove the 1st char of bitmap join and resplit
                bitmap_list = SplitListByMonth(date,
                                ''.join(x for x in bitmap_list)[1:])
            else:
                ## rejoin bitmap and resplit
                bitmap_list = SplitListByMonth(date,
                                    ''.join(str(x) for x in bitmap_list))
            return(''.join(x for x in bitmap_list))
            offset_list = getCorrectiveOffsets(cabinName, date, bitmap_list)

    if (cabinName in CabinsOfInterest['cabinsusa']):
        if (date_dt.day > 31):
            print("*** Inside corrective measure {} {}".
                  format(cabinName, date))
            ## Not clear but need to remove the 1st char of bitmap
            bitmap_list = SplitListByMonth(date,
                                ''.join(x for x in bitmap_list)[1:])
            return(bitmap_list)
            offset_list = getCorrectiveOffsets(cabinName, date, bitmap_list)

    ## APPLY MONTHLY OFFSETS

    occupancy = ''
    for i, offset in enumerate(offset_list):
        if (offset < 0):
            # +ve offset add 'X' before the bitmap
            bitmap_list[i] = abs(offset) * 'X' + bitmap_list[i]
        elif (offset > 0):
            # -ve offsets remove from end of bitmap
            bitmap_list[i] = bitmap_list[i][:-1*offset]
        occupancy = occupancy + bitmap_list[i]

    #print (occupancy)
    return (occupancy)



'''
DESCRIPTION




INPUT


RETURN

'''
def fixAllOccupancyBitmaps(cabinName, cabin_df):

    new_df = cabin_df.loc[:,'month1':'month7'].copy()
    new_df.fillna('0', inplace=True)

    new_df.index = pd.to_datetime(new_df.index, format='%Y_%m_%d')

    numMonths = getNumMonths(new_df.index[0], new_df.index[-1])

    for n in range(0, numMonths):
        nextMonth = new_df.index[0] + relativedelta(months=n+1)
        nextMonth = '{:4}-{:02}'.format(nextMonth.year, nextMonth.month)
        lastXDays = new_df[nextMonth].tail(3).index.values

        for i in range(1,len(lastXDays)):
            try:
                prev = new_df.loc[lastXDays].iloc[i-1]
                next = new_df.loc[lastXDays].iloc[i]
            except KeyError as err:
                print (err)
                continue
            for j in range(1, 7):
                ## For the 6th month if the value is '0' then replace
                ## it by the bitmap from previous month
                if j == 6:
                    r_above = fuzz.ratio(str(prev[j]), str(next[j]))
                    #print('r above = ', next, r_above, str(prev[j]), str(next[j]))
                    if (next.isnull().values.any()):
                        r_above =1
                    if (r_above < 0.50 or next[j] == '0'):
                        logging.info('{} {}: Too far from ({:3}%) .. swtiching {} month from previos day'.format(next.name, cabinName, r_above, j))
                        next[j] = prev[j]
                        new_df.loc[next.name][j] = prev[j]
                # PROBLEM: Here we are checking to see if the value
                # of the jth value of 'today' is close to the j+1th
                # value of the prev day. In that case make the change.
                else:
                    r_above = fuzz.ratio(str(prev[j]), str(next[j]))
                    r_side = fuzz.ratio(str(prev[j+1]), str(next[j]))
                    if r_side > r_above:
                        logging.info('{} {}: Closer to side ({:3}%) than above ({:2}%) .. swtiching {} month from previos day'.format(next.name, cabinName, r_side, r_above, j))
                        next[j] = prev[j]
                        new_df.loc[next.name][j] = prev[j]

    # Once all the high level fixes are done now look for missing days within
    # a month and fix them.

    return(new_df.apply(lambda row: fixOccupancyBitmap(cabinName,
                row.name, [row['month1'],
                row['month2'], row['month3'],
                row['month4'], row['month5'],
                row['month6'], row['month7']]), axis=1))

'''
DESCRIPTION
    This module reads an excel file where each tab represents a cabin
    and the information in the tab includes 'date', 'occupancy' and 
    month by month occupancy (month1, month2 etc.). 
    
    If the input flag 'cleanup' is set to True it will also run the 
    cleanup module while corrects any errors in the bitmaps (missing
    days etc. etc.). 
    
    The information read is returned in a Dictionary of dataframes 
    in the following format:
        {<cabin1_name>:[dataframe with occupancy info],
         <cabin2_name>:[dataframe with occupancy info],
         .....
        }

INPUT 
    Filename: Full pathname of file containing the data
    cleanup: True/False Flag with determines is cleanup is done

RETURN 
    Dictionary of dataframes containing information being read. The 
    dictionary key is the name of the cabin. It can be accessed
    as follows:
        for cabin_name in cabin_dict.keys():
            mydf = cabin_dict[cabin_name]
            ....

'''
def load_cabin_info(filename, FixOccupancyBitmap=True):
    print('Loading filename ... {}'.format(filename))
    cabin_info = {}
    try:
        inputWB = pd.read_excel(filename, sheet_name=None, dtype=object)
    except PermissionError as err:
        print("Error: File Open, Close file and try:", err)
        return(False)
    except FileNotFoundError as err:
        print("Warning: Input file not found ..  ", err)
        return(False)

    if (inputWB):
        print("Reading data ... ")

        for name in inputWB.keys():
            # If name starts with '__' then bypass
            if (name[0:2] == '__'):
                continue

            inputWB[name].fillna('', inplace=True)

            cabin_df = inputWB[name].copy().set_index('Date')
            cabin_df.index = pd.to_datetime(cabin_df.index, format='%Y_%m_%d')
            if ('occupancy' not in cabin_df.columns):
                print("\t\tCleaning up ... ")
                cabin_df['occupancy'] = fixAllOccupancyBitmaps(
                    name, cabin_df.loc[:,'month1':'month7'])
                cabin_df['occupancy'] = cabin_df['occupancy']\
                    .str.slice(stop=180)
            else:
                #print ('\t\tUsing occupancy ...')
                cabin_df['occupancy'] = cabin_df['occupancy']\
                    .str.slice(stop=180)
            print("\t{:30}\t\t{}\t{}\tEntries={:5}".
                  format(name, cabin_df.index[0].strftime('%Y-%m-%d'), cabin_df.index[-1].strftime('%Y-%m-%d'),
                         len(cabin_df.index)))
            cabin_info[name] = cabin_df
    else:
        print("Output file empty ..  ")
        return(False)
    return(cabin_info)


fileName = r'C:\Users\aghos\OneDrive\Desktop\output.xlsx'

if __name__ == '__main__':
    cabin_info = load_cabin_info(fileName, FixOccupancyBitmap=True)
