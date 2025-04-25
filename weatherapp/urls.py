from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),          # Main page with city weather + suggestion
    path('results/', views.results, name='results'),  # Detailed weather page after form submission
]
