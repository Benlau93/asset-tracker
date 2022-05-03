from django.urls import path
from .views import ExtractInvestmentViews, PDFExtractionViews, CPFView, BankView, InvestmentView

urlpatterns = [
    path("extract-investment", ExtractInvestmentViews.as_view()),
    path("extract", PDFExtractionViews.as_view()),
    path("cpf",CPFView.as_view()),
    path("bank",BankView.as_view()),
    path("investment",InvestmentView.as_view())
]