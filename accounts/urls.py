from django.urls import path
from .views import (
    CreateUserView,
    VerifyEmailView,
    ResetPasswordView,
    RequestPasswordResetView,
    ChangePasswordView,
    UserDetailsView,
    LoginView,
)

urlpatterns = [
    path(
        "registering/",
        CreateUserView.as_view(),
        name="user_create",
    ),
    path(
        "verification-email/<int:user_id>/<str:token>/",
        VerifyEmailView.as_view(),
        name="verify_email",
    ),
    path(
        "reset-password/<str:uidb64>/<str:token>/",
        ResetPasswordView.as_view(),
        name="reset_password",
    ),
    path(
        "request-password-reset/",
        RequestPasswordResetView.as_view(),
        name="request_password_reset",
    ),
    path("change-password/", ChangePasswordView.as_view(), name="change-password"),
    path("détails/", UserDetailsView.as_view(), name="user-details"),
    path("login/", LoginView.as_view(), name="login"),
]
