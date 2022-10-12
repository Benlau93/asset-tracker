# Asset Tracker
Asset Tracker is a full-stack financial asset tracker web app that aims to track monthly total asset values of an individual.

## Overview
Assets tracked in this project are mainly from the following 3 sources:
1. Cash (Bank account)
2. Investment (tracked with a separate web app [Trading Dashboard](https://github.com/Benlau93/trading-dashboard))
3. CPF (Singapore Mandatory Social Security Savings Scheme)

### Data Source
1. Cash <br>
Current Cash flow is captured through monthly upload of bank e-statement. Using python PDF reader, e-statement are broken down into their respective transaction and important transactions such as monthly income and balance amount are captured and stored into the database.

2. Investment <br>
API calls are made to the [Trading Dashboard](https://github.com/Benlau93/trading-dashboard)) to extract monthly investment value.

3. CPF <br>
Similar to Cash saving, monthly CPF e-statement are uploaded and transaction are extracted and stored.

## Technology Used
1. Web Frontend - DASH Plotly (Python)
2. Backend API - Django Restful API (Python)
3. Database - Sqlite3 (RDBMS)


## Demo
![Asset Tracker](./img/asset_main.png)