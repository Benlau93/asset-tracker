from dash import html
from dash import dcc
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output
from app import app
from apps import main, income, tax, taxprojection
import requests
import pandas as pd

# define global variables
BANK_TYPE = ["Salary"]
CPF_TYPE = ["OA","SA","MA"]

# building the navigation bar
navbar = dbc.NavbarSimple(
    children=[
        dbc.NavItem(dbc.NavLink("Home", href="/")),
        dbc.NavItem(dbc.NavLink("Income", href="/income")),
        dbc.DropdownMenu(
            children=[
                dbc.DropdownMenuItem("Historical", href="/tax"),
                dbc.DropdownMenuItem("Projection", href="/tax-projection"),

            ],
            nav = True,
            in_navbar=True,
            label="Tax")
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
    investment = pd.DataFrame.from_dict(investment.json()).drop(["INVESTMENT_TYPE","HISTORICAL","DATE"], axis=1)
    # investment["DATE"] = pd.to_datetime(investment["DATE"], format="%Y-%m-%d")

    # combine to get df
    bank_ = bank[bank["BANK_TYPE"]=="END"][["DATE","YEARMONTH","VALUE"]].copy()
    bank_["Asset"] = "Savings"

    cpf_ = cpf[cpf["CODE"]=="BAL"][["DATE","YEARMONTH","OA","SA","MA"]].copy()
    cpf_ = cpf_.set_index(["DATE","YEARMONTH"]).stack().reset_index()
    cpf_.columns = ["DATE","YEARMONTH","Asset","VALUE"]
    cpf_["Asset"] = cpf_["Asset"].map(lambda x: "CPF - " + x)

    investment_ = investment.groupby(["YEARMONTH"]).sum()[["VALUE"]].reset_index()
    investment_["Asset"] = "Investment"

    df = pd.concat([bank_, cpf_, investment_], sort=True, ignore_index=True)

    # drop yearmonth that is not complete
    yearmonth = df[df["Asset"]=="Savings"]["YEARMONTH"].unique()
    df = df[df["YEARMONTH"].isin(yearmonth)].copy()
    # add liquidity
    df["Liquidity"] = df["Asset"].map(lambda x: "non-Liquid" if x.startswith("CPF") else "Liquid")

    # generate income df
    # process bank statement
    bank_income = bank[bank["BANK_TYPE"].isin(BANK_TYPE)].drop(["DATE","ID","HISTORICAL"], axis=1).rename({"BANK_TYPE":"TYPE"},axis=1) # filter to income
    
    # process cpf
    cpf_income = cpf[(cpf["CODE"]=="CON") & (cpf["REF"].isin(["A","B"]))].drop(["DATE","CODE","ID","HISTORICAL"], axis=1).copy() # filter to cpf contribution from dsta income
    cpf_income = cpf_income.groupby(["YEARMONTH","REF"]).sum().reset_index()
    cpf_income = cpf_income.melt(id_vars=["YEARMONTH","REF"], value_name = "VALUE", var_name = "TYPE")
    cpf_income = cpf_income[cpf_income["VALUE"]>0].copy()

    # combine both sources
    income_df = pd.concat([bank_income, cpf_income], sort=True, ignore_index=True)

    def remove_employer(row):
        if row["TYPE"]=="Salary":
            new_value = row["VALUE"]
        else:
            new_value = row["VALUE"] * 20/37
        
        return new_value

    income_df["VALUE_EMPLOYEE"] = income_df.apply(remove_employer, axis=1)

    # load debt
    debt = requests.get("http://127.0.0.1:8001/api/debt")
    debt = pd.DataFrame.from_dict(debt.json())
    debt["DATE"] = pd.to_datetime(debt["DATE"], format="%Y-%m-%d")

    # load tax and relief
    tax_df = requests.get("http://127.0.0.1:8001/api/tax")
    tax_df = pd.DataFrame.from_dict(tax_df.json())

    relief = requests.get("http://127.0.0.1:8001/api/relief")
    relief = pd.DataFrame.from_dict(relief.json())

    return df.to_dict(orient="records"), debt.to_dict(orient = "records"), income_df.to_dict(orient="records"), tax_df.to_dict(orient="records"), relief.to_dict(orient="records")



def serve_layout():
    return html.Div([
        dcc.Location(id='url', refresh=True),
        navbar,
        html.Div(id='page-content'),

        # data store
        dcc.Store(id="df-store"),
        dcc.Store(id="debt-store"),
        dcc.Store(id="income-store"),
        dcc.Store(id="tax-store"),
        dcc.Store(id="relief-store")
    ])
app.layout = serve_layout


@app.callback(
    Output(component_id='page-content', component_property='children'),
    Output(component_id='df-store', component_property='data'),
    Output(component_id='debt-store', component_property='data'),
    Output(component_id='income-store', component_property='data'),
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
    df, debt, income_df, tax_df, relief = load_data()

    return layout, df, debt, income_df, tax_df, relief

# start server
if __name__ == '__main__':
    app.run_server(port=8051,debug=True)