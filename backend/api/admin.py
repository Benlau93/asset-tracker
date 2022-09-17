from django.contrib import admin
from .models import BankModel, CPFModel, InvestmentModel, DebtModel, TaxModel, ReliefModel

# Register your models here.
admin.site.register(BankModel)
admin.site.register(CPFModel)
admin.site.register(InvestmentModel)
admin.site.register(DebtModel)
admin.site.register(TaxModel)
admin.site.register(ReliefModel)