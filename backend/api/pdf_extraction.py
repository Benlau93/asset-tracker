import pandas as pd
import os
import PyPDF4 as PDF
import tabula
import re
from dateutil.relativedelta import relativedelta
import numpy as np
import warnings

warnings.filterwarnings("ignore")

def bank_extraction():
    STATEMENT_DIR = r"C:\Users\ben_l\Desktop\Asset Tracking\Asset\backend\pdf\estatement"

    # check processed statement
    with open(os.path.join(os.path.split(STATEMENT_DIR)[0],"historical-bank.txt"),"r") as f:
        hist = f.readlines()
    hist = list(map(lambda x: x[:-1],hist))
    
    # initialize
    bank = pd.DataFrame()
    filename = ""

    for f in os.listdir(STATEMENT_DIR):

        # do not processed statement that are already in db
        if f in hist:
            continue
        else:
            filename += f  + "\n"

        # read pdf
        pdf = open(os.path.join(STATEMENT_DIR,f), "rb")
        pdf_reader = PDF.PdfFileReader(pdf)

        # concat pdf pages
        num_page = pdf_reader.numPages
        pdf_text = ""

        for i in range(num_page):
            pdf_text = pdf_text + "\n" + pdf_reader.getPage(i).extractText()
        pdf_text = pdf_text.split("\n")
        pdf_text = list(map(lambda x: x.strip(),pdf_text))
        

        # remove USD account
        try:
            usd = pdf_text.index("UNITED STATES DOLLAR")
            pdf_text = pdf_text[:usd]
            
        except:
            pdf_text = pdf_text
        
        # define pdf size
        pdf_size = len(pdf_text)
        
        # get end date and year
        date_location = pdf_text.index("Details of Your DBS Multiplier Account") +1
        end_date = pdf_text[date_location].split("to")[-1].strip()
        end_date = pd.to_datetime(end_date).date()
        year = end_date.year


        # get month end amount
        end_amount_location = pdf_text[::-1].index("Balance Carried Forward") -2
        end_amount = float(pdf_text[len(pdf_text) - end_amount_location].replace(",",""))


        # add to main dataframe
        bank = pd.concat([bank, pd.DataFrame({"DATE":[end_date],"YEARMONTH":[end_date.strftime("%b %Y")],"BANK_TYPE":["END"],"VALUE":end_amount})], sort=True, ignore_index=True)
        
        # loop through all statement and record relavant entry
        for i in range(pdf_size):
            
            # DSTA salary
            if pdf_text[i] == "DSTA":
                try:
                    value = float(pdf_text[i +2].replace(",",""))
                    BANK_TYPE = "SALARY"
                except:
                    continue

                # medium payment
            elif "STRIPE" in pdf_text[i]:
                value = float(pdf_text[i +3].replace(",",""))
                BANK_TYPE = "Medium"

            else:
                continue


            # format date
            date = pdf_text[i -2]
            date = pd.to_datetime(date+f" {year}", format="%d %b %Y").date()
            yearmonth = date.strftime("%b %Y")

            # append to main dataframe
            _ = pd.DataFrame({"DATE":[date],"YEARMONTH":[yearmonth],"BANK_TYPE":[BANK_TYPE],"VALUE":[value]})
            bank = pd.concat([bank, _], sort=True, ignore_index=True)

        if len(bank) == 0:
            return 0
        else:

            # write to txt file to record as processed
            with open(os.path.join(os.path.split(STATEMENT_DIR)[0],"historical-bank.txt"),"a") as f:
                f.writelines(filename)

            return bank

def bank_extraction_historical():
    STATEMENT_DIR = r"C:\Users\ben_l\Desktop\Asset Tracking\Asset\backend\pdf\estatement-historical"
    
    # initialize
    bank_hist = pd.DataFrame()
    for f in os.listdir(STATEMENT_DIR):

        # determine format
        format = 1 if f.startswith("01zz") else 0

        # read pdf
        pdf = open(os.path.join(STATEMENT_DIR,f), "rb")
        pdf_reader = PDF.PdfFileReader(pdf)

        # concat pdf pages
        num_page = pdf_reader.numPages
        pdf_text = ""

        for i in range(num_page):
            pdf_text = pdf_text + "\n" + pdf_reader.getPage(i).extractText()
        pdf_text = pdf_text.split("\n")
        pdf_text = list(map(lambda x: x.strip(),pdf_text))
        

        # remove USD account
        try:
            usd = pdf_text.index("UNITED STATES DOLLAR")
            pdf_text = pdf_text[:usd]
            
        except:
            pdf_text = pdf_text
        
        # define pdf size
        pdf_size = len(pdf_text)
        
        # get end date and year
        date_location = pdf_text.index("DBS Multiplier Account") +1 if format ==1 else pdf_text.index("Details of Your DBS Multiplier Account") +1
        end_date = pdf_text[date_location].split("to")[-1].strip()
        end_date = pd.to_datetime(end_date).date()
        year = end_date.year


        # get month end amount
        end_amount_location = pdf_text[::-1].index("Balance Carried Forward")
        end_amount_location = end_amount_location  if format ==1 else end_amount_location -2
        end_amount = float(pdf_text[len(pdf_text) - end_amount_location].replace(",",""))


        # add to main dataframe
        bank_hist = pd.concat([bank_hist, pd.DataFrame({"DATE":[end_date],"YEARMONTH":[end_date.strftime("%b %Y")],"BANK_TYPE":["END"],"VALUE":end_amount})], sort=True, ignore_index=True)
        
        # loop through all statement and record relavant entry
        for i in range(pdf_size):
            
            # DSTA salary
            if format ==0:

                # DSTA
                if pdf_text[i] == "DSTA":
                    try:
                        value = float(pdf_text[i +2].replace(",",""))
                        BANK_TYPE = "SALARY"
                    except:
                        continue

                # medium payment
                elif "STRIPE" in pdf_text[i]:
                    value = float(pdf_text[i +3].replace(",",""))
                    BANK_TYPE = "Medium"

                else:
                    continue


                # format and append
                date = pdf_text[i -2]


            else:

                # DSTA salary
                if pdf_text[i] == "GIRO Salary":
                    value = float(pdf_text[i +1].replace(",",""))
                    BANK_TYPE = "SALARY"
                    date = pdf_text[i -1]

                # stripe
                elif "STRIPE" in pdf_text[i]:
                    try: 
                        value = float(pdf_text[i -2].replace(",",""))
                        date = pdf_text[i -4]
                    except:
                        value = float(pdf_text[i -1].replace(",",""))
                        date = pdf_text[i -3]

                    BANK_TYPE = "Medium"
                    

                else:
                    continue

            date = pd.to_datetime(date+f" {year}", format="%d %b %Y").date()
            yearmonth = date.strftime("%b %Y")

            # append to main dataframe
            _ = pd.DataFrame({"DATE":[date],"YEARMONTH":[yearmonth],"BANK_TYPE":[BANK_TYPE],"VALUE":[value]})
            bank_hist = pd.concat([bank_hist, _], sort=True, ignore_index=True)

    return bank_hist

def cpf_extraction():
    CPF_DIR = r"C:\Users\ben_l\Desktop\Asset Tracking\Asset\backend\pdf\cpf"

    # check historical
    with open(os.path.join(os.path.split(CPF_DIR)[0],"historical-cpf.txt"),"r") as f:
        hist = f.readlines()
    hist = list(map(lambda x: x[:-1],hist))

    # initialize
    cpf = pd.DataFrame()
    filename = ""
    accounts = ["OA","SA","MA"]
    DIR_FILE = os.listdir(CPF_DIR)

    # if file is the same, no further processing needed
    if sorted(DIR_FILE) == sorted(hist):
        return 0

    else:

        # read all cpf transaction
        cpf = pd.DataFrame()

        # loop all transaction history and add to dataframe
        for f in DIR_FILE:

            # record filename
            filename += f  + "\n"
            
            # read cpf pdf
            _ = tabula.read_pdf(os.path.join(CPF_DIR,f), stream=True, pages=1)[0]
            _.columns = ["DATE","CODE","YEAR","REF","OA","SA","MA"]
            _ = _.drop(["YEAR"], axis=1) # drop unwanted columns

            # add to main dataframe
            cpf = cpf.append(_, sort=True, ignore_index=True)

        # format cpf
        cpf["DATE"] = pd.to_datetime(cpf["DATE"])
        cpf["YEARMONTH"] = cpf["DATE"].dt.strftime("%b %Y")

        for acc in accounts:
            cpf[acc] = cpf[acc].str.replace(",","").astype(np.float32)
            cpf[acc] = cpf[acc].map(lambda x: np.nan if x==0 else x)

        cpf = cpf.sort_values(["DATE"]).reset_index(drop=True)

        # get initial balance
        cpf.loc[0,"CODE"] = "INITAL"
        cpf = cpf[cpf["CODE"]!="BAL"].copy()

        # get BAL per month
        bal = cpf.sort_values("DATE")[["OA","SA","MA"]].cumsum()
        bal = pd.merge(cpf[["DATE","YEARMONTH"]], bal, left_index=True, right_index=True)
        bal["DATE"] = pd.to_datetime(bal["DATE"].dt.date + relativedelta(day=31))
        bal = bal.fillna(method="ffill")
        bal = bal.groupby("YEARMONTH").tail(1)
        bal["CODE"] = "BAL"

        # add to main cpf dataframe
        cpf = pd.concat([cpf,bal], sort=True, ignore_index=True)
        cpf = cpf.sort_values(["DATE"]).reset_index(drop=True)
        
        # fillna
        cpf[["OA","SA","MA"]] = cpf[["OA","SA","MA"]].fillna(0)

        # write to historical text
        with open(os.path.join(os.path.split(CPF_DIR)[0],"historical-cpf.txt"),"w") as f:
            f.writelines(filename)

        return cpf


def cpf_extraction_historical():
    CPF_DIR = r"C:\Users\ben_l\Desktop\Asset Tracking\Asset\backend\pdf\cpf-historical"

    # initialize
    cpf_hist = pd.DataFrame()
    accounts = ["OA","SA","MA"]

    # read all cpf transaction
    cpf_hist = pd.DataFrame()

    # loop all yearly transaction and add to dataframe
    for f in os.listdir(CPF_DIR):
            
        # read cpf pdf
        _ = tabula.read_pdf(os.path.join(CPF_DIR,f), stream=True, pages=1)[0]
        _.columns = ["DATE","CODE","YEAR","REF","OA","SA","MA"]
        _ = _.drop(["YEAR"], axis=1) # drop unwanted columns

        # add to main dataframe
        cpf_hist = cpf_hist.append(_, sort=True, ignore_index=True)

        # format cpf
        cpf_hist["DATE"] = pd.to_datetime(cpf_hist["DATE"])
        cpf_hist["YEARMONTH"] = cpf_hist["DATE"].dt.strftime("%b %Y")

        for acc in accounts:
            cpf_hist[acc] = cpf_hist[acc].str.replace(",","").astype(np.float32)
            cpf_hist[acc] = cpf_hist[acc].map(lambda x: np.nan if x==0 else x)

        cpf_hist = cpf_hist.sort_values(["DATE"]).reset_index(drop=True)

        # get initial balance
        cpf.loc[0,"CODE"] = "INITAL"
        cpf = cpf[cpf["CODE"]!="BAL"].copy()

        # get BAL per month
        bal = cpf.sort_values("DATE")[["OA","SA","MA"]].cumsum()
        bal = pd.merge(cpf[["DATE","YEARMONTH"]], bal, left_index=True, right_index=True)
        bal["DATE"] = pd.to_datetime(bal["DATE"].dt.date + relativedelta(day=31))
        bal = bal.fillna(method="ffill")
        bal = bal.groupby("YEARMONTH").tail(1)
        bal["CODE"] = "BAL"

        # add to main cpf dataframe
        cpf = pd.concat([cpf,bal], sort=True, ignore_index=True)
        cpf_hist = cpf_hist.sort_values(["DATE"]).reset_index(drop=True)
        
        # fillna
        cpf_hist[["OA","SA","MA"]] = cpf_hist[["OA","SA","MA"]].fillna(0)

        return cpf_hist
