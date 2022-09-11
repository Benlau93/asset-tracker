from dash import html
from dash import dcc
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output
from app import app
from apps import main, income, tax, taxprojection
import requests
import pandas as pd


# building the navigation bar
navbar = dbc.NavbarSimple(
    children=[
        dbc.NavItem(dbc.NavLink("Home", href="/")),
        dbc.NavItem(dbc.NavLink("Income", href="/income")),
        dbc.NavItem(dbc.NavLink("Tax", href="/tax"))

    ],
    brand="Asset Tracking",
    brand_href="/",
    color="primary",
    dark=True
)

# laod data
def load_data():

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
    bank_["Asset"] = "Savings"

    cpf_ = cpf[cpf["CODE"]=="BAL"][["DATE","YEARMONTH","OA","SA","MA"]].copy()
    cpf_ = cpf_.set_index(["DATE","YEARMONTH"]).stack().reset_index()
    cpf_.columns = ["DATE","YEARMONTH","Asset","VALUE"]
    cpf_["Asset"] = cpf_["Asset"].map(lambda x: "CPF - " + x)

    investment_ = investment.groupby(["DATE","YEARMONTH"]).sum()[["VALUE"]].reset_index()
    investment_["Asset"] = "Investment"

    df = pd.concat([bank_, cpf_, investment_], sort=True, ignore_index=True)

    # drop yearmonth that is not complete
    yearmonth = df[df["Asset"]=="Savings"]["YEARMONTH"].unique()
    df = df[df["YEARMONTH"].isin(yearmonth)].copy()
    # add liquidity
    df["Liquidity"] = df["Asset"].map(lambda x: "non-Liquid" if x.startswith("CPF") else "Liquid")

    # load debt
    debt = requests.get("http://127.0.0.1:8001/api/debt")
    debt = pd.DataFrame.from_dict(debt.json())
    debt["DATE"] = pd.to_datetime(debt["DATE"], format="%Y-%m-%d")

    # load tax and relief
    tax_df = requests.get("http://127.0.0.1:8001/api/tax")
    tax_df = pd.DataFrame.from_dict(tax_df.json())

    relief = requests.get("http://127.0.0.1:8001/api/relief")
    relief = pd.DataFrame.from_dict(relief.json())

    return df.to_dict(orient="records"), debt.to_dict(orient = "records"),bank.to_dict(orient="records"), cpf.to_dict(orient="records"), investment.to_dict(orient="records"), tax_df.to_dict(orient="records"), relief.to_dict(orient="records")



def serve_layout():
    return html.Div([
        dcc.Location(id='url', refresh=False),
        navbar,
        html.Div(id='page-content'),

        # data store
        dcc.Store(id="df-store"),
        dcc.Store(id="debt-store"),
        dcc.Store(id="bank-store"),
        dcc.Store(id="cpf-store"),
        dcc.Store(id="investment-store"),
        dcc.Store(id="tax-store"),
        dcc.Store(id="relief-store")
    ])
app.layout = serve_layout


@app.callback(
    Output(component_id='page-content', component_property='children'),
    Output(component_id='df-store', component_property='data'),
    Output(component_id='debt-store', component_property='data'),
    Output(component_id='bank-store', component_property='data'),
    Output(component_id='cpf-store', component_property='data'),
    Output(component_id='investment-store', component_property='data'),
    Output(component_id='tax-store', component_property='data'),
    Output(component_id='relief-store', component_property='data'),
    Input(component_id='url', component_property='pathname')
)
def display_page(pathname):
    if pathname == "/income":
        layout = income.layout
    elif pathname =="/tax":
        layout = tax.layout
    elif pathname == "/tax-projection":
        layout =  taxprojection.layout
    else:
        layout = main.layout

    # load data
    print("RETRIEVE DATA FROM BACKEND API")
    df, debt, bank, cpf, investment, tax_df, relief = load_data()

    return layout, df, debt, bank, cpf, investment, tax_df, relief

# start server
if __name__ == '__main__':
    app.run_server(port=8051,debug=True)