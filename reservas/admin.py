from django.contrib import admin
from .models import HorarioBloque, Reserva, FichaAlumno

@admin.register(HorarioBloque)
class HorarioBloqueAdmin(admin.ModelAdmin):
    list_display = ('dia', 'inicio', 'fin', 'capacidad_actual', 'capacidad_maxima')
    list_filter = ('dia',)
    
    def capacidad_actual(self, obj):
        return obj.reservas_bloque.count()
    capacidad_actual.short_description = "Inscritos"

@admin.register(Reserva)
class ReservaAdmin(admin.ModelAdmin):
    list_display = ('alumno', 'bloque', 'fecha_creacion')
    search_fields = ('alumno__nombre_completo', 'bloque__dia')

@admin.register(FichaAlumno)
class FichaAlumnoAdmin(admin.ModelAdmin):
    list_display = ('nombre_completo', 'telefono', 'obtener_edad', 'fecha_registro')
    search_fields = ('nombre_completo', 'telefono', 'correo')
    fieldsets = (
        ('1. Datos Personales', {
            'fields': ('usuario', 'nombre_completo', 'objetivo', 'telefono', 'correo', 'fecha_nacimiento', 'estatura', 'peso', 'ocupacion')
        }),
        ('2. Datos Entrenamiento', {
            'fields': ('dias_semanales', 'horario_preferente', 'experiencia', 'deporte_previo')
        }),
        ('3. Nutrición y Salud (General)', {
            'fields': ('comida_favorita', 'intolerancias', 'alimentos_diarios', 'medicacion', 'drogas', 'lesiones', 'enfermedades_familiares', 'hora_despertar', 'hora_dormir', 'suplementos')
        }),
        ('Recordatorio 24 Horas', {
            'fields': ('dieta_tiempo', 'comida_desayuno', 'comida_snack1', 'comida_almuerzo', 'comida_once', 'comida_cena')
        }),
        ('Extra', {
            'fields': ('comentario_adicional',)
        }),
    )

    def obtener_edad(self, obj):
        return obj.edad
    obtener_edad.short_description = 'Edad'