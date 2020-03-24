import plotly.graph_objs as go
import dash
from dash.dependencies import Input, Output
import dash_core_components as dcc
import dash_html_components as html
import os
import base64
import math


import pandas as pd
import numpy as np

app = dash.Dash(__name__)

colors = {"graphBackground": "#F5F5F5",
          "background": "#ffffff", "text": "#000000"}


def parse_data(name='output1.xlsx'):
    sheets = pd.ExcelFile(name).book.sheets()
    data = []
    for i, sheet in enumerate(sheets):
        if sheet.visibility:
            continue
        if sheet.name != 'Smoky Mountain Lodge' and sheet.name != 'Grandview Theater Lodge':
            continue
        df = pd.read_excel(name, sheet_name=sheet.name,)
        df = df.drop(columns=df.columns.values[0])
        df['date'] = pd.to_datetime(
            df.loc[:, 'date'], format="%Y_%m_%d", errors='coerce')
        df.dropna()
        df['30day'] = df['occupancybitmap'].str[:29].str.count("1")
        df['60day'] = df['occupancybitmap'].str[:59].str.count("1")
        df['90day'] = df['occupancybitmap'].str[:89].str.count("1")
        df['Year'] = df['date'].dt.year
        df['Month'] = df['date'].dt.month_name()
        df['Cabin'] = sheet.name
        data.append(df)
    return pd.concat(data)


def layout():
    df_main = parse_data()
    lookahead_options = [{'label': '30day', 'value': '30day'}, {
        'label': '60day', 'value': '60day'}, {'label': '90day', 'value': '90day'}]
    year_options = [{'label': i, 'value': i}
                    for i in df_main['Year'].unique() if not math.isnan(i)]
    return html.Div([
        html.Div(
            className='container',
            children=[
                dcc.Checklist(
                    options=lookahead_options,
                    value=['30day', '60day', '90day'],
                    id='select-lookahead',
                    className='select-lookahead',
                ),
                html.Div(
                    dcc.Graph(id='plot', className='plot')),
                dcc.Checklist(
                    options=year_options,
                    value=list(df_main['Year'].unique())[:2],
                    id='select-year',
                    className='select-year',
                ),
            ],
        ),

        html.H4('', id='filename',),
        dcc.Upload(
            id='upload',
            children=html.Div(
                ['Drag and Drop or ', html.A('Select File')]),
            style={
                'width': '100%',
                'height': '60px',
                'lineHeight': '60px',
                'borderWidth': '1px',
                'borderStyle': 'dashed',
                'borderRadius': '5px',
                'textAlign': 'center',
                'margin': '10px',
            },
        ),
    ])


app.layout = layout()


@app.callback(
    [
        Output('select-year', 'options'),
        Output('filename', 'children'),
    ],
    [Input('upload', 'contents'), Input('upload', 'filename')],
)
def update_output(contents, filename):
    if contents:
        try:
            data = contents.encode("utf8").split(b";base64,")[1]
            with open('input2.xlsx', 'wb') as fp:
                fp.write(base64.decodebytes(data))
            df_main = parse_data('input2.xlsx')
        except Exception:
            df_main = parse_data('output1.xlsx')
            year_options = [{'label': i, 'value': i}
                            for i in df_main['Year'].unique() if not math.isnan(i)]
            return [year_options, 'File upload errored. Please Reupload']
        with open('input.xlsx', 'wb') as fp:
            fp.write(base64.decodebytes(data))
    df_main = parse_data()
    year_options = [{'label': i, 'value': i}
                    for i in df_main['Year'].unique() if not math.isnan(i)]
    return [year_options, filename]


# need to work on updating and drawing the graph when buttons selected
# how do i display information?
@app.callback(
    Output('plot', 'figure'),
    [Input('select-year', 'value'), Input('select-lookahead', 'value')],
)
def update_plot(years, lookAhead):
    data = []
    df_main = parse_data()
    cabins = list(df_main['Cabin'].unique())
    for cabin in cabins:
        dates = [df_main['Year'].eq(int(year)) for year in years]
        accumulated_dates = 0
        for date in dates:
            accumulated_dates = np.logical_or(accumulated_dates, date)
        lookahead_data = df_main[accumulated_dates &
                                 (df_main['Cabin'] == cabin)][lookAhead]
        for day in lookAhead:
            data.append(
                go.Scatter(
                    x=df_main[accumulated_dates & (
                        df_main['Cabin'] == cabin)]['date'],
                    y=lookahead_data[day],
                    name=str(day) + ' look ahead for ' + str(cabin),
                    line=dict(width=2),
                    hoverinfo='y',
                )
            )
    layout = go.Layout(
        title='Cabin Rental Prediction Software', hovermode='closest')
    fig = go.Figure(data=data, layout=layout)
    fig.update_yaxes(hoverformat=".2f")
    return fig


if __name__ == '__main__':
    app.run_server(debug=True)
