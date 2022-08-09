from django.urls import path
from .views import ExtractInvestmentView, PDFExtractionView, CPFView, BankView, InvestmentView, DebtView, HistoricalExtractionView, TaxView, ReliefView

urlpatterns = [
    path("extract-investment", ExtractInvestmentView.as_view()),
    path("extract", PDFExtractionView.as_view()),
    path("historical", HistoricalExtractionView.as_view()),
    path("cpf",CPFView.as_view()),
    path("bank",BankView.as_view()),
    path("investment",InvestmentView.as_view()),
    path("debt", DebtView.as_view()),
    path("tax",TaxView.as_view()),
    path("relief", ReliefView.as_view())
]