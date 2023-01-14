from django.urls import path
from . import views

# http://127.0.0.1:8000/predict/?image_url= - the url to get prediction of the img

urlpatterns = [
    path('predict/', views.get_image),
]
