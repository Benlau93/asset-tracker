from app import app
from dash import html
from dash import dcc
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import pandas as pd
from dash.dependencies import Input, Output, State
from app import app


# define template used
TEMPLATE = "plotly_white"


# main kpi
def generate_mainkpi(df):
    df = pd.DataFrame(df)
    latest_yearmonth = df[df["DATE"] == df["DATE"].max()]["YEARMONTH"].unique()[0]
    main_kpi = df[df["YEARMONTH"]==latest_yearmonth]["VALUE"].sum()

    kpi_fig = go.Figure()
    kpi_fig.add_trace(
        go.Indicator(mode="number",
                    value = main_kpi,
                    title = "Current Total Asset Value",
                    number = dict(valueformat="$,.0f"))
    )

    kpi_fig.update_layout(
        height = 250,
        template = TEMPLATE
    )

    return kpi_fig


layout = html.Div([
    dbc.Container([
        dbc.Row([
            dbc.Col([
                dcc.Graph(id="main-kpi")
            ], width = 10)
        ], justify="center"),
        dbc.Row([
            dbc.Col([dbc.Card(html.Div(), style={"background-color":"orange"})], width={"size":8}),
            dbc.Col([dbc.Card(html.Div(), style={"background-color":"yellow"})], width = {"size":2, "offset":2})
        ]),
        dbc.Row([
            dbc.Col([dbc.Card(html.Div(), style={"background-color":"green"})]),
            dbc.Col([dbc.Card(html.Div(), style={"background-color":"green"})]),
            dbc.Col([dbc.Card(html.Div(), style={"background-color":"green"})])
        ], align="justify" )
    ])
])


@app.callback(
    Output(component_id="main-kpi",component_property="figure"),
    Input(component_id="url", component_property="pathname"),
    State(component_id="df-store", component_property="data")
)
def update_graph(_,df):

    main_kpi = generate_mainkpi(df)

    return main_kpi