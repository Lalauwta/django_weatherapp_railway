from django.urls import path
from . import views

#url patterns for the main app

urlpatterns = [
    path('', views.index, name='index'),
]