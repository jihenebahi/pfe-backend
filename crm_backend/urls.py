from django.contrib import admin
from django.urls import path , include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/',include('accounts.urls')),
<<<<<<< HEAD
    path('api/categories/', include('categories.urls')),
=======
    path('api/formations/', include('formation.urls')),
>>>>>>> f859b66cd2ba0b53cc2ca3685a77dd53a3d575fe
]
