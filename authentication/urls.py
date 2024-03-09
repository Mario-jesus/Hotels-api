from django.urls import path, include
from .views import LoginView, LogoutView, SignUpView

urlpatterns = [
    path("auth/login/", LoginView.as_view(), name="auth_login"),
    path("auth/logout/", LogoutView.as_view(), name="auth_logout"),
    path("auth/signup/", SignUpView.as_view(), name="auth_signup"),
    path("auth/reset/", include("django_rest_passwordreset.urls"), name="password_reset"),
]