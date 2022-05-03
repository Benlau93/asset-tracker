from dash import html
from dash import dcc
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output, State
from app import app
from datetime import date
import requests
import pandas as pd

# start server
if __name__ == '__main__':
    app.run_server(debug=True)