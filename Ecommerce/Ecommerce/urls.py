from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('admin/', admin.site.urls),
    # allauth under /oauth/ so /accounts/login/ stays our email/password + OTP UI
    path('oauth/', include('allauth.urls')),
    path('', include('accounts.urls')),
    path('', include('store.urls')),
    path('api/v1/', include('store.api.urls')),
    path('api/v1/auth/', include('accounts.api_urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
