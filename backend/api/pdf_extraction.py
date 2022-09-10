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
                        value = float(pdf_text[i +3].replace(",",""))
                        BANK_TYPE = "Salary"
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
                        BANK_TYPE = "Salary"
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
                    BANK_TYPE = "Salary"
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

    
    for f in DIR_FILE:
        # if file is the same, no further processing needed
        if f in hist:
            continue

        else:

            filename += f  + "\n"

            # read cpf pdf
            _ = tabula.read_pdf(os.path.join(CPF_DIR,f), stream=False, pages=1)[0]
            # add to main dataframe
            cpf = cpf.append(_, sort=True, ignore_index=True)

    if len(cpf) == 0:
        return 0

    else:

        # format cpf
        cpf.columns = ["ID","CODE","_","REF","OA","SA","MA","_"]
        cpf = cpf.drop("_",axis=1)

        def format_row(row):
            id = row["ID"].replace(",","")

            if len(id)==11:
                row["DATE"] = id
            else:
                row["DATE"] = id[:11]
                row["CODE"] = id[11:14]
            
                # get account value
                pat = r"-?\d+\.\d{2}"
                row["OA"], row["SA"], row["MA"] = re.findall(pat, id)

                # get REF
                ref_index = re.search(row["OA"], id).start() - 1
                ref = id[ref_index]
                if ref in ["A","B"]:
                    row["REF"] = ref

            return row

        cpf = cpf.apply(format_row, axis=1)
        cpf = cpf.drop("ID", axis=1)

        # format date
        cpf["DATE"] = pd.to_datetime(cpf["DATE"], format="%d %b %Y")
        cpf["YEARMONTH"] = cpf["DATE"].dt.strftime("%b %Y")

        # format acc
        for acc in accounts:
            cpf[acc] = cpf[acc].map(lambda x: round(float(str(x).replace(",","")),2))
        cpf = cpf[cpf["CODE"]!="BAL"].copy()

        # write to historical text
        with open(os.path.join(os.path.split(CPF_DIR)[0],"historical-cpf.txt"),"a") as f:
            f.writelines(filename)

        return cpf


def cpf_extraction_historical():
    CPF_DIR = r"C:\Users\ben_l\Desktop\Asset Tracking\Asset\backend\pdf\cpf-historical"

    # read all historical cpf records
    cpf_2020 = tabula.read_pdf(os.path.join(CPF_DIR,"CPF Yearly Statement 2020.pdf"), stream=False, pages = "all")[0]
    cpf_2021 = tabula.read_pdf(os.path.join(CPF_DIR,"CPF Yearly Statement 2021.pdf"), stream=True, pages = "all")[1]

    # 2020 processing
    cpf_2020.columns = ["ID","REF","OA","SA","MA"]
    cpf_2020 = cpf_2020.iloc[cpf_2020[cpf_2020["ID"]=="01 JAN BAL"].index[0]:].copy()

    # get date and code
    def extract(row):
        id = row["ID"]
        row["DATE"] = pd.to_datetime(id[:6] + " 2020", format = "%d %b %Y")
        row["CODE"] = id[7:10]

        return row

    cpf_2020 = cpf_2020.apply(extract, axis=1)

    # drop ID
    cpf_2020 = cpf_2020.drop("ID",axis=1)

    # get initial bal
    initial_balance = cpf_2020[cpf_2020["CODE"]=="BAL"].sort_values(["DATE"]).head(1)


    # only retain transaction
    cpf_2020 = cpf_2020[cpf_2020["CODE"]!="BAL"].copy()

    # 2021 processing
    cpf_2021.columns = ["DATE","CODE","_","REF","OA","SA","MA"]
    cpf_2021 = cpf_2021[cpf_2021["CODE"]!="BAL"].drop("_", axis=1)

    # process date, only retain to Jun records
    cpf_2021["DATE"] = cpf_2021["DATE"].map(lambda x: pd.to_datetime(x +" 2021",format="%d %b %Y"))
    cpf_2021 = cpf_2021[cpf_2021["DATE"].dt.month<7].copy()


    # combine
    cpf_hist = pd.concat([initial_balance, cpf_2020, cpf_2021], sort=True, ignore_index=True)[["DATE","CODE","REF","OA","SA","MA"]]

    # format
    cpf_hist["YEARMONTH"] = cpf_hist["DATE"].dt.strftime("%b %Y")
    for acc in ["OA","SA","MA"]:
        cpf_hist[acc] = cpf_hist[acc].str.replace(",|\$","").astype(np.float32)
        cpf_hist[acc] = cpf_hist[acc].map(lambda x: np.nan if x==0 else x)

    # get BAL per month
    bal = cpf_hist.sort_values("DATE")[["OA","SA","MA"]].cumsum()
    bal = pd.merge(cpf_hist[["DATE","YEARMONTH"]], bal, left_index=True, right_index=True)
    bal["DATE"] = pd.to_datetime(bal["DATE"].dt.date + relativedelta(day=31))
    bal = bal.fillna(method="ffill")
    bal = bal.groupby("YEARMONTH").tail(1)
    bal["CODE"] = "BAL"

    # add to main cpf_hist dataframe
    cpf_hist = pd.concat([cpf_hist,bal], sort=True, ignore_index=True)
    cpf_hist = cpf_hist.sort_values(["DATE"]).reset_index(drop=True)
    cpf_hist[["OA","SA","MA"]] = cpf_hist[["OA","SA","MA"]].fillna(0)

    return cpf_hist


