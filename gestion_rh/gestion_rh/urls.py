from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('rh.urls')),         # backend : API REST
    path('', include('frontend.urls')),       # frontend : pages Bootstrap
]
