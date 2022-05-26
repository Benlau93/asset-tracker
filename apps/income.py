from app import app
from dash import html
from dash import dcc
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
from dash.dependencies import Input, Output, State
from app import app
from dateutil.relativedelta import relativedelta
from datetime import date


# define template used
TEMPLATE = "plotly_white"

# define variables
YEAR = date.today().year


def generate_indicators(df):
    # get total income for current year
    income_kpi = df["VALUE"].sum()
    cash_kpi = df[df["TYPE"].isin(["DSTA SALARY","DSTA SUPPLEMENT"])]["VALUE"].sum()
    cpf_kpi = income_kpi - cash_kpi

    kpi_fig = go.Figure()
    kpi_fig.add_trace(
        go.Indicator(mode="number",
                    value = income_kpi,
                    title = "Total Income",
                    number = dict(valueformat="$,.0f"),
                    domain = {"row":0, "column":0}
                    )
    )

    kpi_fig.add_trace(
        go.Indicator(mode="number",
                    value = cash_kpi,
                    title = "Total Cash",
                    number = dict(valueformat="$,.0f"),
                    domain = {"row":1, "column":0}
                    )
                    
    )

    kpi_fig.add_trace(
        go.Indicator(mode="number",
                    value = cpf_kpi,
                    title = "Total CPF",
                    number = dict(valueformat="$,.0f"),
                    domain = {"row":2, "column":0}
                    )
                    
    )

    kpi_fig.update_layout(
        grid = {"rows":3, "columns":1, "pattern":"independent"},
        height = 750,
        template = TEMPLATE
    )

    return kpi_fig

def generate_trend(df):

    # find unique years
    uni_years = df.sort_values(["YEARMONTH"], ascending=False)["YEARMONTH"].dt.year.unique()

    # sum value for each yearmonth
    df = df.groupby(["YEARMONTH"]).sum()[["VALUE"]].reset_index()
    first = True
    # get max value for tixk
    max_tick = df["VALUE"].max() * 1.1

    trend_fig = go.Figure()

    # add line chart for each year
    for y in uni_years:

        # filter data
        _ = df[df["YEARMONTH"].dt.year == y].copy()

        # determine mode
        mode =  "lines+markers+text" if first else  "lines+markers"
        first = False
        trend_fig.add_trace(
            go.Scatter(x=_["YEARMONTH"].dt.strftime("%b"), y=_["VALUE"], mode = mode, texttemplate  = "%{y:$,.0f}" ,textposition="bottom right", name=str(y))
        )

    trend_fig.update_xaxes(showgrid=False)
    trend_fig.update_yaxes(tickformat = "$,.0f", range=[0,max_tick])

    trend_fig.update_layout(
        title = "Income Trends by Year, Month",
        legend = {"orientation":"h", "title":"Year", "yanchor":"bottom", "xanchor":"right","y":1, "x":1},
        template = TEMPLATE,
        height=750
    )
    
    return trend_fig


def generate_type_fig(df):

    # sum by type
    df = df.groupby("TYPE").sum()[["VALUE"]].reset_index().sort_values(["VALUE"], ascending=True)

    type_fig = go.Figure()

    type_fig.add_trace(
        go.Bar(x= df["VALUE"], y=df["TYPE"],orientation="h", hovertemplate = "Total: %{x:$,.0f}", name="Type")
    )

    type_fig.update_xaxes(showgrid=False, visible=False)
    type_fig.update_layout(
        title = "Distribution by Income Type",
        height = 300,
        template = TEMPLATE
    )

    return type_fig



layout = html.Div([
    dbc.Container([
        dbc.Row([
            dbc.Col([html.H5("Select Year:")],width=2),
            dbc.Col([
                dbc.Select(
                    id = "year-selection",
                    options = [{"label":y, "value":y} for y in range(2021,YEAR+1)],
                    value = YEAR
            )], width=2),
            dbc.Col([html.H5("Select Type:")],width=2),
            dbc.Col([
                    dbc.RadioItems(
                        id="type-radios",
                        className="btn-group",
                        inputClassName="btn-check",
                        labelClassName="btn btn-outline-primary",
                        labelCheckedClassName="active",
                        options=[
                            {"label": "All", "value": "All"},
                            {"label": "Cash", "value": "Cash"},
                            {"label": "CPF", "value": "CPF"}
                        ],
                        value="All")
            ], width=2)
        ], align="center", justify="center", style={"margin-top":10}),
        dbc.Row([
            dbc.Card(html.H3("Income Analysis", className="text-center text-primary bg-light"), body=True, color="light")
        ], style={"margin-top":20}),
        dbc.Row([
            dbc.Col([dcc.Graph(id="income-kpi")], width=3),
            dbc.Col([dcc.Graph(id="trend-kpi")], width=5),
            dbc.Col([
                dbc.Row(dbc.Col([dcc.Graph(id="type-chart")])),
                dbc.Row(dbc.Col(dbc.Card(style={"background-color":"orange"}))),
                dbc.Row(dbc.Col(dbc.Card(style={"background-color":"orange"}))),
                ], width=4)
        ])
    ])
])




@app.callback(
    Output(component_id="income-kpi", component_property="figure"),
    Output(component_id="trend-kpi", component_property="figure"),
    Output(component_id="type-chart", component_property="figure"),
    Input(component_id="year-selection",component_property="value"),
    Input(component_id="type-radios", component_property="value"),
    State(component_id="bank-store", component_property="data"),
    State(component_id="cpf-store", component_property="data")
)
def update_graph(year,type,bank, cpf):

    # process selector
    year = int(year)

    # convert to dataframe
    bank = pd.DataFrame(bank)
    cpf = pd.DataFrame(cpf)

    # process bank statement
    bank["DATE"] = pd.to_datetime(bank["DATE"])
    bank_income = bank[bank["BANK_TYPE"].isin(["DSTA SUPPLEMENT","DSTA SALARY"])].drop(["DATE","id"], axis=1).rename({"BANK_TYPE":"TYPE"},axis=1) # filter to income
    
    # process cpf
    cpf["DATE"] = pd.to_datetime(cpf["DATE"])
    cpf_income = cpf[(cpf["CODE"]=="CON") & (cpf["REF"].isin(["A","B"]))].drop(["DATE","REF","CODE","ID"], axis=1).copy() # filter to cpf contribution from dsta income
    cpf_income = cpf_income.groupby("YEARMONTH").sum().reset_index() # combine REF A and B
    cpf_income = cpf_income.melt(id_vars=["YEARMONTH"], value_name = "VALUE", var_name = "TYPE")

    # combine both sources
    income = pd.concat([bank_income, cpf_income], sort=True, ignore_index=True)
    income["YEARMONTH"] = pd.to_datetime(income["YEARMONTH"], format="%b %Y")
    income["YEARMONTH"] = income["YEARMONTH"].map(lambda x: x + relativedelta(months=1) - relativedelta(days=1))

    # filters
    income_year = income[income["YEARMONTH"].dt.year==year].copy()
    
    if type =="CPF":
        income_type = income[income["TYPE"].isin(["OA","SA","MA"])].copy()
        income_year_type = income[(income["TYPE"].isin(["OA","SA","MA"])) & (income["YEARMONTH"].dt.year == year)].copy()

    elif type == "Cash":
        income_type = income[income["TYPE"].isin(["DSTA SUPPLEMENT","DSTA SALARY"])].copy()
        income_year_type = income[(income["TYPE"].isin(["DSTA SUPPLEMENT","DSTA SALARY"])) & (income["YEARMONTH"].dt.year == year)].copy()
    
    else:
        income_type = income.copy()
        income_year_type = income_year.copy()

    # generate figures
    kpi_fig = generate_indicators(income_year)
    trend_fig = generate_trend(income_type)
    type_fig = generate_type_fig(income_year_type)

    return kpi_fig, trend_fig, type_fig