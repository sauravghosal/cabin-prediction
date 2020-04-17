import pandas as pd
import numpy as np
import datetime
from calendar import monthrange
from dateutil.relativedelta import relativedelta
import logging

global_cabin_name = ""
dow = {0: "Mon", 1: "Tue", 2: "Wed", 3: "Thu", 4: "Fri", 5: "Sat", 6: "Sun"}
WriteDirectory = r'C:\Users\aghos\OneDrive\Desktop\\'
WriteFileName = r'C:\Users\aghos\OneDrive\Desktop\output.xlsx'

# Do not use the "Smoky Mountain Lodge Cabin Rental" format
cabin_of_interest = [('Smoky Mountain Lodge', 'cabinsusa'),
                     ('Grandview Theater Lodge', 'cabinsofthesmokymountains'),
                     ("It\'s A Waterful Life", 'cabinsofthesmokymountains'),
                     ('Poolin Around', 'elkspringsresort'),
                     ('Skinny Dippin', 'elkspringsresort')
                     ]

cabin_names = ['Smoky Mountain Lodge',
               'Grandview Theater Lodge',
               "It\'s A Waterful Life"]

occ_lookahead_list = [30, 60, 90, 120, 180]
cabin_info = {}
cabin = {'date': [], 'occupancybitmap': []}


def strbmap_diff(mydf):
    changes = ''
    today = mydf['occupancybitmap']
    yesterday = mydf['bmap_diff']

    strlength = min(len(today), len(yesterday)) - 1
    for i in range(strlength):
        if today[i] == yesterday[i+1]:
            changes = changes+'0'
        else:
            if today[i] == '1':
                changes = changes + 'B'
            else:
                changes = changes + 'C'

    if (0):
        if global_cabin_name == 'Smoky Mountain Lodge':
            if mydf.name in ['2020_03_19', '2020_03_20', '2020_03_21']:
                print(mydf.name)
                print(yesterday[1:])
                print(today)
                print(changes)
                print("")

    return(changes)


def load_cabin_info():
    try:
        inputWB = pd.read_excel(WriteFileName, sheet_name=None)
    except PermissionError as err:
        print("Error: File Open, Close file and try:", err)
        exit()
    except FileNotFoundError as err:
        print("Warning: Input file not found ..  ", err)
        exit()

    if (inputWB):
        print("Input file exists .. reading .... ")
        for (name, mgmt_company) in cabin_of_interest:
            if (name in inputWB.keys()):
                global_cabin_name = name
                inputWB[name]['occupancybitmap'].fillna("", inplace=True)
                cabin['date'] = inputWB[name]['date'].tolist()
                cabin['occupancybitmap'] = inputWB[name]['occupancybitmap'].tolist()
                cabin['occupancybitmap'] = [x[0:180]
                                            for x in cabin['occupancybitmap']]

                for n in occ_lookahead_list:
                    cabin[str(n)] = inputWB[name]['occupancybitmap'].\
                        apply(lambda x: x[0:n].count('1'))
                startdate, lastdate = cabin['date'][0], cabin['date'][-1]
                print("\t{}\t\t{}\t{}\tEntries={:5}".
                      format(name, startdate, lastdate, len(cabin['date'])))
                cabin_info[name] = pd.DataFrame(cabin)
    else:
        print("Output file empty ..  ")
        exit()
    return(cabin_info)


def clean_cabin_info(cabin_df):
    cabin_df['occupancybitmap'].fillna(180*'X', inplace=True)
    if 'date' in cabin_df.columns:
        cabin_df.set_index('date', inplace=True)
    cabin_df['tot_count'] = cabin_df['occupancybitmap'].str.len()
    cabin_df['occ_count'] = cabin_df['occupancybitmap'].str.count('1')
   # Adjust previous day to start from the next day
    today_count_list = cabin_df['occupancybitmap'].str.slice(start=0, stop=-1).\
        str.count('1').tolist()
    prev_day_count_list = cabin_df['occupancybitmap'].shift(
        fill_value=180*'X').str.slice(start=1).str.count('1')
    cabin_df['occ_delta'] = np.array([m-n for m, n in zip(today_count_list,
                                                          prev_day_count_list)])
    my_dow_list = pd.Series(pd.to_datetime(cabin_df.index,
                                           format="%Y_%m_%d")).dt.dayofweek.map(dow)
    cabin_df['dow'] = np.array(my_dow_list)
    cabin_df['bmap_diff'] = cabin_df['occupancybitmap'].shift(fill_value="000")
    cabin_df['bmap_diff'] = cabin_df.apply(strbmap_diff, axis=1)
    cabin_df['C'] = cabin_df['bmap_diff'].str.count('C')
    cabin_df['B'] = cabin_df['bmap_diff'].str.count('B')


def execute_cleanup(cabin_df):
    filt1 = (cabin_df.index.map(lambda x: x.split('_')[2]) == '01')
    filt2 = (abs(cabin_df['occ_delta']) >= 12)
    filt3 = (abs(cabin_df['occ_delta'] - (cabin_df['B'] - cabin_df['C'])) > 3)
    filt4 = (cabin_df['B'].gt(10) & cabin_df['C'].gt(10))
    drop_list = (cabin_df.loc[(filt1 | filt2 | filt4)].index)
    cabin_df.drop(drop_list, inplace=True)
    return()

# Take the bitmap add both padding and month breaks


def format_bitmap(date_list, bitmap_list):
    padded_occ_list = []
    if len(date_list) != len(bitmap_list):
        print("Error; Date List = {} Bitmap List = {} \
        Needs to be same length".format(len(date_list), len(bitmap_list)))
        exit()

    (start_year, start_month, start_day) = \
        list(map(int, date_list[0].split("_")))
    start = datetime.date(start_year, start_month, start_day)
    gap_insert = [monthrange(start_year, start_month)[1] - start_day + 1]
    for n in range(6):
        mydate = start+relativedelta(months=+n+1)
        gap_insert.append(monthrange(mydate.year, mydate.month)[1]
                          + 1 + gap_insert[n])

    # Only reason to do this is otherwise padded_list overwrites bitmap_list
    for n in bitmap_list:
        padded_occ_list.append(n)

    for i in range(len(bitmap_list)):
        padded_occ_list[i] = 'X'*i + padded_occ_list[i]
        for x in gap_insert:
            padded_occ_list[i] = padded_occ_list[i][:x] \
                + " " + padded_occ_list[i][x:]
    return(padded_occ_list)


def print_bitmap(start_date, end_date, cabin_name, padding=True, myfilt=True):

    try:
        cabin_df = cabin_info[cabin_name]
    except KeyError as err:
        print("ERROR: {} not found in {}".
              format(cabin_name, cabin_info.keys(), err))
        exit()

    cabin_df = cabin_df.truncate(start_date, end_date)
    # Bug in scraping software, if it is the 1st day of the month
    # then, prepend the first two characters of the previous day
    filt = (cabin_df.index.map(lambda x: x.split('_')[2]) == '01')
    cabin_df.loc[filt, 'occupancybitmap'].apply(lambda x: ".."+x)
    ##############################################################
    cabin_df['occ_padded_bitmap'] = np.array(format_bitmap(
        cabin_df.index, cabin_df['occupancybitmap'].values))

    ##############################################################
    # Only print certain values from the dataframe
    ##############################################################
    pd.set_option('display.max_rows', 2000)
    # Filter based on large delta between two consecutive days
    filt = (abs(cabin_df['occ_delta']) >= 0)
    # Filter based on difference between the delta from previous day
    # and the value derived from calculating new bookings and subtracting
    # new cancellations
    filt = abs(cabin_df['occ_delta'] - (cabin_df['B'] - cabin_df['C'])) > 3
    #filt = ((cabin_df['bmap_diff'] - abs(cabin_df['occ_delta'])) >= -1000)

    if (padding):
        print(cabin_df.loc[:, ["tot_count", 'occ_count', 'occ_delta',
                               'B', 'C', 'dow', 'occ_padded_bitmap']].rename(lambda x: x[0:3],
                                                                             axis=1))
    else:
        print(cabin_df.loc[:, ["tot_count", 'occ_count', 'occ_delta',
                               'B', 'C', 'dow', 'occupancybitmap']].rename(lambda x: x[0:3], axis=1))

    # logging.info(cabin_df.loc[filt,["tot_count", 'occ_count',
    # 'occ_delta', 'occ_padded_bitmap']].rename(lambda x: x[4:7], axis=1))


if __name__ == "__main__":
    pd.set_option('display.max_rows', 2000)
    pd.set_option('display.max_columns', 2000)
    pd.set_option('display.max_colwidth', -1)
    pd.set_option('max_rows', 5000)
    pd.set_option('display.colheader_justify', 'left')
    pd.set_option('display.width', 1000)

    logging.basicConfig(filename=WriteDirectory+'cabins_analytics.log',
                        level=logging.INFO,
                        format='%(asctime) %(message)')

    cabin_info = load_cabin_info()
    for key in cabin_info:
        global_cabin_name = key
        clean_cabin_info(cabin_info[key])
        execute_cleanup(cabin_info[key])
    print_bitmap('2020_03_15', '2020_04_30', cabin_names[0], myfilt=True)
    #print_bitmap('2020_02_02', '2020_09_15', cabin_names[1], myfilt=False)
    #print_bitmap('2020_03_05', '2020_09_15', cabin_names[2], myfilt=False)
