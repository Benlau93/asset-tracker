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
BANK_TYPE = ["Salary"]
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

def generate_yoy_trend(df, year, visible):

    # get prev year
    prev_year = year - 1

    # find unique years/month
    uni_years = df.sort_values(["YEARMONTH"])["YEARMONTH"].dt.year.unique()

    # create df for all month
    month_df = pd.DataFrame({"MONTH":list(range(1,13)),"YEARMONTH_REF":df.sort_values(["YEARMONTH"])["YEARMONTH"].dt.strftime("%b").unique(),"VALUE_REF":[0] * 12})
    
    # sum value for each yearmonth
    df = df.groupby(["YEARMONTH"]).sum()[["VALUE"]].reset_index()
    df["MONTH"] = df["YEARMONTH"].dt.month # define month

    # get max value for tick
    max_tick = df["VALUE"].max() * 1.1

    yoy_trend_fig = go.Figure()

    # add current year line chart
    _ = df[df["YEARMONTH"].dt.year == year].copy()
    # check missing month
    _ = pd.merge(_, month_df, on="MONTH", how="outer").sort_values("MONTH")
    _["VALUE"] = _["VALUE"].fillna(_["VALUE_REF"])

    yoy_trend_fig.add_trace(
        go.Scatter(x=_["YEARMONTH_REF"], y=_["VALUE"], mode = "lines+markers", name=str(year),
        line = dict(color = "firebrick", width=2))
    )

    # add prev year line chart
    _ = df[df["YEARMONTH"].dt.year == prev_year].sort_values("YEARMONTH").copy()
    # check missing month
    _ = pd.merge(_, month_df, on="MONTH", how="outer").sort_values("MONTH")
    _["VALUE"] = _["VALUE"].fillna(_["VALUE_REF"])

    yoy_trend_fig.add_trace(
        go.Scatter(x=_["YEARMONTH_REF"], y=_["VALUE"], mode = "lines+markers", name=str(prev_year),
        line = dict(color = "royalblue", width=1, dash="dash"))
    )

    # if visible, show historical data
    if visible == "Yes":
        for y in uni_years:
            if y < prev_year:
                _ = df[df["YEARMONTH"].dt.year == y].sort_values("YEARMONTH").copy()
                # check missing month
                _ = pd.merge(_, month_df, on="MONTH", how="outer").sort_values("MONTH")
                _["VALUE"] = _["VALUE"].fillna(_["VALUE_REF"])

                yoy_trend_fig.add_trace(
                    go.Scatter(x=_["YEARMONTH_REF"], y=_["VALUE"], mode = "lines+markers", name=str(y),
                    line = dict(color="#D3D3D3", dash="dot"))
                )


    yoy_trend_fig.update_xaxes(showgrid=False)
    yoy_trend_fig.update_yaxes(tickformat = "$,.0f", range=[0,max_tick])

    yoy_trend_fig.update_layout(
        legend = {"orientation":"h", "title":"Year", "yanchor":"bottom", "xanchor":"right","y":1, "x":1},
        template = TEMPLATE,
        height=750
    )
    
    return yoy_trend_fig


def generate_bar(df):
    # current month
    num_month = df["YEARMONTH"].dt.month.max()

    # get average
    df_avg = df.groupby("YEARMONTH").sum()[["VALUE"]].reset_index()
    df_avg["AVG"] = df_avg["VALUE"].sum() / num_month
    
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
        legend = {"orientation":"h", "title":"Legend", "yanchor":"bottom", "xanchor":"right","y":1, "x":1},
        annotations = [dict(xref="paper", yref="paper",x=0.9,y=0.95, xanchor="left",yanchor="top",text="Mean: ${:,}".format(round(df_avg['AVG'].iloc[0])),
                        font = dict(size=15, color="red"), showarrow=False)],
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
        height = 500,
        template = TEMPLATE
    )

    return type_fig

def generate_base_fig(df):
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
        height = 250
    )

    return base_fig


def generate_yoy_indicator(df, year):

    # define year, month
    PREV_YEAR = year - 1
    MONTH = df[df["YEARMONTH"].dt.year==year]["YEARMONTH"].dt.month.max()

    # get prev and current value
    prev_income = df[(df["YEARMONTH"].dt.year == PREV_YEAR) & (df["YEARMONTH"].dt.month <=MONTH)]["VALUE"].sum()
    curr_income = df[(df["YEARMONTH"].dt.year == year) & (df["YEARMONTH"].dt.month <=MONTH)]["VALUE"].sum()

    # get change
    # check if prev year present
    if prev_income == 0:
        yoy_change, yoy_per = 0,0
    else:
        yoy_change = curr_income - prev_income
        yoy_per = (curr_income - prev_income) / prev_income

    # generate figure
    yoy_fig = go.Figure()

    yoy_fig.add_trace(
        go.Indicator(
            mode="number",
                value = yoy_change,
                title = "YoY Change",
                number = dict(valueformat="$,.0f"),
                domain = {"row":0, "column":0}
        )
    )

    yoy_fig.add_trace(
        go.Indicator(
            mode="number",
                value = yoy_per,
                title = "YoY Change (%)",
                number = dict(valueformat=".01%"),
                domain = {"row":0, "column":1}
        )
    )
    yoy_fig.update_layout(
        grid = {"rows":1, "columns":2, "pattern":"independent"},
        height = 250,
        template = TEMPLATE
    )

    return yoy_fig

def generate_yoy_change(df, curr_year):

    # get year
    df["YEAR"] = df["YEARMONTH"].dt.year
    df = df[df["YEAR"]<=curr_year].copy()

    # get change for historical
    df_hist = df[df["YEAR"]<curr_year].copy()
    df_hist = df_hist.groupby(["YEAR"]).sum()[["VALUE"]].reset_index()
    df_hist["YEAR-1"] = df_hist["VALUE"].shift(1)
    

    # get change for current
    df_curr = df[df["YEAR"]>=curr_year-1].copy()
    # remove month not in current month
    max_curr_month = df[df["YEAR"]==curr_year]["YEARMONTH"].dt.month.max()
    df_curr = df_curr[df_curr["YEARMONTH"].dt.month<=max_curr_month].copy()
    df_curr = df_curr.groupby(["YEAR"]).sum()[["VALUE"]].reset_index()
    df_curr["YEAR-1"] = df_curr["VALUE"].shift(1)
    df_curr = df_curr[df_curr["YEAR"]==curr_year].copy()

    # merge
    yoy_change = pd.concat([df_hist, df_curr], sort=True, ignore_index=True)
    yoy_change["%CHANGE"] = (yoy_change["VALUE"] - yoy_change["YEAR-1"]) / yoy_change["YEAR-1"]

    # generate chart
    yoy_change_fig = make_subplots(specs=[[{"secondary_y": True}]])

    # add % change
    yoy_change_fig.add_trace(
        go.Bar(x = yoy_change["YEAR"], y = yoy_change["%CHANGE"], textposition="inside", texttemplate="%{y:.01%}", hovertemplate = "%{x}, %{y:.01%}",name="YoY % Change")
    )

    # add total annual income
    yoy_change_fig.add_trace(
        go.Scatter(x = yoy_change["YEAR"], y = yoy_change["VALUE"], mode = "lines+markers+text", texttemplate="%{y:$,.0f}",textposition="bottom left", hovertemplate="%{y:$,.0f}", name="Annual Income")
    , secondary_y = True)

    yoy_change_fig.update_yaxes(showticklabels=False, showgrid=False)
    yoy_change_fig.update_yaxes(showticklabels=False, showgrid=False, secondary_y=True, range=[0,yoy_change["VALUE"].max()])
    yoy_change_fig.update_xaxes(showgrid=False, dtick=1)

    yoy_change_fig.update_layout(
        template=TEMPLATE,
        height=500,
        showlegend=False
    )

    # get avg change
    avg_change = yoy_change["%CHANGE"].mean()

    # indicator
    avg_change_fig = go.Figure()
    avg_change_fig.add_trace(
        go.Indicator(
            mode="number",
            value=avg_change,
            title="Annualised % Change",
            number = dict(valueformat=".01%"),

        )
    )
    
    avg_change_fig.update_layout(
        template=TEMPLATE,
        height=250
    )

    return yoy_change_fig, avg_change_fig

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
        html.Br(),
        dbc.Row([
            dbc.Col([html.H5("Employer Contribution:")],width=3),
            dbc.Col(
                    dbc.RadioItems(
                        id="employer-radios",
                        className="btn-group",
                        inputClassName="btn-check",
                        labelClassName="btn btn-outline-primary",
                        labelCheckedClassName="active",
                        options=[
                            {"label": "True", "value": "True"},
                            {"label": "False", "value": "False"}
                        ],
                        value="True")
                , width=2)
        ], align="center", justify="center"),
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
            dbc.Card(html.H3("Y.o.Y Comparison", className="text-center text-primary bg-light"), body=True, color="light")
        ], style={"margin-top":20}),
        dbc.Row([
            dbc.Col([dcc.Graph(id="yoy-kpi")], width=8)
        ], justify="center"),
        dbc.Row([
                dbc.Col([html.H4("Show Historical:")],width={"size":2,"offset":2}, align="center"),
                dbc.Col([
                dbc.RadioItems(
                    id="visible-radios",
                    className="btn-group",
                    inputClassName="btn-check",
                    labelClassName="btn btn-outline-info",
                    labelCheckedClassName="active",
                    options=[
                        {"label": "No", "value": "No"},
                        {"label": "Yes", "value": "Yes"},
                    ],
                    value="No")], width=2),
                    ], justify="center"),
        dbc.Row([
            dbc.Col([dcc.Graph(id="yoy-trend-chart")], width=7),
            dbc.Col([
                dbc.Row([dbc.Col([dcc.Graph(id="yoy-change-kpi")])]),
                dbc.Row([dbc.Col([dcc.Graph(id="yoy-change-chart")])])
            ], width=5)
        ]),
        ])
    ])
])




@app.callback(
    Output(component_id="income-kpi", component_property="figure"),
    Output(component_id="bar-kpi", component_property="figure"),
    Output(component_id="type-chart", component_property="figure"),
    Output(component_id="base-chart", component_property="figure"),
    Output(component_id="yoy-kpi", component_property="figure"),
    Output(component_id="yoy-trend-chart", component_property="figure"),
    Output(component_id="yoy-change-kpi", component_property="figure"),
    Output(component_id="yoy-change-chart", component_property="figure"),
    Input(component_id="year-selection",component_property="value"),
    Input(component_id="type-radios", component_property="value"),
    Input(component_id="visible-radios", component_property="value"),
    Input(component_id="employer-radios", component_property="value"),
    State(component_id="bank-store", component_property="data"),
    State(component_id="cpf-store", component_property="data")
)
def update_graph(year,type, visible, employer,bank, cpf):

    # process selector
    year = int(year)
    type_map = {"CPF":CPF_TYPE, "Cash":BANK_TYPE , "All":BANK_TYPE + CPF_TYPE}
    employer_ref = ["A","B"] if employer == "True" else ["A"]

    # convert to dataframe
    bank = pd.DataFrame(bank)
    cpf = pd.DataFrame(cpf)

    # process bank statement
    bank_income = bank[bank["BANK_TYPE"].isin(BANK_TYPE)].drop(["DATE","ID","HISTORICAL"], axis=1).rename({"BANK_TYPE":"TYPE"},axis=1) # filter to income
    
    # process cpf
    cpf_income = cpf[(cpf["CODE"]=="CON") & (cpf["REF"].isin(employer_ref))].drop(["DATE","REF","CODE","ID","HISTORICAL"], axis=1).copy() # filter to cpf contribution from dsta income
    cpf_income = cpf_income.groupby("YEARMONTH").sum().reset_index()
    cpf_income = cpf_income.melt(id_vars=["YEARMONTH"], value_name = "VALUE", var_name = "TYPE")

    # combine both sources
    income = pd.concat([bank_income, cpf_income], sort=True, ignore_index=True)
    income["YEARMONTH"] = pd.to_datetime(income["YEARMONTH"], format="%b %Y")

    # handle employer contribution
    if employer == "False":
        def remove_employer(row):
            if row["TYPE"]=="Salary":
                new_value = row["VALUE"]
            else:
                new_value = round(row["VALUE"] * 20/37,2)
            
            return new_value

        income["VALUE"] = income.apply(remove_employer, axis=1)

    # filters
    income_year = income[income["YEARMONTH"].dt.year==year].copy()
    income_type = income[income["TYPE"].isin(type_map[type])].copy()
    income_year_type = income_year[(income_year["TYPE"].isin(type_map[type]))].copy()

    # generate figures for income analysis
    kpi_fig = generate_indicators(income_year)
    bar_fig = generate_bar(income_year_type)
    type_fig = generate_type_fig(income_year_type)
    base_fig = generate_base_fig(income_year_type)

    # generate figures for yoy comparison
    yoy_fig = generate_yoy_indicator(income_type, year)
    yoy_trend_fig = generate_yoy_trend(income_type, year, visible)
    yoy_change_fig, avg_change_fig = generate_yoy_change(income_type, year)

    return kpi_fig, bar_fig, type_fig, base_fig, yoy_fig, yoy_trend_fig, avg_change_fig, yoy_change_fig