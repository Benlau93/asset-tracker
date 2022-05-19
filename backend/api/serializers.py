from rest_framework import serializers
from .models import InvestmentModel, BankModel, CPFModel, DebtModel

class InvestmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = InvestmentModel
        fields = "__all__"


class BankSerializer(serializers.ModelSerializer):
    class Meta:
        model = BankModel
        fields = "__all__"

class CPFSerialzier(serializers.ModelSerializer):
    class Meta:
        model = CPFModel
        fields = "__all__"

class DebtSerializer(serializers.ModelSerializer):
    class Meta:
        model = DebtModel
        fields = "__all__"