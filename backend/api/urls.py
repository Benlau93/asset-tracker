from django.urls import path
from .views import InvestmentAPIViews, PDFExtractionViews

urlpatterns = [
    path("investment", InvestmentAPIViews.as_view()),
    path("extract", PDFExtractionViews.as_view())
]