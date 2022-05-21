from django.contrib import admin
from .models import BankModel, CPFModel, InvestmentModel, DebtModel

# Register your models here.
admin.site.register(BankModel)
admin.site.register(CPFModel)
admin.site.register(InvestmentModel)
admin.site.register(DebtModel)