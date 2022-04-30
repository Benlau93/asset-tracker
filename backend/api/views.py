from re import L
from rest_framework.views import APIView
from rest_framework import status
from rest_framework.response import Response
import requests
import pandas as pd
import datetime
from .pdf_extraction import bank_extraction, cpf_extraction
from .models import CPFModel, BankModel, InvestmentModel

from .serializers import CPFSerialzier, InvestmentSerializer, BankSerializer

# Create your views here.

class InvestmentAPIViews(APIView):
    investment_serializer = InvestmentSerializer

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
                DATE = record["DATE"],
                YEARMONTH = record["YEARMONTH"],
                INVESTMENT_TYPE = record["INVESTMENT_TYPE"],
                VALUE = record["VALUE"]
            ) for record in df_records]

        InvestmentModel.objects.bulk_create(model_instances)

        return Response(status=status.HTTP_200_OK)


class PDFExtractionViews(APIView):

    def get(self, request, format=None):
        cpf = cpf_extraction()
        bank = bank_extraction()

        if type(bank) == int:
            print("No Further Bank Statement Extraction Needed ...")
        else:
            print("Extracted New Bank Statement Records ...")
            # insert into bank model
            df_records = bank.to_dict(orient="records")
            model_instances = [BankModel(
                DATE = record["DATE"],
                YEARMONTH = record["YEARMONTH"],
                BANK_TYPE = record["BANK_TYPE"],
                VALUE = record["VALUE"]
            ) for record in df_records]

            BankModel.objects.bulk_create(model_instances)

        if type(cpf) == int:
            print("No Further CPF Extraction Needed ...")

        else:
            print("Extracted New CPF Transaction Records ...")
            # delete exisitng cpf data
            exist = CPFModel.objects.all().delete()

            # insert into cpf model
            df_records =  cpf.to_dict(orient="records")
            model_instances = [CPFModel(
                ID = record["ID"],
                DATE = record["DATE"],
                YEARMONTH = record["YEARMONTH"],
                CODE = record["CODE"],
                OA = record["OA"],
                SA = record["SA"],
                MA = record["MA"]
            ) for record in df_records]

            CPFModel.objects.bulk_create(model_instances)

        return Response(status = status.HTTP_200_OK)
