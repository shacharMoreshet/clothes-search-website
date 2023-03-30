from django.urls import path
from . import views

# http://127.0.0.1:8000/predict/?image_url=https://images.asos-media.com/products/asos-design-crochet-shirt-dress-in-black/202934994-2?$n_480w$&wid=476&fit=constrain - the url to get prediction of the img

urlpatterns = [
    path('predict/', views.get_image),
]
