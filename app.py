import numpy as np
import plotly.graph_objs as go
import dash
from dash.dependencies import Input, Output
import dash_core_components as dcc
import dash_html_components as html
import os
import base64
import math
from cabin_analytics import clean_cabin_info, strbmap_diff, execute_cleanup
import pandas as pd

my_color = [['#10D6CE', '#103CD6', '#3810D6'],
            ['#DC0209', '#AF195B', '#9F19AF'],
            ['#08764C', '#09D208', '#77D208']]


global_data = "This is global data"
column_names = []
df_main = pd.DataFrame(columns=column_names)

app = dash.Dash()
server = app.server


def parse_data(name='output.xlsx'):
    sheets = pd.ExcelFile(name).book.sheets()
    print("Parsing data .... ")
    data = []
    for i, sheet in enumerate(sheets):
        if sheet.visibility:
            continue

        df = pd.read_excel(name, sheet_name=sheet.name,)

        # Remove bad data here ..
        clean_cabin_info(df)
        execute_cleanup(df)

        df = df.drop(columns=df.columns.values[0])
        if df.empty:
            continue
        df['date'] = pd.to_datetime(
            df.index, format="%Y_%m_%d", errors='coerce')
        df.dropna(inplace=True)
        df['30day'] = df.loc[:, "occupancybitmap"].str[:30].str.count(
            '1').fillna(0).map(int)
        df['60day'] = df.loc[:, "occupancybitmap"].str[:60].str.count(
            "1").fillna(0).map(int)
        df['90day'] = df.loc[:, "occupancybitmap"].str[:90].str.count(
            "1").fillna(0).map(int)
        df['120day'] = df.loc[:, "occupancybitmap"].str[:120].str.count(
            "1").fillna(0).map(int)
        df['180day'] = df.loc[:, "occupancybitmap"].str[:180].str.count(
            "1").fillna(0).map(int)
        df['Cabin'] = sheet.name
        df['Year'] = df['date'].dt.year
        # move all dates to year 2000 to allow for graph overlay
        df['date'] = df['date'].apply(lambda dt: dt.replace(year=2000))
        data.append(df)
    return pd.concat(data)


def layout():
    df_main = parse_data()
    lookahead_options = [{'label': '30day', 'value': '30day'},
                         {'label': '60day', 'value': '60day'},
                         {'label': '90day', 'value': '90day'},
                         {'label': '120day', 'value': '120day'},
                         {'label': '180day', 'value': '180day'}]
    cabin_options = [{'label': i, 'value': i}
                     for i in df_main['Cabin'].unique()]
    year_options = [{'label': i, 'value': i}
                    for i in df_main['Year'].unique()]
    year_options.sort(key=lambda item: item['value'], reverse=True)
    return html.Div([
        html.Div(
            className="page-content",
            children=[
                html.H1("Ghosal RE Cabin Rental Predictor"),

                html.Div(
                    className="graph-container",
                    children=[
                        dcc.Graph(id='plot', className='plot')
                    ],
                ),
                html.Div(
                    className='container',
                    children=[
                        dcc.Checklist(
                            options=lookahead_options,
                            value=['30day'],
                            id='select-lookahead',
                            className='select-lookahead',
                        ),


                        dcc.Checklist(
                            options=cabin_options,
                            value=list(df_main['Cabin'].unique()),
                            id='select-cabin',
                            className='select-cabin'
                        ),
                        dcc.Checklist(
                            options=year_options,
                            value=sorted(list(df_main['Year'].unique()),
                                         reverse=True)[:1],
                            id='select-year',
                            className='select-year',
                        ),

                    ],
                    style={
                        'display': 'flex',
                        'flex-direction': 'row',
                        'justifyContent': 'space-around'
                    }
                ),

                dcc.Upload(
                    id='upload',
                    children=html.Div(
                        ['Drag and Drop or ', html.A('Select File')]),
                    style={
                        'width': '100%',
                        'margin': '30px',
                        'height': '60px',
                        'lineHeight': '60px',
                        'borderWidth': '1px',
                        'borderStyle': 'dashed',
                        'borderRadius': '5px',
                        'textAlign': 'center',
                    },
                ),

            ],
            style={
                'display': 'flex',
                'flex-direction': 'column',
                'justifyContent': 'space-around'
            })
    ])


app.layout = layout()


@app.callback(
    [
        Output('select-cabin', 'options'),
        Output('select-year', 'options'),
        Output('upload', 'style'),
    ],
    [Input('upload', 'contents'), Input('upload', 'filename')],


)
def update_output(contents, filename):
    style = {'width': '100%',
             'margin': '30px',
             'height': '60px',
             'lineHeight': '60px',
             'borderWidth': '1px',
             'borderStyle': 'dashed',
             'borderRadius': '5px',
             'textAlign': 'center',
             }
    if contents:
        try:
            data = contents.encode("utf8").split(b";base64,")[1]
            with open('output1.xlsx', 'wb') as fp:
                fp.write(base64.decodebytes(data))
            df_main = parse_data('output1.xlsx')
            style['backgroundColor'] = 'green'
        # fallback
        except:
            df_main = parse_data()
            cabin_options = [
                {'label': i, 'value': i} for i in df_main['Cabin'].unique()
            ]
            year_options = [{'label': i, 'value': i}
                            for i in df_main['Year'].unique()]
            year_options.sort(key=lambda item: item['value'], reverse=True)
            style['backgroundColor'] = 'red'
            return [cabin_options, year_options, style]
        with open('output.xlsx', 'wb') as fp:
            fp.write(base64.decodebytes(data))
    df_main = parse_data()
    cabin_options = [{'label': i, 'value': i}
                     for i in df_main['Cabin'].unique()]
    year_options = [{'label': i, 'value': i}
                    for i in df_main['Year'].unique()]
    year_options.sort(key=lambda item: item['value'], reverse=True)
    return [cabin_options, year_options, style]


# need to work on updating and drawing the graph when buttons selected
# how do i display information?
@app.callback(
    Output('plot', 'figure'),
    [Input('select-year', 'value'), Input('select-lookahead',
                                          'value'), Input('select-cabin', 'value')]
)
def update_plot(years, lookAhead, cabins):
    #print (global_data)
    data = []
    #df_main = parse_data()
    for a, cabin in enumerate(cabins):
        for b, year in enumerate(years):
            for day in lookAhead:
                data.append(
                    go.Scatter(
                        x=df_main[(df_main['Year'] == int(year)) &
                                  (df_main['Cabin'] == cabin)
                                  ]['date'],
                        y=df_main[(df_main['Year'] == int(year)) &
                                  (df_main['Cabin'] == cabin)][day],
                        name=str(day) + '-' + str(year)+'-'+str(cabin)[0:20],
                        line=dict(width=2),
                        hoverinfo='y+x',
                        mode='lines+markers',
                        # marker=dict(color=my_color[(a%3)][(b%3)])
                    )
                )
    layout = go.Layout(
        title='Cabin Occupancy Predictor', hovermode='closest')
    fig = go.Figure(data=data, layout=layout)
    fig.update_layout(xaxis_tickformat='%d %b', autosize=True,  width=1500,
                      height=450,  xaxis_title="Dates",
                      yaxis_title="Bookings",)
    fig.update_yaxes(hoverformat="@x{int}", ticksuffix=" days")
    return fig


if __name__ == '__main__':
    df_main = parse_data()
    app.run_server(debug=True)
