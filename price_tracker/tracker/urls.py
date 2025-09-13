from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    # Home and authentication
    path('', views.home, name='home'),
    path('register/', views.register, name='register'),
    path('login/', auth_views.LoginView.as_view(template_name='tracker/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),

    # Password reset
    path('password-reset/', auth_views.PasswordResetView.as_view(template_name='tracker/password_reset.html'), name='password_reset'),
    path('password-reset/done/', auth_views.PasswordResetDoneView.as_view(template_name='tracker/password_reset_done.html'), name='password_reset_done'),
    path('password-reset-confirm/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='tracker/password_reset_confirm.html'), name='password_reset_confirm'),
    path('password-reset-complete/', auth_views.PasswordResetCompleteView.as_view(template_name='tracker/password_reset_complete.html'), name='password_reset_complete'),
    
    # User dashboard and product tracking
    path('dashboard/', views.dashboard, name='dashboard'),
    path('product-history/', views.product_history, name='product-history'),
    path('track-product/', views.track_product, name='track-product'),
    path('track-category/', views.track_category, name='track-category'),
    path('untrack-product/<int:product_id>/', views.untrack_product, name='untrack-product'),
    path('check-price/<int:product_id>/', views.check_price, name='check-price'),
    
    # Category and offer pages
    path('top-categories/', views.top_categories, name='top-categories'),
    path('top-offers/', views.top_offers, name='top-offers'),
    path('browse-category/<str:category>/', views.browse_category, name='browse-category'),
    
    # Product details and history
    path('product-details/<int:product_id>/', views.product_details, name='product-details'),
]
