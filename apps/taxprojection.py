from app import app
from dash import html
from dash import dcc
from dash import dash_table
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import pandas as pd
from dash.dependencies import Input, Output, State
from .tax import generate_indicators, generate_relief_table, generate_waterfall
from app import app
from datetime import date

# define template used
TEMPLATE = "plotly_white"

# define variables
YEAR = date.today().year
MONTH = date.today().month - 1

layout = html.Div([
    dbc.Container([
        dbc.Row([
            dbc.Col([html.H5("Select Projection:")],width={"size":2,"offset":3}, align="center"),
            dbc.Col([
                    dbc.RadioItems(
                        id="projection-radios",
                        className="btn-group",
                        inputClassName="btn-check",
                        labelClassName="btn btn-outline-success",
                        labelCheckedClassName="active",
                        options=[
                            {"label": "To-Date", "value": "To-Date"},
                            {"label": "EOY", "value": "EOY"}
                        ],
                        value="To-Date")
            ], width=3),
            dbc.Col(dbc.Button("Historical Tax",href="http://127.0.0.1:8051/tax",color="secondary"),width={"size":2,"offset":2})
        ], style={"margin-top":10}),
        dbc.Row(dbc.Col(html.H1(f"{YEAR}", style={"font-size":"80px","font-weight":"bold","color":"#2898d8","text-align":"center","margin":"10px","font-family": "Times New Roman"})), align="center",justify="center"),
        dbc.Row([
            dbc.Card(html.H3("Income Tax Projection", className="text-center text-primary bg-light"), body=True, color="light")
        ], style={"margin-top":20}),
        dbc.Row([
            dbc.Col([dcc.Graph(id="project-main-kpi")], width=6)
        ], justify="center"),
        dbc.Row([
            dbc.Col([dcc.Graph(id="project-sub-kpi")], width=10)
        ], justify="center"),
        dbc.Row([
            dbc.Card(html.H3("Tax Reliefs Projection", className="text-center text-primary bg-light"), body=True, color="light")
        ], style={"margin-top":20}),
        dbc.Row([
            dbc.Col(id="project-table-container",width={"size":8}, style={"margin-top":20}),
        ], align="center", justify="center"),
        dbc.Row([dbc.Col(html.P("*denote projected relief values"))]),
        html.Hr(),
        html.Br(),
        dbc.Row([
            dbc.Col(html.H2("Chargeable Income : ", style={"font-style": "italic"}), width={"size":4,"offset":2}),
            dbc.Col(html.H2(id="project-eq-str"), style={"font-style": "italic"}, width=4)
        ]),
        dbc.Row([dbc.Col(html.H2(id="project-charge-income-str", style={"font-style": "italic","text-decoration": "underline"}), width = {"size":4,"offset":6})]),
        html.Br(),
        html.Hr(),
        dbc.Row(
            dbc.Col(dcc.Graph(id="waterfall-project"), width=8)
        , align="center", justify="center")
    ])
])


@app.callback(
    Output(component_id="project-main-kpi", component_property="figure"),
    Output(component_id="project-sub-kpi", component_property="figure"),
    Output(component_id="project-table-container", component_property="children"),
    Output(component_id="project-eq-str", component_property="children"),
    Output(component_id="project-charge-income-str", component_property="children"),
    Output(component_id="waterfall-project", component_property="figure"),
    Input(component_id="projection-radios", component_property="value"),
    State(component_id="income-store", component_property="data"),
    State(component_id="relief-store", component_property="data")
)
def update_figures(projection, income_df, relief):
    # get income for the year
    income_df = pd.DataFrame(income_df)
    income_df["YEARMONTH"] = pd.to_datetime(income_df["YEARMONTH"], format="%b %Y")
    income_df = income_df[(income_df["YEARMONTH"].dt.year==YEAR) & (income_df["REF"]!="B")][["YEARMONTH","TYPE","VALUE_EMPLOYEE"]].copy()

    if projection == "EOY":
        month = 12
        monthly_income = income_df.groupby("YEARMONTH").sum()["VALUE_EMPLOYEE"].mean()
        eoy_income, cpf_projection = (12 - MONTH) * monthly_income, (12 - MONTH) * 1200 if monthly_income >= 6000 else monthly_income *0.2
        year_project = pd.to_datetime(f"Dec {YEAR}", format="%b %Y")
        income_df = pd.concat([income_df, pd.DataFrame({"YEARMONTH":[year_project]*2,
                                                        "TYPE":["Salary","CPF"],"VALUE_EMPLOYEE":[eoy_income,cpf_projection]})], sort=True, ignore_index=True)
    else:
        month = MONTH

    # get relief for the year
    relief = pd.DataFrame(relief)
    relief = relief[relief["YEAR"]==YEAR][["RELIEF","VALUE"]].copy()
    # project standard relief
    cpf_relief = min(income_df[income_df["TYPE"]!="Salary"]["VALUE_EMPLOYEE"].sum(), 20400)
    donation_relief = month * 5 * 2.5
    relief_project = pd.DataFrame({"RELIEF":["Provident Fund/ Life Insurance*","Donation*","NSman-self/ wife/ parent*"],"VALUE":[cpf_relief,donation_relief,1500]})
    # append to main relief df
    relief = pd.concat([relief,relief_project], sort=True, ignore_index=True)

    # get chargeable income
    total_income = income_df[income_df["TYPE"]!="CPF"]["VALUE_EMPLOYEE"].sum()
    total_rebate = min(relief["VALUE"].sum(),80000)
    chargeable_income = total_income - total_rebate
    eq_str = "${:,.0f} - ${:,.0f}".format(total_income, total_rebate)
    charge_income_str = "= ${:,.0f}".format(chargeable_income)

    # generate waterfall chart and get total tax payable
    waterfall_fig, payable = generate_waterfall(chargeable_income)
    
    # simulate tax df
    tax_df = pd.DataFrame({"INCOME":[total_income],"TAX_YEAR":[payable],"TAX_MONTH":[payable/12]})

    # generate chart
    main_kpi_fig, kpi_fig = generate_indicators(tax_df)
    table_fig = generate_relief_table(relief)
    
    return main_kpi_fig, kpi_fig, table_fig, eq_str, charge_income_str, waterfall_fig