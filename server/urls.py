from django.urls import path
from . import views

# http://127.0.0.1:8000/predict/?image_url=https://images.asos-media.com/products/asos-design-crochet-shirt-dress-in-black/202934994-2?$n_480w$&wid=476&fit=constrain - the url to get prediction of the img

urlpatterns = [
    path('predict/', views.get_image),
    path('register/', views.signup_view),
    path('favorites/add/', views.add_favorite_product, name='add_favorite_product'),
    path('favorites/get/', views.get_all_favorites_products, name='get_all_favorites_products'),
    path('favorites/delete/', views.delete_favorite_product, name='delete_favorite_product'),
]
