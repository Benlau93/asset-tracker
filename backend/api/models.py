from django.db import models

# Create your models here.
class CPFModel(models.Model):
    ID = models.IntegerField(primary_key=True)
    DATE = models.DateField(blank=False)
    YEARMONTH = models.CharField(blank=False, max_length=10)
    CODE = models.CharField(max_length=10)
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