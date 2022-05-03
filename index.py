from dash import html
from dash import dcc
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output, State
from app import app
from apps import main
from datetime import date
import requests
import pandas as pd


# building the navigation bar
navbar = dbc.NavbarSimple(
    children=[
        dbc.NavItem(dbc.NavLink("Home", href="/")),
        dbc.NavItem(dbc.NavLink("Breakdown", href="/breakdown"))

    ],
    brand="Asset Tracking",
    brand_href="/",
    color="primary",
    dark=True
)

# laod data
def load_data():
    # extract pdf and investment if any
    pdf_extraction = requests.get("http://127.0.0.1:8001/api/extract")
    investment_extraction = requests.get("http://127.0.0.1:8001/api/extract-investment")

    # load DB
    # bank
    bank = requests.get("http://127.0.0.1:8001/api/bank")
    bank = pd.DataFrame.from_dict(bank.json())
    bank["DATE"] = pd.to_datetime(bank["DATE"], format="%Y-%m-%d")

    # cpf
    cpf = requests.get("http://127.0.0.1:8001/api/cpf")
    cpf = pd.DataFrame.from_dict(cpf.json())
    cpf["DATE"] = pd.to_datetime(cpf["DATE"], format="%Y-%m-%d")

    # investment
    investment= requests.get("http://127.0.0.1:8001/api/investment")
    investment = pd.DataFrame.from_dict(investment.json())
    investment["DATE"] = pd.to_datetime(investment["DATE"], format="%Y-%m-%d")

    # combine to get df
    bank_ = bank[bank["BANK_TYPE"]=="END"][["DATE","YEARMONTH","VALUE"]].copy()
    bank_["TYPE"] = "Savings"

    cpf_ = cpf[cpf["CODE"]=="BAL"][["DATE","YEARMONTH","OA","SA","MA"]].copy()
    cpf_["VALUE"] = cpf_["OA"] + cpf_["MA"] + cpf["SA"]
    cpf_ = cpf_.drop(["OA","MA","SA"], axis=1)
    cpf_["TYPE"] = "CPF"

    investment_ = investment.groupby(["DATE","YEARMONTH"]).sum()[["VALUE"]].reset_index()
    investment_["TYPE"] = "Investment"

    df = pd.concat([bank_, cpf_, investment_], sort=True, ignore_index=True)

    # drop yearmonth that is not complete
    yearmonth = df[df["TYPE"]=="Savings"]["YEARMONTH"].unique()
    df = df[df["YEARMONTH"].isin(yearmonth)].copy()

    return df.to_dict(orient="records"), bank.to_dict(orient="records"), cpf.to_dict(orient="records"), investment.to_dict(orient="records")



def serve_layout():
    return html.Div([
        dcc.Location(id='url', refresh=False),
        navbar,
        html.Div(id='page-content'),

        # data store
        dcc.Store(id="df-store"),
        dcc.Store(id="bank-store"),
        dcc.Store(id="cpf-store"),
        dcc.Store(id="investment-store")
    ])
app.layout = serve_layout


@app.callback(
    Output(component_id='page-content', component_property='children'),
    Output(component_id='df-store', component_property='data'),
    Output(component_id='bank-store', component_property='data'),
    Output(component_id='cpf-store', component_property='data'),
    Output(component_id='investment-store', component_property='data'),
    Input(component_id='url', component_property='pathname')
)
def display_page(pathame):
    layout = main.layout

    # load data
    print("RETRIEVE DATA FROM BACKEND API")
    df, bank, cpf, investment = load_data()

    return layout, df, bank, cpf, investment

# start server
if __name__ == '__main__':
    app.run_server(port=8051,debug=True)