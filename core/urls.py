from django.contrib import admin
from django.views.generic import RedirectView
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    # Aquí le decimos a Django que todo lo que empiece con /gym/ lo maneje tu aplicación
    path('gym/', include('reservas.urls')), 
    path('', RedirectView.as_view(url='/gym/', permanent=True)),
]