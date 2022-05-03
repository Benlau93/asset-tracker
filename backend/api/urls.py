from django.urls import path
from .views import ExtractInvestmentViews, PDFExtractionViews

urlpatterns = [
    path("extract-investment", ExtractInvestmentViews.as_view()),
    path("extract", PDFExtractionViews.as_view())
]