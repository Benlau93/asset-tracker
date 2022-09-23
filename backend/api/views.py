from rest_framework.views import APIView
from rest_framework import status
from rest_framework.response import Response
import requests
import pandas as pd
import datetime
from dateutil.relativedelta import relativedelta
import os
import yfinance as yf

from .pdf_extraction import bank_extraction, cpf_extraction, bank_extraction_historical, cpf_extraction_historical
from .models import CPFModel, BankModel, InvestmentModel, DebtModel, TaxModel, ReliefModel
from .serializers import CPFSerialzier, InvestmentSerializer, BankSerializer, DebtSerializer, TaxSerializer, ReliefSerializer

# Create your views here.

class ExtractInvestmentView(APIView):
    investment_serializer = InvestmentSerializer

    def get(self, request, format=None):

        # check if previous month record in investmentmodel
        prev_month = pd.to_datetime(datetime.date.today() - relativedelta(months=1)).strftime("%b %Y")
        query = InvestmentModel.objects.filter(ID = prev_month)

        if len(query) == 1:
            print("No Further Investment Extraction Needed ...")
            return Response(status=status.HTTP_200_OK)

        # get current portfolio
        try:
            portfolio = requests.get("http://127.0.0.1:8000/api/open")
            transaction = requests.get("http://127.0.0.1:8000/api/transaction")
        except:
            print("Investment Connection Failed, unable to extract Investment data")
            return Response(status=status.HTTP_400_BAD_REQUEST)
        
        # get current month
        current_month = datetime.date.today()
        current_month = pd.to_datetime(f"{current_month.year}-{current_month.month}-01", format="%Y-%m-%d")

        # convert to dataframe
        portfolio = pd.DataFrame.from_dict(portfolio.json())[["symbol","date_open","total_quantity","avg_exchange_rate"]].copy()
        transaction = pd.DataFrame.from_dict(transaction.json())[["symbol","date","action","quantity","exchange_rate"]].copy()

        # filter potfolio before this month
        portfolio["date_open"] = pd.to_datetime(portfolio["date_open"], format="%Y-%m-%d")
        portfolio = portfolio[portfolio["date_open"]<current_month].drop("date_open", axis=1).copy()
        symbol_list = portfolio["symbol"].unique()

        # filter transaction in current month
        transaction["date"] = pd.to_datetime(transaction["date"], format="%Y-%m-%d")
        transaction = transaction[(transaction["date"]>=current_month)].copy()

        # handle symbol in current portfolio
        trans_port = transaction[transaction["symbol"].isin(symbol_list)].copy()
        trans_port["quantity"] = trans_port.apply(lambda row: row["quantity"] * -1 if row["action"]=="Buy" else row["quantity"], axis=1) # format quantity to reverse current month transaction
        
        # handle symbols closed in current month
        trans_closed = transaction[~(transaction["symbol"].isin(symbol_list)) & (transaction["action"]=="Sell")].rename({"quantity":"total_quantity",
                                                                                                                        "exchange_rate":"avg_exchange_rate"}, axis=1)
        # merge and replicate previous month portfolio
        # change quantity based on transaction
        portfolio = pd.merge(portfolio, trans_port[["symbol","quantity"]], on="symbol", how="left")
        portfolio["quantity"] = portfolio["quantity"].fillna(0)
        portfolio["total_quantity"] = portfolio["total_quantity"] + portfolio["quantity"]
        portfolio = portfolio.drop(["quantity"], axis=1)

        # add back closed position
        portfolio = pd.concat([portfolio, trans_closed], sort=True, ignore_index=True, join="inner")

        # get portfolio current price
        symbol_list = " ".join(portfolio["symbol"].unique())
        data = yf.download(symbol_list, period = "30d", interval="1d", group_by="ticker", progress=False).reset_index()
        data = data.melt(id_vars="Date", var_name=["symbol","OHLC"], value_name="price").dropna()
        data = data[(data["OHLC"]=="Close") & (data["Date"]<current_month)].drop(["OHLC"],axis=1)
        data = data.sort_values(["symbol","Date"]).groupby("symbol").tail(1).drop("Date", axis=1)
        
        # get usd exchange rate
        exchange_rate = yf.download("SGDUSD=X", period = "30d", interval="1d",progress=False)
        exchange_rate = exchange_rate[["Close"]].reset_index()
        exchange_rate = 1/ exchange_rate[exchange_rate["Date"]<current_month].iloc[-1,1]
        
        # get total investment value for prev month
        investment = pd.merge(portfolio, data, on="symbol")
        investment["US_exchange"] = exchange_rate
        investment["avg_exchange_rate"] = investment.apply(lambda row: row["US_exchange"] if row["avg_exchange_rate"]>1 else row["avg_exchange_rate"], axis=1)
        investment["VALUE"] = investment["total_quantity"] * investment["avg_exchange_rate"] * investment["price"]
        investment["YEARMONTH"] = prev_month
        investment = investment.groupby("YEARMONTH").sum()["VALUE"].iloc[0]

        # insert to investment model
        data_upload = {"ID":prev_month,
                    "YEARMONTH":prev_month,
                    "VALUE":investment}

        investment_serialised = self.investment_serializer(data=data_upload)
        if investment_serialised.is_valid():
            
            investment_serialised.save()
            print("Added New Investment Value ...")
            return Response(status=status.HTTP_200_OK)
        else:
            print("Failed to add new Investment Value ")
            return Response(status=status.HTTP_400_BAD_REQUEST)


class PDFExtractionView(APIView):
    cpf_serializer = CPFSerialzier

    def get(self, request, format=None):
        cpf = cpf_extraction()
        bank = bank_extraction()

        if type(bank) == int:
            print("No Further Bank Statement Extraction Needed ...")
        else:
            
            # insert into bank model
            df_records = bank.to_dict(orient="records")
            model_instances = [BankModel(
                ID = str(record["DATE"]) + "|" + record["BANK_TYPE"] + "|" + str(round(record["VALUE"])),
                DATE = record["DATE"],
                YEARMONTH = record["YEARMONTH"],
                BANK_TYPE = record["BANK_TYPE"],
                VALUE = record["VALUE"],
            ) for record in df_records]

            BankModel.objects.bulk_create(model_instances)
            print("Extracted New Bank Statement Records ...")

        if type(cpf) == int:
            print("No Further CPF Extraction Needed ...")

        else:
            
            # get latest balance in db
            db_max_ym = cpf["DATE"].min() - relativedelta(months=1)
            db_max_ym = db_max_ym.strftime("%b %Y")
            cpf_db = CPFModel.objects.filter(YEARMONTH=db_max_ym).filter(CODE="BAL").get()
            cpf_db = self.cpf_serializer(cpf_db)
            cpf_db = pd.DataFrame.from_dict([cpf_db.data])
            cpf_db["DATE"] = pd.to_datetime(cpf_db["DATE"])

            # add initial balance to cpf
            cpf_bal = pd.concat([cpf_db,cpf], sort=True, ignore_index=True)

            # get BAL per month
            bal = cpf_bal.sort_values("DATE")[["OA","SA","MA"]].cumsum()
            bal = pd.merge(cpf_bal[["DATE","YEARMONTH"]], bal, left_index=True, right_index=True)
            bal["DATE"] = pd.to_datetime(bal["DATE"].dt.date + relativedelta(day=31))
            bal = bal.fillna(method="ffill")
            bal = bal.groupby("YEARMONTH").tail(1)
            bal["CODE"] = "BAL"

            # add to main cpf dataframe
            cpf = pd.concat([cpf,bal], sort=True, ignore_index=True)
            cpf = cpf.sort_values(["DATE"]).reset_index(drop=True).iloc[1:]

            # insert into cpf model
            cpf["TOTAL"] = cpf["OA"] + cpf["SA"] + cpf["MA"]
            cpf["TOTAL"] = cpf["TOTAL"].map(lambda x: str(round(x)))

            df_records =  cpf.to_dict(orient="records")
            model_instances = [CPFModel(
                ID = record["YEARMONTH"] + "|" + record["CODE"] + "|" + record["TOTAL"],
                DATE = record["DATE"],
                YEARMONTH = record["YEARMONTH"],
                CODE = record["CODE"],
                REF = record["REF"],
                OA = record["OA"],
                SA = record["SA"],
                MA = record["MA"]
            ) for record in df_records]

            CPFModel.objects.bulk_create(model_instances)
            print("Extracted New CPF Transaction Records ...")

        return Response(status = status.HTTP_200_OK)


class HistoricalExtractionView(APIView):

    def get(self, request, format=None):
        
        # read investment historical data
        investment_hist = pd.read_csv(os.path.join(r"C:\Users\ben_l\Desktop\Web Apps\Asset\backend\pdf\investment-historical","Investment-historical.csv"))
        investment_hist["DATE"] = pd.to_datetime(investment_hist["DATE"])

        # read initial debt data
        debt_hist =  pd.read_csv(os.path.join(r"C:\Users\ben_l\Desktop\Web Apps\Asset\backend\pdf\debt","debt.csv"))
        debt_hist["DATE"] = pd.to_datetime(debt_hist["DATE"])

        # pdf extraction of cpf and bank historical data
        cpf_hist = cpf_extraction_historical()
        bank_hist = bank_extraction_historical()

        # remove all historical data in db
        _ = BankModel.objects.filter(HISTORICAL=True).delete()
        _ = CPFModel.objects.filter(HISTORICAL=True).delete()
        _ = InvestmentModel.objects.filter(HISTORICAL=True).delete()
        _ = DebtModel.objects.all().delete()

        # insert into bank model
        df_records = bank_hist.to_dict(orient="records")
        model_instances = [BankModel(
            ID = str(record["DATE"]) + "|" + record["BANK_TYPE"] + "|" + str(round(record["VALUE"])),
            DATE = record["DATE"],
            YEARMONTH = record["YEARMONTH"],
            BANK_TYPE = record["BANK_TYPE"],
            VALUE = record["VALUE"],
            HISTORICAL = True
            ) for record in df_records]

        BankModel.objects.bulk_create(model_instances)
        print("Extracted Historical Bank Statement Records ...")


        # insert into cpf model
        cpf_hist["TOTAL"] = cpf_hist["OA"] + cpf_hist["SA"] + cpf_hist["MA"]
        cpf_hist["TOTAL"] = cpf_hist["TOTAL"].map(lambda x: str(round(x)))

        df_records =  cpf_hist.to_dict(orient="records")
        model_instances = [CPFModel(
                ID = record["YEARMONTH"] + "|" + record["CODE"] + "|" + record["TOTAL"],
                DATE = record["DATE"],
                YEARMONTH = record["YEARMONTH"],
                CODE = record["CODE"],
                REF = record["REF"],
                OA = record["OA"],
                SA = record["SA"],
                MA = record["MA"],
                HISTORICAL = True
            ) for record in df_records]

        CPFModel.objects.bulk_create(model_instances)
        
        print("Extracted Historical CPF Transaction Records ...")


        # insert to investment model
        df_records =  investment_hist.to_dict(orient="records")
        model_instances = [InvestmentModel(
                ID = record["YEARMONTH"] + "|" + record["INVESTMENT_TYPE"],
                DATE = record["DATE"],
                YEARMONTH = record["YEARMONTH"],
                INVESTMENT_TYPE = record["INVESTMENT_TYPE"],
                VALUE = record["VALUE"],
                HISTORICAL = True,
            ) for record in df_records]

        InvestmentModel.objects.bulk_create(model_instances)

        print("Extracted Historical Investment Data ...")

        # insert to debt model
        df_records =  debt_hist.to_dict(orient="records")
        model_instances = [DebtModel(
            ID = record["YEARMONTH"] + "|" + record["DEBT_TYPE"],
            DATE = record["DATE"],
            YEARMONTH = record["YEARMONTH"],
            DEBT_TYPE = record["DEBT_TYPE"],
            DEBT_VALUE = record["DEBT_VALUE"],
            INTEREST_RATE = record["INTEREST_RATE"],
            INTEREST_COMPOUND = record["INTEREST_COMPOUND"],
            REPAYMENT = record["REPAYMENT"],
            INTEREST = record["INTEREST"],
            REMAINING_VALUE = record["REMAINING_VALUE"]
            ) for record in df_records]

        DebtModel.objects.bulk_create(model_instances)

        print("Extracted Debt Baseline Data ...")

        return Response(status = status.HTTP_200_OK)

class CPFView(APIView):
    cpf_serializer = CPFSerialzier

    def get(self, request, format=None):
        data = CPFModel.objects.all()
        serializer = self.cpf_serializer(data, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class InvestmentView(APIView):
    investment_serialzier = InvestmentSerializer

    def get(self, request, format=None):
        data = InvestmentModel.objects.all()
        serializer = self.investment_serialzier(data, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class BankView(APIView):
    bank_serializer = BankSerializer

    def get(self, request, format=None):
        data = BankModel.objects.all()
        serializer = self.bank_serializer(data, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

class DebtView(APIView): 
    debt_serializer = DebtSerializer

    def get(self, request, format=None):
        data = DebtModel.objects.all()
        serializer = self.debt_serializer(data, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
            

class DebtRefreshView(APIView): # currently only works for 1 debt
    debt_serializer = DebtSerializer

    def get(self, request, format=None):
        data = DebtModel.objects.all()
        serializer = self.debt_serializer(data, many=True)

        # check if debt is updated
        current = datetime.date.today() - relativedelta(months=1)
        current = current.strftime("%b %Y")
        df = pd.DataFrame.from_dict(serializer.data)
        if len(df[df["YEARMONTH"]==current]) > 0:
            # debt is updated, return dataframe
            print("No Further Debt Refresh Needed ...")
            return Response(status=status.HTTP_200_OK)

        else:
            # update debt model
            df["DATE"] = pd.to_datetime(df["DATE"])
            current_max_date = df["DATE"].max()
            max_yearmonth = current_max_date.strftime("%b %Y")

            # add new entry
            debt_new = pd.DataFrame()

            # loop through by month till current month
            while max_yearmonth != current:
                _ = df.sort_values("DATE")
                new_debt = _.iloc[-1].copy()

                # get new date
                new_debt["DATE"] = new_debt["DATE"] + relativedelta(months=1)
                max_yearmonth = new_debt["DATE"].strftime("%b %Y")
                new_debt["YEARMONTH"] = max_yearmonth
                
                # get new debt value
                new_debt["DEBT_VALUE"] = new_debt["REMAINING_VALUE"]

                # calculate interest, only handle monthly and yearly
                if new_debt["INTEREST_COMPOUND"] == "Monthly":
                    new_debt["INTEREST"] = ((new_debt["INTEREST_RATE"] / 12) / 100 ) * new_debt["DEBT_VALUE"]
                elif new_debt["INTEREST_COMPOUND"] == "Annually" and new_debt["DATE"].month == 12:
                    new_debt["INTEREST"] = (new_debt["INTEREST_DATE"] / 100) * new_debt["DEBT_VALUE"]
                else:
                    new_debt["INTEREST"] = 0

                # calculate remaining value
                new_debt["REMAINING_VALUE"] = new_debt["DEBT_VALUE"] + new_debt["INTEREST"] - new_debt["REPAYMENT"]

                # add to df to be store in db
                df = df.append(new_debt, sort=True, ignore_index=True)
                debt_new = debt_new.append(new_debt, sort=True, ignore_index=True)

            # store in db
            # insert into debt model
            df_records =  debt_new.to_dict(orient="records")
            model_instances = [DebtModel(
                ID = record["YEARMONTH"] + "|" + record["DEBT_TYPE"],
                DATE = record["DATE"],
                YEARMONTH = record["YEARMONTH"],
                DEBT_TYPE = record["DEBT_TYPE"],
                DEBT_VALUE = record["DEBT_VALUE"],
                INTEREST_RATE = record["INTEREST_RATE"],
                INTEREST_COMPOUND = record["INTEREST_COMPOUND"],
                REPAYMENT = record["REPAYMENT"],
                INTEREST = record["INTEREST"],
                REMAINING_VALUE = record["REMAINING_VALUE"]
            ) for record in df_records]

            DebtModel.objects.bulk_create(model_instances)

            print("Refreshed Remaining Debt Value ...")

            return Response(status=status.HTTP_200_OK)
            

                
class TaxView(APIView):
    tax_serializer = TaxSerializer

    def get(self, request, format=None):
        data = TaxModel.objects.all()
        serializer = self.tax_serializer(data, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class ReliefView(APIView):
    relief_serializer = ReliefSerializer

    def get(self, request, format=None):
        data = ReliefModel.objects.all()
        serializer = self.relief_serializer(data, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
