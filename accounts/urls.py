from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import (
    CreateUserView,
    VerifyEmailView,
    ResetPasswordView,
    RequestPasswordResetView,
    ChangePasswordView,
    UserDetailsView,
    LoginView,
    UpdateUserView,
    ChangePasswordView,
    UpdateUserPhotoView,
    get_image_url,
    SubscriptionViewSet,
    UserListView,
    UserSearchView,
    UserDetails,
)

# Créez un routeur
router = DefaultRouter()
router.register(r"abonnements", SubscriptionViewSet, basename="subscription")

urlpatterns = [
    path("users/<int:user_id>/", UserDetails.as_view(), name="user-details"),
    path("search/users/", UserSearchView.as_view(), name="user-search"),
    path("user-list/", UserListView.as_view(), name="user-list"),
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
        "reset-password/",
        ResetPasswordView.as_view(),
        name="reset_password",
    ),
    path(
        "request-password-reset/",
        RequestPasswordResetView.as_view(),
        name="request_password_reset",
    ),
    path("change-password/", ChangePasswordView.as_view(), name="change-password"),
    path("login/", LoginView.as_view(), name="login"),
    path("detail/", UserDetailsView.as_view(), name="user-details"),
    path("update/", UpdateUserView.as_view(), name="update-user"),
    path("update-photo/", UpdateUserPhotoView.as_view(), name="update-photo"),
    path("change-password/", ChangePasswordView.as_view(), name="change-password"),
    path("get_image_url/<int:id>/", get_image_url, name="get_image_url"),
    path("get_image_url/<int:id>/", get_image_url, name="get_image_url"),
]
# Ajoutez les URLs générées par le routeur pour les ViewSets
urlpatterns += router.urls
