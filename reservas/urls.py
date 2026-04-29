from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('', views.home, name='home'), 
    path('radio/', views.radio_popup, name='radio_popup'),
    path('login/', auth_views.LoginView.as_view(template_name='admin_gym/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('dashboard/', views.dashboard_admin, name='dashboard_admin'),
    path('nutricion/', views.dashboard_nutricion, name='reserva_nutricional'),
    path('calendario-semanal/', views.calendario_semanal, name='calendario_semanal'),
    path('kinesiologia/', views.dashboard_kinesiologia, name='reserva_kinesiologica'),
    path('bloque/eliminar/', views.eliminar_bloque, name='eliminar_bloque'),
    path('reserva/eliminar/<int:reserva_id>/', views.eliminar_reserva, name='eliminar_reserva'),
    path('alumnos/', views.lista_alumnos, name='lista_alumnos'),
    path('alumnos/<int:pk>/', views.detalle_alumno, name='detalle_alumno'),
    path('alumnos/<int:pk>/editar/', views.editar_alumno, name='editar_alumno'),
    path('alumnos/<int:pk>/toggle/', views.toggle_estado_alumno, name='toggle_estado_alumno'),
    path('registrar-alumno/', views.registrar_alumno, name='registrar_alumno'),
    path('alumnos/<int:pk>/pdf/', views.exportar_ficha_pdf, name='exportar_ficha_pdf'),
    path('crear-bloque/', views.crear_bloque_manual, name='crear_bloque_manual'),
    path('bloque/<int:bloque_id>/detalle/', views.detalle_bloque_json, name='detalle_bloque_json'),
    path('agendar-reserva/', views.agendar_reserva, name='agendar_reserva'),
    path('obtener-bloques/', views.obtener_bloques_disponibles, name='obtener_bloques'),
    path('reportes/', views.reportes_admin, name='reportes_admin'),
]