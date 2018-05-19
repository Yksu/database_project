from django.contrib import admin
from django.urls import include, path


app_name = 'online_library'
urlpatterns = [
    path('', include('library.urls')),
    path('admin/', admin.site.urls),
]
