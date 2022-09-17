from app import app
from dash import html
from dash import dcc
from dash import dash_table
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import pandas as pd
from dash.dependencies import Input, Output, State
from app import app
from datetime import date
import os

# define template used
TEMPLATE = "plotly_white"

# define variables
YEAR = date.today().year

# import tax rate
tax_rate = pd.read_csv(os.path.join(r"C:\Users\ben_l\Desktop\Web Apps\Asset\backend","Tax Rate.csv"))
tax_rate = tax_rate.sort_values("ORDER")

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
    df_ = df.copy()
    df_.columns = df_.columns.str.capitalize()

    # get total relief
    total = df_["Value"].sum()
    df_ = pd.concat([df_, pd.DataFrame({"Relief":["Total: "],"Value":[total]})], sort=True, ignore_index=True)

    # sort
    df_ = df_.sort_values("Value")
    
    # table
    money = dash_table.FormatTemplate.money(2)
    table_fig = dash_table.DataTable(
        id="relief-table",
        columns = [
            dict(id="Relief", name="Relief"),
            dict(id="Value", name="Value", type="numeric", format=money),
        ],

        data=df_.to_dict('records'),
        sort_action="native",
        style_data= {"border":"none"},
        style_header = {'display': 'none'},
        style_cell={
        'height': 'auto',
        'whiteSpace': 'normal','textAlign': 'left',"font-size":"28px"},
        style_data_conditional=(
            [

            {
                "if":{
                    "filter_query":"{Relief} = 'Total: '",
                    "column_id":"Relief"
                },
                "textAlign":"right"
            },
            {
                "if":{
                    "filter_query":"{Relief} = 'Total: '"
                },
                "color":"#DC143C",
                "font-style":"italic",
                "font-weight":"bold",
                "font-size":"32px"
            }
            ]
        ),
        style_as_list_view=True,
        page_action="native",
        page_current= 0,
        page_size= 10,
    )

    return table_fig

# waterfall chart
def generate_waterfall(chargeable_income):
    tax_rate["CUMSUM"] = tax_rate["TAX_BRACKET"].cumsum()

    # get tax payable breakdown
    tax_payable = tax_rate[tax_rate["CUMSUM"]<=chargeable_income].copy()
    if len(tax_payable) == 0: # handle year when no tax payable
        tax_payable = tax_rate[tax_rate["ORDER"]==1].copy()

    remaining = chargeable_income - tax_payable["CUMSUM"].iloc[-1]
    if remaining > 0:
        _ = tax_rate[tax_rate["ORDER"] == tax_payable["ORDER"].max() + 1].copy()
        _["TAX_BRACKET"] = remaining
        tax_payable = pd.concat([tax_payable,_], sort = True, ignore_index=True).sort_values("ORDER")
    tax_payable["PAYABLE"] = tax_payable["TAX_BRACKET"] * tax_payable["RATE"]

    # generate waterfall
    tax_payable["x"] = tax_payable.apply(lambda row: "${:,.0f} ({:.1%})".format(row["TAX_BRACKET"], row["RATE"]), axis=1)
    tax_payable["text"] = tax_payable["PAYABLE"].map(lambda x: "+ ${:,.2f}".format(x))
    tax_payable["measure"] = "relative"

    # add total
    total_tax = tax_payable["PAYABLE"].sum()
    total = pd.DataFrame({"x":["Total"],"PAYABLE":[0], "text":["${:,.2f}".format(total_tax)], "measure":["total"]})
    tax_payable = pd.concat([tax_payable, total], sort=True, ignore_index=True, join="inner")

    waterfall_fig = go.Figure()
    waterfall_fig.add_trace(
        go.Waterfall(x = tax_payable["x"], y = tax_payable["PAYABLE"], text = tax_payable["text"],measure = tax_payable["measure"], textposition="outside",name="Tax")
    )

    # update layout
    waterfall_fig.update_layout(
        title = "Tax Payable by Tax Bracket",
        showlegend=False,
        template = TEMPLATE,
        height = 500,
        yaxis = dict(showgrid=False, visible=False)
    )

    return waterfall_fig


layout = html.Div([
    dbc.Container([
        dbc.Row([
            dbc.Col([html.H5("Select Year:")],width={"size":2,"offset":4}, align="center"),
            dbc.Col([
                dbc.Select(
                    id = "tax-year",
                    options = [{"label":y, "value":y} for y in range(YEAR-1,2018,-1)],
                    value = YEAR -1
            )], width=2),
            dbc.Col(dbc.Button("Tax Projection",href="http://127.0.0.1:8051/tax-projection",color="secondary"),width={"size":2,"offset":2})
        ], style={"margin-top":10}),
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
            dbc.Card(html.H3("Tax Reliefs", className="text-center text-primary bg-light"), body=True, color="light")
        ], style={"margin-top":20}),
        dbc.Row([
            dbc.Col(id="relief-table-container",width={"size":8}, style={"margin-top":20})
        ], align="center", justify="center"),
        html.Hr(),
        html.Br(),
        dbc.Row([
            dbc.Col(html.H2("Chargeable Income : ", style={"font-style": "italic"}), width={"size":4,"offset":2}),
            dbc.Col(html.H2(id="eq-str"), style={"font-style": "italic"}, width=4)
        ]),
        dbc.Row([dbc.Col(html.H2(id="charge-income-str", style={"font-style": "italic","text-decoration": "underline"}), width = {"size":4,"offset":6})]),
        html.Br(),
        html.Hr(),
        dbc.Row(
            dbc.Col(dcc.Graph(id="waterfall-tax"), width=8)
        , align="center", justify="center")
    ])
])


@app.callback(
    Output(component_id="tax-main-kpi", component_property="figure"),
    Output(component_id="tax-sub-kpi", component_property="figure"),
    Output(component_id="relief-table-container", component_property="children"),
    Output(component_id="eq-str", component_property="children"),
    Output(component_id="charge-income-str", component_property="children"),
    Output(component_id="waterfall-tax", component_property="figure"),
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
    relief = relief[relief["YEAR"]==year].drop(["ID","YEAR"], axis=1).copy()

    # generate chart
    main_kpi_fig, kpi_fig = generate_indicators(tax_df)
    table_fig = generate_relief_table(relief)
    
    # get chargeable income
    total_income = tax_df["INCOME"].iloc[0]
    total_rebate = relief["VALUE"].sum()
    chargeable_income = total_income - total_rebate
    eq_str = "${:,.0f} - ${:,.0f}".format(total_income, total_rebate)
    charge_income_str = "= ${:,.0f}".format(chargeable_income)

    # generate waterfall chart
    waterfall_fig = generate_waterfall(chargeable_income)

    return main_kpi_fig, kpi_fig, table_fig, eq_str, charge_income_str, waterfall_fig