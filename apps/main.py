from app import app
from dash import html
from dash import dcc
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
from dash.dependencies import Input, Output, State
from dash import callback_context
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

def generate_sub_indicator(df):

    # calculate value and % 
    total_value = df["VALUE"].sum()
    
    # value figure
    value_fig = go.Figure()
    value_fig.add_trace(
        go.Indicator(mode="number",
                    value=total_value,
                    title = "Total Value",
                    number = dict(valueformat="$,.0f"))
    )

    value_fig.update_layout(
        height = 250,
        template = TEMPLATE
    )

    return value_fig

def generate_bar(df):
    df_ = df.groupby("Liquidity").sum()[["VALUE"]].reset_index()
    total = df_["VALUE"].sum()
    df_["PER"] = df_["VALUE"] / total

    # add figure
    bar_fig = go.Figure()
    bar_fig.add_trace(
        go.Bar(x=df_["PER"], y=df_["Liquidity"], textposition="inside", texttemplate="%{x:.1%}", hovertemplate="%{y}: %{x:.1%}",orientation='h', name="Liquidity")
    )

    bar_fig.update_layout(
        title="Distribution by Liquidity",
        template=TEMPLATE,
        height=500,
        xaxis=dict(visible=False),
        showlegend=False
    )

    return bar_fig
    


def generate_pie(df):

    pie_fig = go.Figure()

    pie_fig.add_trace(
        go.Pie(labels = df["Asset"], values = df["VALUE"], textinfo = "label+percent", hovertemplate = "%{label}: %{value:$,.02f}", name="Asset Class")
    )
    pie_fig.update_layout(title = "Distribution by Asset Class",
                        showlegend=False,
                        height=500,
                        template=TEMPLATE)



    return pie_fig


def generate_line(df):

    # sum value
    df = df.sort_values("DATE").groupby("DATE").sum()[["VALUE"]].reset_index()
    df["CHANGE"] = df.shift(1)["VALUE"]
    df["CHANGE"] = df["VALUE"] - df["CHANGE"]
    

    # trend of asset value
    line_fig = make_subplots(rows=2, cols = 1, subplot_titles = ["Asset Trends","% Change Trends"], row_heights=[0.8,0.2], vertical_spacing=0)

    line_fig.add_trace(
        go.Scatter(x=df["DATE"], y = df["VALUE"], mode="lines+markers+text", name = "Asset"), row=1, col=1
    )

    # add bar
    # define bar color
    bar_colors = ["crimson" if change <0 else "#2E8B57" for change in df["CHANGE"].values]

    line_fig.add_trace(
        go.Bar(x=df["DATE"], y=df["CHANGE"], name="Change", marker_color = bar_colors, opacity=0.5),
        row=1, col=1
    )


    # add line to monitor yearly trend
    df_year = df[df["DATE"].dt.month==12].copy()
    years = df_year["DATE"].dt.year.unique()
    green = 222
    for i in range(len(years)):

        # determine variables
        year = years[i]
        value = df_year[df_year["DATE"].dt.year==year]["VALUE"].iloc[0]
        color = f"rgb(100,{green},200)"
        green = max(0,green-50)
        text = f"{year+1}, ${str(round(value))}"

        # plot lines
        line_fig.add_hline(y=value, line_dash="dash", annotation_text=text, line_color=color)
    
    # update axis
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
                            height=1000,
                            showlegend=False,
                            template = TEMPLATE)

    return line_fig



layout = html.Div([
    dbc.Container([
        dbc.Row([
            dbc.Col([dcc.Graph(id="main-kpi")], width = 5),
            dbc.Col([dcc.Graph(id="debt-kpi")], width = 5),
        ], justify="center"),
        dbc.Row([
            dbc.Card(html.H3(id="info",className="text-center text-light bg-dark"), body=True, color="dark")
        ]),
        dbc.Row([
            dbc.Col([dcc.Graph(id="value-kpi")], width = {"size":6, "offset":3}, align="center"),
            dbc.Col([dbc.Button("Reset",id="reset-button",color="primary", style={"margin-top":10})],width={"size":3, "offset":0})
        ]),
        dbc.Row([
                dbc.Col([dcc.Graph(id="liquid-chart")], width=6, align="center"),
                dbc.Col([dcc.Graph(id="pie-chart")], width = 4)
        ], justify="center"),
        dbc.Row([
            dbc.Card(html.H3(children="Trend Analysis",className="text-center text-light bg-dark"), body=True, color="dark")
        ]),
        dbc.Row([
            dbc.Col([dcc.Graph(id="line-chart")], width={"size":12}),
        ])
    ])
])


@app.callback(
    Output(component_id="main-kpi",component_property="figure"),
    Output(component_id="debt-kpi",component_property="figure"),
    Output(component_id="liquid-chart",component_property="figure"),
    Output(component_id="pie-chart",component_property="figure"),
    Output(component_id="value-kpi",component_property="figure"),
    Output(component_id="line-chart",component_property="figure"),
    Output(component_id="info",component_property="children"),
    Input(component_id="liquid-chart", component_property="clickData"),
    Input(component_id="pie-chart", component_property="clickData"),
    Input(component_id="reset-button", component_property="n_clicks"),
    State(component_id="df-store", component_property="data"),
    State(component_id="debt-store", component_property="data")
)
def filter_graph(click_bar, click_pie, n_clicks, df, debt):
    n_clicks = 0 if n_clicks ==None else n_clicks
    title = "Total Asset"
    # get triggered input
    changed_id = [p['prop_id'] for p in callback_context.triggered][0]

    # convert to dataframe
    df = pd.DataFrame(df)
    df["DATE"] = pd.to_datetime(df["DATE"])
    debt = pd.DataFrame(debt)

    # get latest yearmonth df
    latest_yearmonth = df[df["DATE"] == df["DATE"].max()]["YEARMONTH"].unique()[0]
    df_latest = df[df["YEARMONTH"]==latest_yearmonth].copy()
    debt_latest = debt[debt["YEARMONTH"]==latest_yearmonth].copy()
    
    # get initial state
    if click_bar != None and "reset-button" not in changed_id:
        liquid = click_bar["points"][0]["y"]
        df_pie = df_latest[df_latest["Liquidity"]==liquid].copy()
    else:
        df_pie = df_latest.copy()
    df_line = df.copy()
    df_value = df_latest.copy()

    # trigger filter based on what was clicked
    if "liquid-chart" in changed_id:
        
        df_pie = df_latest[df_latest["Liquidity"]==liquid].copy()
        df_value = df_pie.copy()
        df_line = df[df["Liquidity"]==liquid].copy()
        title = liquid
    elif "pie-chart" in changed_id:
        asset = click_pie["points"][0]["label"]
        df_line = df[df["Asset"]==asset].copy()
        df_value = df_latest[df_latest["Asset"]==asset].copy()
        title = asset
    
    # generate charts
    main_fig = generate_indicator(df_latest)
    debt_fig = generate_debt_indicator(debt_latest)
    bar_fig = generate_bar(df_latest)
    pie_fig = generate_pie(df_pie)
    value_fig = generate_sub_indicator(df_value)
    line_fig = generate_line(df_line)

    return main_fig, debt_fig, bar_fig, pie_fig, value_fig, line_fig, f"{title} Analysis"
