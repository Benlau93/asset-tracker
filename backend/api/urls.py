from django.urls import path
from .views import InvestmentAPIViews, ExtractionViews

urlpatterns = [
    path("investment", InvestmentAPIViews.as_view()),
    path("extract", ExtractionViews.as_view())
]