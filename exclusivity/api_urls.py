from django.urls import path, include

urlpatterns = [
    path("utilisateurs/", include("accounts.urls")),
    path("postes/", include("posts.urls")),
    path("paiements/", include("payments.urls")),
]
