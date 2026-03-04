from django.contrib import admin
from django.urls import path , include

from django.conf import settings
from django.conf.urls.static import static  # ✅ Import manquant

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/',include('accounts.urls')),

    path('api/formations/', include('formation.urls')),
    
    path('api/categories/', include('categories.urls')),
    path('api/formateurs/', include('formateurs.urls')),


]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
