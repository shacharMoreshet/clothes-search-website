from django.urls import path
from . import views


urlpatterns = [
    path('predict/', views.get_image),
    path('register/', views.signup_view),
    path('favorites/add/', views.add_favorite_product, name='add_favorite_product'),
    path('favorites/get/', views.get_all_favorites_products, name='get_all_favorites_products'),
    path('favorites/delete/', views.delete_favorite_product, name='delete_favorite_product'),
    path('history/add/', views.add_history, name='add_history'),
    path('history/get/', views.get_history, name='get_history'),
    path('history/delete/', views.delete_history, name='delete_history'),
    path('edit/', views.edit_user_info, name='edit_user_info'),
    path('login/', views.login_view, name='login_view'),
    path('email/get/', views.get_email, name='get_email'),
    path('delete/user/', views.delete_user, name='delete_user')
]
