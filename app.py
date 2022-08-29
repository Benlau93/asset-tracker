import dash
import dash_bootstrap_components as dbc

# initialize app
external_stylesheets = [dbc.themes.FLATLY]
app = dash.Dash(__name__, external_stylesheets=external_stylesheets,suppress_callback_exceptions=True)
app.title = "Asset Tracking"
server = app.server