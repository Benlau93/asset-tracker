from app import app
from dash import html
from dash import dcc
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from dash.dependencies import Input, Output, State
from app import app


# define template used
TEMPLATE = "plotly_white"


# main kpi
def generate_indicator(df):
    # get current total asset value
    main_kpi = df["VALUE"].sum()

    main_fig = go.Figure()
    main_fig.add_trace(
        go.Indicator(mode="number",
                    value = main_kpi,
                    title = "Total Asset Value",
                    number = dict(valueformat="$,.0f"))
    )

    main_fig.update_layout(
        height = 250,
        template = TEMPLATE
    )

    return main_fig

def generate_sub_indicator(df, asset):

    # add liquidity
    df["Liquidity"] = df["Asset"].map(lambda x: "non-Liquid" if x.startswith("CPF") else "Liquid")

    # calculate value and % 
    total_value = df["VALUE"].sum()

    filtered_value = df[df["Liquidity"]==asset]["VALUE"].sum()
    per = filtered_value / total_value
    
    # value figure
    value_fig = go.Figure()
    value_fig.add_trace(
        go.Indicator(mode="number",
                    value=filtered_value,
                    title = f"Total {asset} Value",
                    number = dict(valueformat="$,.0f"))
    )

    value_fig.update_layout(
        height = 250,
        template = TEMPLATE
    )

    # % indicator
    per_fig = go.Figure()
    per_fig.add_trace(
        go.Indicator(mode="number",
                    value = per,
                    title = "% Total Value",
                    number = dict(valueformat=".01%")
        )
    )

    per_fig.update_layout(
        height = 250,
        template = TEMPLATE
    )

    return value_fig, per_fig

def generate_pie(df):

    pie_fig = go.Figure()
    pie_fig.add_trace(
        go.Pie(labels = df["Asset"], values = df["VALUE"], hole =0.5)
    )
    

    pie_fig.update_layout(title = "Distribution by Asset",
                        showlegend=False,
                        template=TEMPLATE)

    return pie_fig


def generate_area(df):

    # label liquid or non-liquid
    df["Liquidity"] = df["Asset"].map(lambda x: "Liquid" if x!="CPF" else "non-Liquid")
    df = df.groupby(["DATE","Liquidity"]).sum()[["VALUE"]].reset_index()

    area_fig = go.Figure()

    # non-lid
    non_liq = df[df["Liquidity"]=="non-Liquid"].copy()

    area_fig.add_trace(
        go.Scatter(x=non_liq["DATE"], y = non_liq["VALUE"], 
         line=dict(width=0.5, color='red') , mode="lines+markers", stackgroup="one", name = "non-Liquid")
    )

    # liq
    liq = df[df["Liquidity"]=="Liquid"].copy()
    area_fig.add_trace(
        go.Scatter(x=liq["DATE"], y = liq["VALUE"], 
        line=dict(width=0.5, color='green'), mode="lines+markers", stackgroup="one", name = "Liquid")
    )

    area_fig.update_layout(title="Total Asset Trends",
                            showlegend=False,
                            template = TEMPLATE)

    return area_fig



layout = html.Div([
    dbc.Container([
        dbc.Row([
            dbc.Col([dcc.Graph(id="main-kpi")], width = 3),
            dbc.Col([dcc.Graph(id="debt-kpi")], width = 3),
            dbc.Col([
                    html.H6("Select Asset Class:"),
                    dbc.RadioItems(
                        id="radios",
                        className="btn-group",
                        inputClassName="btn-check",
                        labelClassName="btn btn-outline-info",
                        labelCheckedClassName="active",
                        options=[
                            {"label": "Liquid", "value": "Liquid"},
                            {"label": "non-Liquid", "value": "non-Liquid"}
                        ],
                        value="Liquid")
            ], width = 3, align="center"),
        ], justify="center"),
        dbc.Row([
            dbc.Col([dcc.Graph(id="value-kpi")], width = 5),
            dbc.Col([dcc.Graph(id="per-kpi")], width=5)
        ], justify = "center"),
        dbc.Row([
            dbc.Col([dcc.Graph(id="area-chart")], width={"size":8}),
            dbc.Col([dcc.Graph(id="pie-chart")], width = {"size":4})
        ])
    ])
])


@app.callback(
    Output(component_id="main-kpi",component_property="figure"),
    Output(component_id="debt-kpi",component_property="figure"),
    Output(component_id="value-kpi",component_property="figure"),
    Output(component_id="per-kpi",component_property="figure"),
    Output(component_id="pie-chart",component_property="figure"),
    Output(component_id="area-chart",component_property="figure"),
    Input(component_id="radios", component_property="value"),
    State(component_id="df-store", component_property="data")
)
def update_graph(asset,df):

    # get latest yearmonth
    df = pd.DataFrame(df)
    latest_yearmonth = df[df["DATE"] == df["DATE"].max()]["YEARMONTH"].unique()[0]
    df_ = df[df["YEARMONTH"]==latest_yearmonth].copy()

    # generate charts
    main_fig = generate_indicator(df_)
    value_fig, per_fig = generate_sub_indicator(df_, asset)
    pie_fig = generate_pie(df_)
    area_fig = generate_area(df)

    return main_fig, main_fig, value_fig, per_fig, pie_fig, area_fig