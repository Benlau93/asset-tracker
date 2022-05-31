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
BANK_TYPE = ["Salary","Medium"]
CPF_TYPE = ["OA","SA","MA"]

def generate_indicators(df):
    # get total income for current year
    income_kpi = df["VALUE"].sum()
    cash_kpi = df[df["TYPE"].isin(BANK_TYPE)]["VALUE"].sum()
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
    uni_years = df.sort_values(["DATE"], ascending=False)["DATE"].dt.year.unique()

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


def generate_bar(df):

    # get average
    df_avg = df.groupby("YEARMONTH").sum()[["VALUE"]].reset_index()
    df_avg["AVG"] = df_avg["VALUE"].mean()
    
    # split into cash and cpf
    cash = df[df["TYPE"].isin(BANK_TYPE)].copy()
    cash = cash.groupby(["YEARMONTH"]).sum()[["VALUE"]].reset_index()

    cpf = df[df["TYPE"].isin(CPF_TYPE)].copy()
    cpf = cpf.groupby("YEARMONTH").sum()[["VALUE"]].reset_index()

    bar_fig = go.Figure()

    # add cash
    bar_fig.add_trace(
        go.Bar(x = cash["YEARMONTH"], y= cash["VALUE"], text = cash["VALUE"], texttemplate = "%{y:$,.0f}",name="Cash", textposition="inside",
        marker_color = "#6495ED")
    )
    # add cpf
    bar_fig.add_trace(
        go.Bar(x = cpf["YEARMONTH"], y= cpf["VALUE"], name="CPF", text = cpf["VALUE"], texttemplate = "%{y:$,.0f}", textposition="inside",
        marker_color = "#F2CA85")
    )

    # add monthly average
    bar_fig.add_trace(
        go.Scatter(x = df_avg["YEARMONTH"], y = df_avg["AVG"] , name = "Average", line = dict(color="red", dash="dash"), hovertemplate = "%{y:$,.0f}")
    )

    # update layout
    bar_fig.update_yaxes(tickformat = "$,.0f", showgrid=False)
    bar_fig.update_xaxes(tickformat="%b %Y")

    bar_fig.update_layout(
        title = "Income by Type & Month",
        legend = {"orientation":"h", "title":"Legend", "yanchor":"bottom", "xanchor":"right","y":1, "x":1},
        barmode = "stack",
        template = TEMPLATE,
        height=750
    )

    return bar_fig



def generate_type_fig(df):

    # sum by type
    df = df.groupby("TYPE").sum()[["VALUE"]].reset_index().sort_values(["VALUE"], ascending=True)

    type_fig = go.Figure()

    type_fig.add_trace(
        go.Pie(labels= df["TYPE"], values=df["VALUE"],textinfo = "label+percent", hovertemplate = "%{label}: %{value:$,.02f}", name="Type",
        hole = 0.5)
    )


    type_fig.update_layout(
        title = "Distribution by Income Type",
        showlegend=False,
        height = 450,
        template = TEMPLATE
    )

    return type_fig

def generate_base_fig(df):
    # remove medium
    df = df[df["TYPE"]!="Medium"].copy()
    df["RANK"] = df["VALUE"]

    # get base salary
    base = 0
    for t in df["TYPE"].unique():
        _ = df[df["TYPE"]==t].sort_values("YEARMONTH")
        _["RANK"] = _.groupby("VALUE").rank(method="first")["RANK"]
        base += _[_["RANK"]>1].tail(1)["VALUE"].iloc[0]

    # generate figure
    base_fig = go.Figure()
    base_fig.add_trace(
        go.Indicator(mode = "number", value = base, number = dict(valueformat="$,.0f"), title = "Monthly Base Income")
    )

    base_fig.update_layout(
        template = TEMPLATE,
        height = 300
    )

    return base_fig

layout = html.Div([
    dbc.Container([
        dbc.Row([
            dbc.Col([html.H5("Select Year:")],width=2),
            dbc.Col([
                dbc.Select(
                    id = "year-selection",
                    options = [{"label":y, "value":y} for y in range(YEAR,2019,-1)],
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
            dbc.Col([dcc.Graph(id="bar-kpi")], width=5),
            dbc.Col([
                dbc.Row([
                    dbc.Col([dcc.Graph(id="base-chart")]),
                ]),
                dbc.Row([
                    dbc.Col([dcc.Graph(id="type-chart")]),
                ])], width=4),
        dbc.Row([
            dbc.Card(html.H3("Y.O.Y Comparison", className="text-center text-primary bg-light"), body=True, color="light")
        ], style={"margin-top":20}),
        ])
    ])
])




@app.callback(
    Output(component_id="income-kpi", component_property="figure"),
    Output(component_id="bar-kpi", component_property="figure"),
    Output(component_id="type-chart", component_property="figure"),
    Output(component_id="base-chart", component_property="figure"),
    Input(component_id="year-selection",component_property="value"),
    Input(component_id="type-radios", component_property="value"),
    State(component_id="bank-store", component_property="data"),
    State(component_id="cpf-store", component_property="data")
)
def update_graph(year,type,bank, cpf):

    # process selector
    year = int(year)
    type_map = {"CPF":CPF_TYPE, "Cash":BANK_TYPE , "All":BANK_TYPE + CPF_TYPE}

    # convert to dataframe
    bank = pd.DataFrame(bank)
    cpf = pd.DataFrame(cpf)

    # process bank statement
    bank_income = bank[bank["BANK_TYPE"].isin(BANK_TYPE)].drop(["DATE","ID","HISTORICAL"], axis=1).rename({"BANK_TYPE":"TYPE"},axis=1) # filter to income
    
    # process cpf
    cpf_income = cpf[(cpf["CODE"]=="CON") & (cpf["REF"].isin(["A","B"]))].drop(["DATE","REF","CODE","ID","HISTORICAL"], axis=1).copy() # filter to cpf contribution from dsta income
    cpf_income = cpf_income.groupby("YEARMONTH").sum().reset_index() # combine REF A and B
    cpf_income = cpf_income.melt(id_vars=["YEARMONTH"], value_name = "VALUE", var_name = "TYPE")

    # combine both sources
    income = pd.concat([bank_income, cpf_income], sort=True, ignore_index=True)
    income["YEARMONTH"] = pd.to_datetime(income["YEARMONTH"], format="%b %Y")

    # filters
    income_year = income[income["YEARMONTH"].dt.year==year].copy()
    income_type = income[income["TYPE"].isin(type_map[type])].copy()
    income_year_type = income_year[(income_year["TYPE"].isin(type_map[type]))].copy()

    # generate figures
    kpi_fig = generate_indicators(income_year)
    bar_fig = generate_bar(income_year_type)
    # trend_fig = generate_trend(income_type)
    type_fig = generate_type_fig(income_year_type)
    base_fig = generate_base_fig(income_year_type)

    return kpi_fig, bar_fig, type_fig, base_fig