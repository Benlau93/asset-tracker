# Asset Tracker
Asset Tracker is a full-stack financial asset tracker web app that aims to track monthly total asset values of an individual.

## Overview
Assets tracked in this project are mainly from the following 3 sources:
1. Cash (Bank account)
2. Investment (tracked with a separate web app [Trading Dashboard](https://github.com/Benlau93/trading-dashboard))
3. CPF (Singapore Mandatory Social Security Savings Scheme)

### Data Source
1. Cash <br>
Current Cash flow is captured through monthly upload of bank e-statement. Using python PDF reader, e-statement are broken down into their respective transaction and important transaction such as monthly income, balance amount are captured and stored into the database.

2. Investment <br>
API calls are made to the [Trading Dashboard](https://github.com/Benlau93/trading-dashboard)) to extract monthly investment value.