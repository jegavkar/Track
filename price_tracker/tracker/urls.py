from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    # Home and authentication
    path('', views.home, name='home'),
    path('register/', views.register, name='register'),
    path('login/', auth_views.LoginView.as_view(template_name='tracker/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    
    # User dashboard and product tracking
    path('dashboard/', views.dashboard, name='dashboard'),
    path('track-product/', views.track_product, name='track-product'),
    path('untrack-product/<int:product_id>/', views.untrack_product, name='untrack-product'),
    path('check-price/<int:product_id>/', views.check_price, name='check-price'),
    
    # Category and offer pages
    path('top-categories/', views.top_categories, name='top-categories'),
    path('top-offers/', views.top_offers, name='top-offers'),
    
    # Product details and history
    path('product-details/<int:product_id>/', views.product_details, name='product-details'),
]
