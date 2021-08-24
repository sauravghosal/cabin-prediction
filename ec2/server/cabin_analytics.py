import pandas as pd
import numpy as np
import datetime
from calendar import monthrange
from dateutil.relativedelta import relativedelta
import logging
from appsupport import updateCabinColumns, load_cabin_info, \
    SplitListByMonth, getDaysByMonth
import dash
import plotly.graph_objs as go
import platform
from plotly.subplots import make_subplots
from plotly.tools import get_subplots
import math
import inspect
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State
from cabinsofinterest import CabinsOfInterest


if (platform.node() == 'Anjan-New-Asus-Laptop'):
    WriteDirectory = r'C:\Users\aghos\OneDrive\Desktop\\'
    WriteFileName = r'C:\Users\aghos\OneDrive\Desktop\output.xlsx'
else:
    WriteDirectory = ''
    WriteFileName = 'output.xlsx'

occ_lookahead_list = [30, 60, 90, 120, 180]
cabin = {'date':[], 'occupancy':[]}

app = dash.Dash()


'''
DESCRIPTION
This function takes a list of dates and corresponding bitmaps and
returns a formatted bitmap for display on the screen. The bitmaps 
are padded from left with 'X' so that the occupancy maps for the 
subsequent days align when displayed on the screen

RETURN:
A list of bitmaps which are modified to include the padding. This 
may be used by the calling program to insert it into a dataframe. 

'''

## Take the bitmap add both padding and month breaks
def format_bitmap(date_list, bitmap_list):

    if len(date_list) != len(bitmap_list):
        print("Error; Date List = {} Bitmap List = {} \
        Needs to be same length".format(len(date_list),len(bitmap_list)))
        exit()

    # Convert to dataframe and add a column for padded bitmap
    mydf = pd.DataFrame(list(zip(date_list,bitmap_list)),
                        columns=['date','occupancy'])
    mydf.date = pd.to_datetime(mydf.date, format="%Y_%m_%d")
    mydf.set_index('date', inplace=True)

    #mydf['delta'] = (mydf['date'] - mydf['date'].iloc[0]).dt.days.astype(int)
    mydf['delta'] = (mydf.index - mydf.index[0]).days.astype(int)

    mydf['padded'] = 'X'
    # Compute the padding in terms of sequence of 'X'
    mydf['padded'] = mydf['padded'].str.repeat(mydf.delta.to_list())
    # Prepend padding in front of 'occupancy' column
    mydf['padded'] = mydf['padded'] + mydf['occupancy']
    # Compute list of offsets for the locations where month break
    # will be inserted
    start = date_list[0]
    start = datetime.date(start.year, start.month, start.day)
    gap_insert = [monthrange(start.year, start.month)[1] - start.day + 1]

    # After padding the string become much longer and hence you need more
    # Month breaks

    for n in range(1,24):
        mydate = start+relativedelta(months=n)
        gap_insert.append(monthrange(mydate.year, mydate.month)[1]
                          + gap_insert[n-1])

    # Insert month break into the 'occupancy'
    for i, offset in enumerate(gap_insert):
        mydf['padded'] = (mydf['padded'].str.slice(stop=i+offset) + ' '
                          + mydf['padded'].str.slice(start=i+offset))
    return (mydf.padded.to_list())

####################################################################
def splitList(source_list, split_values):
    pass
    #return ([source    for x])

# 4cc417 green #347c17 dark green
#colorscale = [[False, '#eeeeee'], [True, '#76cf63']]
colorscale = [[0.00, '#eeeeee'],
              [0.25, '#eeeeee'],
              [0.25, '#008000'],
              [0.50, '#008000'],
              [0.50, '#0000FF'],
              [0.75, '#0000FF'],
              [0.75, '#FF0000'],
              [1.00, '#FF0000']]


def draw_bitmap_multipleCabins(cabin_info):

    numCabins = len(cabin_info.keys())
    cabin_list = list(cabin_info.keys())

    ## Calculating Column Width to be used in make_subplots
    start_date = cabin_info[cabin_list[0]].index[-1]

    numWeeks = [math.ceil(x/7) for x in getDaysByMonth(start_date)][0:6]

    numWeeks1 = []
    for i in range(6):
        mydate = start_date + relativedelta(months=i)
        a, b = monthrange(mydate.year, mydate.month)
        #print(mydate, a, b, math.ceil((b - (7 - a)) / 7) + 1)
        if i == 0:
            numWeeks1.append(math.ceil(((b - start_date.day) / 7) + 1))
        else:
            numWeeks1.append(math.ceil((b - (7 - a)) / 7) + 1)

    columnWidth = [x/sum(numWeeks1) for x in numWeeks1]

    fig = make_subplots(rows=numCabins,
                        cols=6, #### Fix this absolute value
                        column_widths=columnWidth,
                        shared_yaxes=True,
                        horizontal_spacing=0.03,
                        vertical_spacing=0.03,
                        row_titles=['<b>'+x+'</b>' for x in cabin_list],
                        #column_titles=['a', 'b', 'c', 'd', 'e', 'f']
                        )

    for annotations in fig['layout']['annotations']:
        annotations['font'] = dict(size=12, color='#ff0000')

    print("List of cabins to be plotted: {}".format(cabin_list))
    for indx, cabin_name in enumerate(cabin_info):
        print('Plotting {}'.format(cabin_name))
        updateCabinColumns(cabin_name, cabin_info[cabin_name])
        mydf = cabin_info[cabin_name]
        start_date=mydf.index[-1]
        bitmap=mydf.iloc[-1,:].bmap_diff.replace('B', '2').\
                    replace('C', '3')

        subplottitle = "<b>{}({})</b>".format(cabin_name,str(bitmap.count('1')))
        #fig.update_annotations(dict(text=subplottitle))
        fig['layout']['annotations'][indx]['text'] = subplottitle

        z = [bitmap[i] for i in range(len(bitmap))]
        date_list = [start_date + datetime.timedelta(days=i)
                     for i in range(len(bitmap))]
        dow_list = [date.weekday() for date in date_list]
        text = [str(i)[0:10] for i in date_list]
        weeknumber = [i.strftime("%Gww%V") for i in date_list]

        # Get list of months for subplot label
        month_list = [(start_date + relativedelta(months=i)).strftime("%B")
                      for i in range(6)]
        z_split = SplitListByMonth(start_date, z)
        y_dow_list_split = SplitListByMonth(start_date, dow_list)
        text_split = SplitListByMonth(start_date, text)
        x_weeknumber_split = SplitListByMonth(start_date, weeknumber)
        num_months = len(month_list)
        month_list = [(start_date + relativedelta(months=i)).strftime("%B")
                      for i in range(num_months)]

        #z_split[0] = ['1','1','0', '1', '1', '0', '0']
        #y_dow_list_split[0] = [0,1,2,3,4,5,6]

        for i in range(num_months):
            fig.add_trace(go.Heatmap(
                x=x_weeknumber_split[i],
                y=y_dow_list_split[i],
                z=z_split[i],
                text=text_split[i],
                hoverinfo='text',
                #hoverongaps=False,
                xgap=3,  # this
                ygap=3,  # and this is for grid-like appearance
                showscale=False,
                zmin=0,
                zmax=3,
                colorscale=colorscale
                ),
                row=indx+1,
                col=i + 1
            )
            fig.update_xaxes(title_text=month_list[i],
                             showticklabels=False,
                             showline=False,
                             zeroline=False,
                             showgrid=False,
                             row=indx+1,
                             col=i+1)
            fig.update_yaxes(showline=True,
                             showgrid=True,
                             zeroline=True,
                             tickmode='array',
                             ticktext=['Mon','Tue','Wed','Thu','Fri','Sat','Sun'],
                             tickvals=[0, 1, 2, 3, 4, 5, 6],
                             row=indx + 1,
                             col=i + 1)
    fig.update_layout(
        font_family="Courier New",
        font_color="blue",
        font_size=12,
        title_font_family="Times New Roman",
        title_font_color="red",
        legend_title_font_color="green",
        height=3200,
        width=900,
        plot_bgcolor=('#fff'),
        margin=dict(t=40),
    )
    '''
    fig.update_layout(go.Layout(
        height=3200,
        width=900,
        plot_bgcolor=('#fff'),
        margin=dict(t=40),
        )
    )
    '''
    fig.show()
    return fig


def draw_bitmap_multipleDays(cabin_info, cabin_name, numDays):

    updateCabinColumns(cabin_name, cabin_info[cabin_name])
    mydf = cabin_info[cabin_name]


    date_list = [mydf.index[-i] for i in range(1, numDays+1)]


    ## Calculating Column Width to be used in make_subplots
    start_date = mydf.index[-1]
    numWeeks1 = []
    for i in range(6):
        mydate = start_date + relativedelta(months=i)
        a, b = monthrange(mydate.year, mydate.month)
        #print(mydate, a, b, math.ceil((b - (7 - a)) / 7) + 1)
        if i == 0:
            numWeeks1.append(math.ceil(((b - start_date.day) / 7) + 1))
        else:
            numWeeks1.append(math.ceil((b - (7 - a)) / 7) + 1)

    columnWidth = [x / sum(numWeeks1) for x in numWeeks1]
    rowHeight = [0.45 for x in range(12)]

    fig = make_subplots(rows=numDays,
                        cols=6,  #### Fix this absolute value
                        row_heights=rowHeight,
                        column_widths=columnWidth,
                        shared_yaxes=True,
                        horizontal_spacing=0.03,
                        vertical_spacing=0.03,
                        row_titles=['<b>' + x.strftime('%Y-%m-%d') + '</b>'
                                    for x in date_list],
                        #font=dict(size=12, color='#ff0000')
                        )

    fig.update_annotations(font=dict(size=10, color='#ff0000'))
    #for annotations in fig['layout']['annotations']:
    #    annotations['font'] = dict(size=12, color='#ff0000')

    print('Plotting {}'.format(cabin_name))
    for indx, date in enumerate(date_list):
        bitmap = mydf.loc[date]['bmap_diff'].replace('B', '2'). \
                replace('C', '3')

        subplottitle = "<b>{}({})</b>".format(date.strftime('%Y-%m-%d'),
                                              str(bitmap.count('1')))
        #fig.update_annotations(text=subplottitle)
        fig['layout']['annotations'][indx]['text'] = subplottitle

        z = [bitmap[i] for i in range(len(bitmap))]
        date_list = [date + datetime.timedelta(days=i)
                     for i in range(len(bitmap))]
        dow_list = [date.weekday() for date in date_list]
        text = [str(i)[0:10] for i in date_list]
        weeknumber = [i.strftime("%Gww%V") for i in date_list]

        # Get list of months for subplot label
        month_list = [(date + relativedelta(months=i)).strftime("%B")
                      for i in range(6)]
        z_split = SplitListByMonth(date, z)
        y_dow_list_split = SplitListByMonth(date, dow_list)
        text_split = SplitListByMonth(date, text)
        x_weeknumber_split = SplitListByMonth(date, weeknumber)
        num_months = len(month_list)
        month_list = [(date + relativedelta(months=i)).strftime("%B")
                      for i in range(num_months)]

        for i in range(num_months):
        #for i in range(2):

            if (i == 0):
                print(date_list[i], cabin_name, month_list[i])
                print("X values = {}".format(x_weeknumber_split[i]))
                print("Y values = {}".format(y_dow_list_split[i]))
                print("Z values = {}".format(z_split[i]))
            fig.add_trace(go.Heatmap(
                x=x_weeknumber_split[i],
                y=y_dow_list_split[i],
                z=z_split[i],
                text=text_split[i],
                hoverinfo='text',
                xgap=3,  # this
                ygap=3,  # and this is for grid-like appearance
                showscale=False,
                zmin=0,
                zmax=3,
                colorscale=colorscale
                ),
                row=indx + 1,
                col=i + 1
            )

            fig.update_xaxes(title=dict(text=month_list[i]),
                             #title_text=month_list[i],
                             showticklabels=False,
                             showline=False,
                             zeroline=False,
                             showgrid=False,
                             tickmode='array',
                             row=indx + 1,
                             col=i + 1)
            fig.update_yaxes(showline=False,
                             showgrid=False,
                             zeroline=False,
                             #title=dict(text="anjan ghosal -> ",
                             #           font=dict(family="Balto", color='red')),
                             #type=date,
                             #autorange=False,
                             rangemode='tozero',
                             tickmode='array',
                             ticktext=['Mon', 'Tue', 'Wed', 'Thu', 'Fri',
                                       'Sat', 'Sun'],
                             tickvals=[0, 1, 2, 3, 4, 5, 6],
                             ticks='',
                             row=indx + 1,
                             col=i + 1)

    fig.update_layout(
        title=cabin_name,
        title_font_family="Courier New",
        title_font_color="blue",
        #title_font_color="black",
        legend=(dict(title=dict(text='this is legend text'))),
        #legend_title_font_color="pink",
        font_size=12,
        #title_font_family="Times New Roman",
        height=2400,
        width=900,
        plot_bgcolor=('#fff'),
        margin=dict(t=40),
    )

    fig.show()
    return fig


def draw_bitmap(cabin_name, start_date, bitmap):
    #print("Inside draw_bitmap .. cabin name={} start_date={} bitmap={}".
    #      format(cabin_name, start_date, bitmap))
    try:
        dt_start_date = start_date
        #dt_start_date = datetime.datetime.strptime(start_date, "%Y_%m_%d")
    except ValueError as err:
        print("In draw_bitmap: {}".format(err))
        return()

    cabin_name = "{} {} ({}/{} days booked)".format(cabin_name, start_date,
                                str(bitmap.count('1')), str(len(bitmap)))

    z = [bitmap[i] for i in range(len(bitmap))]
    date_list = [dt_start_date + datetime.timedelta(days=i)
                 for i in range(len(bitmap))]

    # Get list of months for subplot label
    month_list = [(dt_start_date + relativedelta(months=i)).strftime("%B")
                  for i in range(6)]

    dow_list = [date.weekday() for date in date_list]
    weeknumber = [i.strftime("%Gww%V")for i in date_list]
    text = [str(i)[0:10] for i in date_list]

    z_split = SplitListByMonth(start_date, z)
    y_dow_list_split = SplitListByMonth(start_date, dow_list)
    text_split = SplitListByMonth(start_date, text)
    x_weeknumber_split = SplitListByMonth(start_date, weeknumber)

    num_months = len(month_list)

    # Create six subplots .. one for each month
    fig = make_subplots(cols=num_months,
                        column_widths=[0.01, 0.15, 0.15, 0.15, 0.15, 0.15],
                        shared_yaxes=True,
                        horizontal_spacing=0.02)

    # Create month_list and x-axis titles for each subplot
    # Weird way to set up the x-axis titles of each subplot
    month_list = [(dt_start_date + relativedelta(months=i)).strftime("%B")
                  for i in range(num_months)]
    for i in range(num_months):
        fig['layout']['xaxis'+str(i+1)]['title'] = month_list[i]

    # Insert heatmap of each month in each subplot
    for i in range(num_months):
        fig.append_trace(go.Heatmap(
                    x=x_weeknumber_split[i],
                    y=y_dow_list_split[i],
                    z=z_split[i],
                    text=text_split[i],
                    hoverinfo='text',
                    xgap=3,  # this
                    ygap=3,  # and this is for grid-like apperance
                    showscale=False,
                    zmin=0,
                    zmax=3,
                    colorscale=colorscale
                    ),
            row=1, col=i+1
        )

    fig.update_xaxes(showticklabels=False)
    fig.update_layout(go.Layout(
            html="this is that",
            title=cabin_name,
            height=280,
            width=900,
            yaxis=dict(
                showline=False,
                showgrid=False,
                zeroline=False,
                tickmode='array',
                ticktext=['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
                tickvals=[0, 1, 2, 3, 4, 5, 6],
            ),
            xaxis=dict(
                showline=False,
                showgrid=False,
                zeroline=False,
            ),
            plot_bgcolor=('#fff'),
            margin=dict(t=40),
        ))

    fig.show()
    return fig

'''
DESCRIPTION:
This module takes the cabin_name, start_date, end_date and prints out a 
padded display of the occupancy. It invokes the format_bitmap to get the
padding into the bitmaps. 

One key function of this module is to 'filter' out dates with bad data. It
uses various filters for doing this cleaning up. 

RETURN:
'''
def print_bitmap(cabin_name, start_date, end_date, padding=True, myfilt=True):
    try:
        cabin_df = cabin_info[cabin_name]
    except KeyError as err:
        print("ERROR: {} not found in {}".
              format(cabin_name, cabin_info.keys(), err))
        return()
    startDate = datetime.datetime.strptime(start_date, '%Y_%m_%d')
    endDate = datetime.datetime.strptime(end_date, '%Y_%m_%d')

    cabin_df = cabin_df[startDate:endDate]
    ##############################################################

    cabin_df['occ_padded_bitmap'] = np.array(format_bitmap(
        cabin_df.index, cabin_df['occupancy'].values))

    ##############################################################
    # Only print certain values from the dataframe
    ##############################################################
    pd.set_option('display.max_rows', 2000)

    if (padding):
        print(cabin_df.loc[:,["tot_count", 'occ_count','occ_delta','B', 'C',
        'dow', 'occ_padded_bitmap']].rename(lambda x: x[0:3], axis=1))
    else:
        print(cabin_df.loc[:,["tot_count", 'occ_count','occ_delta',
        'B', 'C','dow', 'occupancy']].rename(lambda x: x[0:3], axis=1))

    #logging.info(cabin_df.loc[filt,["tot_count", 'occ_count',
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

    cabin_info = load_cabin_info(WriteFileName, FixOccupancyBitmap=True)
    for cabin_name in cabin_info:
        cabin_df = cabin_info[cabin_name]
        updateCabinColumns(cabin_name, cabin_info[cabin_name])

    draw_bitmap_multipleCabins(cabin_info)
    draw_bitmap_multipleDays(cabin_info, "It\'s A Waterful Life", 12)

    if (1):
        draw_bitmap_multipleDays(cabin_info, 'Mountain Pool and Views', 12)
        draw_bitmap_multipleDays(cabin_info, 'Smoky Mountain Splash', 12)
        draw_bitmap_multipleDays(cabin_info, 'The Watering Hole', 12)
        draw_bitmap_multipleDays(cabin_info, 'The Swimming Hole', 12)
        draw_bitmap_multipleDays(cabin_info, 'Glacier Falls', 12)
        draw_bitmap_multipleDays(cabin_info, 'Majestic Waters', 12)
        draw_bitmap_multipleDays(cabin_info, 'Splash Mansion', 12)
        draw_bitmap_multipleDays(cabin_info, 'Grandview Theater Lodge', 12)
        draw_bitmap_multipleDays(cabin_info,'Smoky Mountain Lodge', 12)
        #draw_bitmap_multipleDays(cabin_info, 'Queen of Hearts ', 12)


    for cabin_name in cabin_info:
        cabin_df = cabin_info[cabin_name]
        updateCabinColumns(cabin_name, cabin_info[cabin_name])

        # Print the daily occupancy bitmap with padding
        #print("\nCabin Name: {}".format(cabin_name))
        #print_bitmap(cabin_name, '2020_07_23', '2021_06_02', myfilt=True)

        mydf = cabin_info[cabin_name]
        #draw_bitmap(cabin_name, mydf.index[-1],
        #            mydf.iloc[-1,:].bmap_diff.replace('B', '2').
        #            replace('C', '3'))

