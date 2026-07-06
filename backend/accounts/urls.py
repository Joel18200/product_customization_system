"""
URL configuration for the accounts app.
"""
from django.urls import path
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from .views import RegisterView, ProfileView, UserListView

urlpatterns = [
    path("register/", RegisterView.as_view(), name="auth-register"),
    path("login/", TokenObtainPairView.as_view(), name="auth-login"),
    path("refresh/", TokenRefreshView.as_view(), name="auth-refresh"),
    path("profile/", ProfileView.as_view(), name="auth-profile"),
    path("users/", UserListView.as_view(), name="user-list"),
]
