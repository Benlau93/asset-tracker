from rest_framework.views import APIView
from rest_framework import status
from rest_framework.response import Response
import requests
import pandas as pd
import datetime
from dateutil.relativedelta import relativedelta
import os

from .pdf_extraction import bank_extraction, cpf_extraction, bank_extraction_historical, cpf_extraction_historical
from .models import CPFModel, BankModel, InvestmentModel, DebtModel
from .serializers import CPFSerialzier, InvestmentSerializer, BankSerializer, DebtSerializer

# Create your views here.

class ExtractInvestmentView(APIView):

    def get(self, request, format=None):

        # get current portfolio
        portfolio = requests.get("http://127.0.0.1:8000/api/open")
        portfolio = pd.DataFrame.from_dict(portfolio.json())

        # get ticker information
        ticker = requests.get("http://127.0.0.1:8000/api/ticker")
        ticker = pd.DataFrame.from_dict(ticker.json())
        ticker["INVESTMENT_TYPE"] = ticker["type"] + " - " + ticker["currency"]

        # refresh current price and get current investment value
        refresh = requests.get("http://127.0.0.1:8000/api/refresh")
        historical = requests.get("http://127.0.0.1:8000/api/historical")
        historical = pd.DataFrame.from_dict(historical.json())
        historical["date"] = pd.to_datetime(historical["date"], format="%Y-%m-%d")
        historical = historical.sort_values(["symbol","date"]).groupby(["symbol"]).tail(1)[["symbol","pl_sgd"]].copy()

        # merge ticker information to current investment
        portfolio = pd.merge(portfolio, ticker[["symbol","INVESTMENT_TYPE"]], on="symbol")
        # merge pl to get current value
        portfolio = pd.merge(portfolio, historical, on="symbol")
        portfolio["VALUE"] = portfolio["total_value_sgd"] + portfolio["pl_sgd"]

        # get total value per investment type
        portfolio = portfolio.groupby(["INVESTMENT_TYPE"]).sum()[["VALUE"]].reset_index()
        portfolio["DATE"] = pd.to_datetime(datetime.date.today())

        # add year month
        portfolio["YEARMONTH"] = portfolio["DATE"].dt.strftime("%b %Y")

        # handle data model
        # if there are data for current year month, delete it
        try:
            # delete existing record
            record = InvestmentModel.objects.filter(YEARMONTH = portfolio["YEARMONTH"].iloc[0])
            record.delete()
            print("Updated Existing Investment Value ...")
        except:
            print("Added New Investment Value ...")


        # insert to investment model
        df_records =  portfolio.to_dict(orient="records")
        model_instances = [InvestmentModel(
                ID = record["YEARMONTH"] + "|" + record["INVESTMENT_TYPE"],
                DATE = record["DATE"],
                YEARMONTH = record["YEARMONTH"],
                INVESTMENT_TYPE = record["INVESTMENT_TYPE"],
                VALUE = record["VALUE"]
            ) for record in df_records]

        InvestmentModel.objects.bulk_create(model_instances)

        return Response(status=status.HTTP_200_OK)


class PDFExtractionView(APIView):

    def get(self, request, format=None):
        cpf = cpf_extraction()
        bank = bank_extraction()

        if type(bank) == int:
            print("No Further Bank Statement Extraction Needed ...")
        else:
            
            # insert into bank model
            df_records = bank.to_dict(orient="records")
            model_instances = [BankModel(
                ID = record["YEARMONTH"] + "|" + record["BANK_TYPE"] + "|" + str(round(record["VALUE"],2)),
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
            
            # delete non-historical cpf data
            _ = CPFModel.objects.filter(HISTORICAL=False).delete()

            # insert into cpf model
            df_records =  cpf.to_dict(orient="records")
            model_instances = [CPFModel(
                ID = record["YEARMONTH"] + "|" + record["CODE"] + record["REF"] + str(record["OA"] + record["SA"] + record["MA"]),
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
        investment_hist = pd.read_csv(os.path.join(r"C:\Users\ben_l\Desktop\Asset Tracking\Asset\backend\pdf\investment-historical","Investment-historical.csv"))
        investment_hist["DATE"] = pd.to_datetime(investment_hist["DATE"])

        # pdf extraction of cpf and bank historical data
        cpf_hist = cpf_extraction_historical()
        bank_hist = bank_extraction_historical()

        # remove all historical data in db
        _ = BankModel.objects.filter(HISTORICAL=True).delete()
        _ = CPFModel.objects.filter(HISTORICAL=True).delete()
        _ = InvestmentModel.objects.filter(HISTORICAL=True).delete()

        # insert into bank model
        df_records = bank_hist.to_dict(orient="records")
        model_instances = [BankModel(
            ID = record["YEARMONTH"] + "|" + record["BANK_TYPE"] + "|" + str(round(record["VALUE"])),
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

class DebtView(APIView): # currently only works for 1 debt
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
            return Response(serializer.data, status=status.HTTP_200_OK)

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

            # re-query db and return db
            data = DebtModel.objects.all()
            serializer = self.debt_serializer(data, many=True)

            return Response(serializer.data, status=status.HTTP_200_OK)

                



