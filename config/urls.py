from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    # Browsable API login/logout
    path("api-auth/", include("rest_framework.urls")),
    path("api/", include("quiz.urls")),
]
