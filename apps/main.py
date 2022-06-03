from app import app
from dash import html
from dash import dcc
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
from plotly.subplots import make_subplots
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

# debt kpi
def generate_debt_indicator(df):
    # get current debt value
    debt_kpi = df["REMAINING_VALUE"].iloc[0]

    debt_fig = go.Figure()
    debt_fig.add_trace(
        go.Indicator(mode="number",
                    value = debt_kpi,
                    title = "Total Debt Value",
                    number = dict(valueformat="$,.0f"))
    )

    debt_fig.update_layout(
        height = 250,
        template = TEMPLATE
    )

    return debt_fig

def generate_sub_indicator(df, asset):

    # calculate value and % 
    total_value = df["VALUE"].sum()

    if asset != "Total":
        filtered_value = df[df["Liquidity"]==asset]["VALUE"].sum()
    else:
        filtered_value = df["VALUE"].sum()

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
        go.Pie(labels = df["Asset"], values = df["VALUE"], textinfo = "label+percent", hovertemplate = "%{label}: %{value:$,.02f}", name="Asset Class")
    )
    pie_fig.update_layout(title = "Distribution by Asset Class",
                        showlegend=False,
                        template=TEMPLATE)



    return pie_fig


def generate_line(df):

    # sum value
    df = df.sort_values("DATE").groupby("DATE").sum()[["VALUE"]].reset_index()

    # trend of asset value
    line_fig = make_subplots(rows=2, cols = 1, subplot_titles = ["Asset Trends","% Change Trends"], row_heights=[0.7,0.3])

    line_fig.add_trace(
        go.Scatter(x=df["DATE"], y = df["VALUE"], mode="lines+markers+text", name = "Asset"), row=1, col=1
    )
    line_fig.update_xaxes(row=1,col=1,showgrid=False, visible=False)
    line_fig.update_yaxes(row=1,col=1, tickformat = "$,.0f", showgrid=False)

    # percentage change
    df["CHANGE"] = df["VALUE"].shift(1)
    df["CHANGE"] = (df["VALUE"] - df["CHANGE"]) / df["CHANGE"]

    line_fig.add_trace(
        go.Scatter(x=df["DATE"], y = df["CHANGE"], mode="lines+markers", name = "% Change", line=dict(dash="dash", color="#3A3A38")),row=2, col=1
    )

    line_fig.update_xaxes(row=2,col=1,showgrid=False)
    line_fig.update_yaxes(row=2,col=1, tickformat = ".0%", zeroline=True, zerolinecolor="red", zerolinewidth=0.5)

    line_fig.update_layout(
                            showlegend=False,
                            template = TEMPLATE)

    return line_fig



layout = html.Div([
    dbc.Container([
        dbc.Row([
            dbc.Col([dcc.Graph(id="main-kpi")], width = 4),
            dbc.Col([dcc.Graph(id="debt-kpi")], width = 4),
            dbc.Col([
                    html.H6("Select Asset Class:"),
                    dbc.RadioItems(
                        id="radios",
                        className="btn-group",
                        inputClassName="btn-check",
                        labelClassName="btn btn-outline-info",
                        labelCheckedClassName="active",
                        options=[
                            {"label":"Total", "value":"Total"},
                            {"label": "Liquid", "value": "Liquid"},
                            {"label": "non-Liquid", "value": "non-Liquid"}
                        ],
                        value="Total")
            ], width = 3, align="center"),
        ], justify="center"),
        dbc.Row([
            dbc.Card(html.H3(id="info", className="text-center text-light bg-dark"), body=True, color="dark")
        ]),
        dbc.Row([
            dbc.Col([dcc.Graph(id="value-kpi")], width = 5),
            dbc.Col([dcc.Graph(id="per-kpi")], width=5)
        ], justify = "center"),
        dbc.Row([
            dbc.Col([dcc.Graph(id="line-chart")], width={"size":8}),
            dbc.Col([dcc.Graph(id="pie-chart")], width = {"size":4})
        ])
    ])
])


@app.callback(
    Output(component_id="main-kpi",component_property="figure"),
    Output(component_id="debt-kpi",component_property="figure"),
    Output(component_id="info",component_property="children"),
    Output(component_id="value-kpi",component_property="figure"),
    Output(component_id="per-kpi",component_property="figure"),
    Output(component_id="pie-chart",component_property="figure"),
    Output(component_id="line-chart",component_property="figure"),
    Input(component_id="radios", component_property="value"),
    State(component_id="df-store", component_property="data"),
    State(component_id="debt-store", component_property="data")
)
def update_graph(asset,df, debt):

    # convert to dataframe
    df = pd.DataFrame(df)
    debt = pd.DataFrame(debt)
    # add liquidity
    df["Liquidity"] = df["Asset"].map(lambda x: "non-Liquid" if x.startswith("CPF") else "Liquid")
    
    # get latest yearmonth df
    latest_yearmonth = df[df["DATE"] == df["DATE"].max()]["YEARMONTH"].unique()[0]
    df_latest = df[df["YEARMONTH"]==latest_yearmonth].copy()
    debt_latest = debt[debt["YEARMONTH"]==latest_yearmonth].copy()

    # filter
    if asset != "Total":
        df_latest_asset = df_latest[df_latest["Liquidity"]==asset].copy()
        df_asset = df[df["Liquidity"]==asset].copy()
    else:
        df_latest_asset = df_latest.copy()
        df_asset = df.copy()

    # generate charts
    main_fig = generate_indicator(df_latest)
    debt_fig = generate_debt_indicator(debt_latest)
    value_fig, per_fig = generate_sub_indicator(df_latest, asset)
    pie_fig = generate_pie(df_latest_asset)
    line_fig = generate_line(df_asset)

    return main_fig, debt_fig, f"{asset} Asset Breakdown" ,value_fig, per_fig, pie_fig, line_fig