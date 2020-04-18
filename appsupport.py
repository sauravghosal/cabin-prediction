import pandas as pd
import numpy as np

dow = {0: "Mon", 1:"Tue", 2:"Wed", 3:"Thu", 4:"Fri", 5:"Sat", 6:"Sun"}

def strbmap_diff(mydf):
    changes=''
    today = mydf['occupancy']
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

    return(changes)


def clean_cabin_info(cabin_df):
    cabin_df['occupancy'].fillna(180*'X', inplace=True)
    if 'date' in cabin_df.columns:
        cabin_df.set_index('date', inplace=True)
    cabin_df['tot_count'] = cabin_df['occupancy'].str.len()
    cabin_df['occ_count'] = cabin_df['occupancy'].str.count('1')
   #Adjust previous day to start from the next day
    today_count_list = cabin_df['occupancy'].str.slice(start=0, stop=-1).\
        str.count('1').tolist()
    prev_day_count_list = cabin_df['occupancy'].shift(
        fill_value=180*'X').str.slice(start=1).str.count('1')
    cabin_df['occ_delta'] = np.array([m-n for m,n in zip(today_count_list,
                                                         prev_day_count_list)])
    my_dow_list = pd.Series(pd.to_datetime(cabin_df.index,
                                format="%Y_%m_%d")).dt.dayofweek.map(dow)
    cabin_df['dow'] = np.array(my_dow_list)
    cabin_df['bmap_diff'] = cabin_df['occupancy'].shift(fill_value="000")
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

