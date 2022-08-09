from app import app
from dash import html
from dash import dcc
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
from dash.dependencies import Input, Output, State
from app import app
from datetime import date

# define template used
TEMPLATE = "plotly_white"

# define variables
YEAR = date.today().year

layout = html.Div([
    dbc.Container([
        dbc.Row([
            dbc.Col([html.H5("Select Year:")],width=2),
            dbc.Col([
                dbc.Select(
                    id = "tax-year",
                    options = [{"label":y, "value":y} for y in range(YEAR-1,2018,-1)],
                    value = YEAR -1
            )], width=2),
        ], align="center", justify="center", style={"margin-top":10}),
        dbc.Row([
            dbc.Card(html.H3("Income Tax", className="text-center text-primary bg-light"), body=True, color="light")
        ], style={"margin-top":20}),
        dbc.Row([
            dbc.Col(html.Div(html.H2(id="tax-title"), style={"margin-top":80}), width={"size":6, "offset":2})
        ], justify="center"),
        dbc.Row([
            dbc.Col(html.Div(html.Span("Total Annual Income:"), style={"margin-top":40, "font-size":32 }), width={"size":4, "offset":0}),
            dbc.Col(html.Div(html.Span("$100,000"), style={"margin-top":40, "font-size":32 }), width={"size":3, "offset":0})
        ]),
    ])
])


@app.callback(
    Output(component_id="tax-title", component_property="children"),
    Input(component_id="tax-year", component_property="value"),
    State(component_id="tax-store", component_property="data"),
    State(component_id="relief-store", component_property="data")
)
def update_figures(year, tax_df, relief):
    # get tax for the year
    tax_df = pd.DataFrame(tax_df)
    tax_df = tax_df[tax_df["YEAR"]==year].copy()

    # get relief for the year
    relief = pd.DataFrame(relief)
    relief = relief[relief["YEAR"]==year].copy()

    return f"{year} TAX ASSESSMENT"