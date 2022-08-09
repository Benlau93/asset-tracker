from app import app
from dash import html
from dash import dcc
from dash import dash_table
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
from dash.dependencies import Input, Output, State
from app import app
from datetime import date
from dash.dash_table.Format import Format,Scheme

# define template used
TEMPLATE = "plotly_white"

# define variables
YEAR = date.today().year


# kpi
def generate_indicators(df):
    # get total income for current year
    total_income = df["INCOME"].iloc[0]

    main_kpi_fig = go.Figure()
    main_kpi_fig.add_trace(
        go.Indicator(mode="number",
                    value = total_income,
                    title = "Total Annual Income",
                    number = dict(valueformat="$,.0f")
                    )
    )

    main_kpi_fig.update_layout(
        height = 250,
        template = TEMPLATE
    )

    # get tax payable
    tax_annual = df["TAX_YEAR"].iloc[0]
    tax_month = df["TAX_MONTH"].iloc[0]

    kpi_fig = go.Figure()
    kpi_fig.add_trace(
        go.Indicator(mode="number",
                    value = tax_annual,
                    title = "Tax Payable (Annual)",
                    number = dict(valueformat="$,.02f"),
                    domain = {"row":1, "column":0}
                    )
                    
    )

    kpi_fig.add_trace(
        go.Indicator(mode="number",
                    value = tax_month,
                    title = "Tax Payable (Monthly)",
                    number = dict(valueformat="$,.02f"),
                    domain = {"row":2, "column":1}
                    )
                    
    )

    kpi_fig.update_layout(
        grid = {"rows":1, "columns":2, "pattern":"independent"},
        height = 250,
        template = TEMPLATE
    )

    return main_kpi_fig, kpi_fig


# relief table
def generate_relief_table(df):
    df = df.drop(["ID","YEAR"], axis=1).copy()
    df = df.sort_values("RELIEF")
    df.columns = df.columns.str.capitalize()

    money = dash_table.FormatTemplate.money(2)

    # table
    table_fig = dash_table.DataTable(
        id="tax-table",
        columns = [
            dict(id="Relief", name="Relief"),
            dict(id="Value", name="Value", type="numeric", format=money),
        ],

        data=df.to_dict('records'),
        sort_action="native",
        # row_selectable='single',
        style_cell={
        'height': 'auto',
        'minWidth': '180px', 'width': '180px', 'maxWidth': '180px',
        'whiteSpace': 'normal'},
        style_table={'overflowX': 'scroll'},
        style_as_list_view=True,
        page_action="native",
        page_current= 0,
        page_size= 10,
    )

    return table_fig


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
            dbc.Card(html.H3("Income Tax Assessment", className="text-center text-primary bg-light"), body=True, color="light")
        ], style={"margin-top":20}),
        dbc.Row([
            dbc.Col([dcc.Graph(id="tax-main-kpi")], width=6)
        ], justify="center"),
        dbc.Row([
            dbc.Col([dcc.Graph(id="tax-sub-kpi")], width=10)
        ], justify="center"),
        dbc.Row([
            dbc.Card(html.H3("Breakdown of Reliefs", className="text-center text-primary bg-light"), body=True, color="light")
        ], style={"margin-top":20}),
        dbc.Row([
            dbc.Col(id="tax-table",width={"size":6}, style={"margin-top":50})
        ], align="center", justify="center"),
    ])
])


@app.callback(
    Output(component_id="tax-main-kpi", component_property="figure"),
    Output(component_id="tax-sub-kpi", component_property="figure"),
    Output(component_id="tax-table", component_property="children"),
    Input(component_id="tax-year", component_property="value"),
    State(component_id="tax-store", component_property="data"),
    State(component_id="relief-store", component_property="data")
)
def update_figures(year, tax_df, relief):
    # convert to int
    year = int(year)
    # get tax for the year
    tax_df = pd.DataFrame(tax_df)
    tax_df = tax_df[tax_df["YEAR"]==year].copy()

    # get relief for the year
    relief = pd.DataFrame(relief)
    relief = relief[relief["YEAR"]==year].copy()
    print(relief)
    # generate chart
    main_kpi_fig, kpi_fig = generate_indicators(tax_df)
    table_fig = generate_relief_table(relief)

    return main_kpi_fig, kpi_fig, table_fig