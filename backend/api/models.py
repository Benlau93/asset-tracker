from django.db import models

# Create your models here.
class CPFModel(models.Model):
    ID = models.IntegerField(primary_key=True)
    DATE = models.DateField(blank=False)
    YEARMONTH = models.CharField(blank=False, max_length=10)
    CODE = models.CharField(max_length=10)
    REF = models.CharField(max_length=10)
    OA = models.FloatField()
    SA = models.FloatField()
    MA = models.FloatField()

class InvestmentModel(models.Model):
    DATE = models.DateField(blank=False)
    YEARMONTH = models.CharField(blank=False, max_length=10)
    INVESTMENT_TYPE = models.CharField(max_length=50, blank=False)
    VALUE = models.FloatField(blank=False)

class BankModel(models.Model):
    DATE = models.DateField(blank=False)
    YEARMONTH = models.CharField(blank=False, max_length=10)
    BANK_TYPE = models.CharField(max_length=20, blank=False)
    VALUE = models.FloatField(blank=False)

class DebtModel(models.Model):
    DATE = models.DateField(blank=False)
    YEARMONTH = models.CharField(blank=False, max_length=10)
    DEBT_TYPE = models.CharField(blank=False, max_length=50)
    DEBT_VALUE = models.FloatField(blank=False)
    INTEREST_RATE = models.FloatField(blank=False)
    INTEREST_COMPOUND = models.CharField(blank=False, max_length=20)
    REPAYMENT = models.FloatField(blank=False)
    INTEREST = models.FloatField(blank=False)
    REMAINING_VALUE = models.FloatField(blank=False)