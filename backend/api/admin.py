from django.contrib import admin
from .models import DataModel, BankModel, CPFModel

# Register your models here.
admin.site.register(DataModel)
admin.site.register(BankModel)
admin.site.register(CPFModel)
