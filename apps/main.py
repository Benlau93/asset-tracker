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
                    title = "Current Total Asset Value",
                    number = dict(valueformat="$,.0f"))
    )

    main_fig.update_layout(
        height = 250,
        template = TEMPLATE
    )

    # get current liquid value
    liquid_kpi = df[df["Asset"]!="CPF"]["VALUE"].sum()
    
    liquid_fig = go.Figure()
    liquid_fig.add_trace(
        go.Indicator(mode="number",
                    value = liquid_kpi,
                    title = "Liquid Asset Value",
                    number = dict(valueformat="$,.0f"))
    )

    liquid_fig.update_layout(
        height = 250,
        template = TEMPLATE
    )

    # get % liquid
    liquid_per = liquid_kpi / main_kpi
    
    liquid_per_fig = go.Figure()
    liquid_per_fig.add_trace(
        go.Indicator(mode="number",
                    value = liquid_per,
                    title = "% Liquidity",
                    number = dict(valueformat=".01%"))
    )

    liquid_per_fig.update_layout(
        height = 250,
        template = TEMPLATE
    )


    return main_fig, liquid_fig, liquid_per_fig

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
            dbc.Col([
                dcc.Graph(id="main-kpi")
            ], width = 10)
        ], justify="center"),
        dbc.Row([
            dbc.Col([dcc.Graph(id="area-chart")], width={"size":8}),
            dbc.Col([dcc.Graph(id="pie-chart")], width = {"size":4})
        ]),
        dbc.Row([
            dbc.Col([dcc.Graph(id="liquid-kpi")], width = {"size":3}),
            dbc.Col([dcc.Graph(id="liquid-per-kpi")], width = {"size":3}),
            dbc.Col([dbc.Card(html.Div(), style={"background-color":"green"})])
        ], align="justify" )
    ])
])


@app.callback(
    Output(component_id="main-kpi",component_property="figure"),
    Output(component_id="liquid-kpi",component_property="figure"),
    Output(component_id="liquid-per-kpi",component_property="figure"),
    Output(component_id="pie-chart",component_property="figure"),
    Output(component_id="area-chart",component_property="figure"),
    Input(component_id="url", component_property="pathname"),
    State(component_id="df-store", component_property="data")
)
def update_graph(_,df):

    # get latest yearmonth
    df = pd.DataFrame(df)
    latest_yearmonth = df[df["DATE"] == df["DATE"].max()]["YEARMONTH"].unique()[0]
    df_ = df[df["YEARMONTH"]==latest_yearmonth].copy()

    # generate charts
    main_fig, liquid_fig, liquid_per_fig = generate_indicator(df_)
    pie_fig = generate_pie(df_)
    area_fig = generate_area(df)

    return main_fig, liquid_fig, liquid_per_fig, pie_fig, area_fig