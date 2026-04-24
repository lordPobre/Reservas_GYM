from django.db import models
from datetime import date
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

class HorarioBloque(models.Model):
    TIPO_CHOICES = [
        ('ENTRENAMIENTO', 'Entrenamiento'),
        ('NUTRICION', 'Nutrición'),
    ]
    dia = models.DateField(verbose_name="Día")
    inicio = models.TimeField(verbose_name="Hora de Inicio")
    fin = models.TimeField(verbose_name="Hora de Fin")
    capacidad_maxima = models.PositiveIntegerField(default=20, verbose_name="Capacidad Máxima")
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, default='ENTRENAMIENTO')

    class Meta:
        verbose_name = "Bloque de Horario"
        verbose_name_plural = "Bloques de Horario"
        ordering = ['dia', 'inicio']

    def __str__(self):
        return f"{self.dia} | {self.inicio.strftime('%H:%M')} - {self.fin.strftime('%H:%M')}"

class FichaAlumno(models.Model):
    PLANES_CHOICES = [
        ('4_CLASES', '4 Clases ($30.000) - 1 vez x semana'),
        ('8_CLASES', '8 Clases ($40.000) - 2 veces x semana'),
        ('12_CLASES', '12 Clases ($50.000) - 3 veces x semana'),
        ('16_CLASES', '16 Clases ($55.000) - 4 veces x semana'),
        ('FULL_20', 'FULL 20 ($60.000) - 5 veces x semana'),
        ('PASE_DIARIO', 'Pase Diario ($8.000)'),
        ('SOLO_CLINICA', 'Solo Servicios Clínicos (Sin Gym)'), # NUEVO
    ]

    usuario = models.OneToOneField(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='ficha')
    fecha_registro = models.DateField(auto_now_add=True)
    nombre_completo = models.CharField(max_length=200)
    plan = models.CharField(
        max_length=20, 
        choices=PLANES_CHOICES, 
        default='4_CLASES'
    )
    plan_nutricional = models.BooleanField('Habilitar Nutrición', default=False)
    plan_kinesiologia = models.BooleanField('Habilitar Kinesiología', default=False)
    fecha_nacimiento = models.DateField(null=True, blank=True)
    objetivo = models.TextField(verbose_name="Objetivo entrenamiento", help_text="disminuir peso corporal, disminuir grasa, aumentar masa muscular etc")
    telefono = models.CharField(max_length=20, verbose_name="Contacto telefónico/whatsapp")
    correo = models.EmailField(blank=True, null=True, verbose_name="Correo electrónico")
    fecha_nacimiento = models.DateField()
    estatura = models.PositiveIntegerField(verbose_name="Estatura (Cms.)")
    peso = models.DecimalField(max_digits=5, decimal_places=2, verbose_name="Peso (Kgs.)")
    ocupacion = models.CharField(max_length=200, verbose_name="Ocupación o trabajo")
    dias_semanales = models.CharField(max_length=50, verbose_name="Días de entrenamiento semanal (cantidad)")
    horario_preferente = models.CharField(max_length=100, verbose_name="Horario del día en que entrena preferentemente")
    experiencia = models.CharField(max_length=200, verbose_name="Experiencia en entrenamiento (hace cuanto entrena)")
    deporte_previo = models.CharField(max_length=200, verbose_name="Deporte que practica o alguna vez practicó", blank=True)
    comida_favorita = models.CharField(max_length=255, verbose_name="Comida favorita (o preferencia, dulce, salado etc)", blank=True)
    intolerancias = models.TextField(verbose_name="Comida que le haga mal o que no puede comer", blank=True)
    alimentos_diarios = models.TextField(verbose_name="¿Qué alimentos le acomoda ingerir diariamente?", blank=True)
    medicacion = models.CharField(max_length=255, verbose_name="¿Consume algún tipo de medicación? ¿Cual?", blank=True)
    drogas = models.CharField(max_length=255, verbose_name="¿Consume algún tipo de droga habitual o socialmente?", blank=True)
    dieta_tiempo = models.CharField(max_length=200, verbose_name="¿Hace cuánto se alimenta de esta forma?", blank=True)
    comida_desayuno = models.TextField(verbose_name="Desayuno", blank=True)
    comida_snack1 = models.TextField(verbose_name="Snack o colación", blank=True)
    comida_almuerzo = models.TextField(verbose_name="Almuerzo", blank=True)
    comida_once = models.TextField(verbose_name="Once o colación", blank=True)
    comida_cena = models.TextField(verbose_name="Cena o ultima comida del dia", blank=True)
    lesiones = models.TextField(verbose_name="Lesiones, problemas, operación/tratamiento médico", blank=True)
    enfermedades_familiares = models.TextField(verbose_name="Enfermedades/patologías familiares", blank=True)
    hora_despertar = models.TimeField(verbose_name="¿A qué hora usted generalmente se despierta o levanta?", null=True, blank=True)
    hora_dormir = models.TimeField(verbose_name="¿a qué hora usted generalmente se duerme o acuesta?", null=True, blank=True)
    suplementos = models.TextField(verbose_name="Suplementos que ha consumido, tiempo y administración", blank=True)
    comentario_adicional = models.TextField(verbose_name="Comentario adicional", blank=True)
    activo = models.BooleanField(default=True)
    

    class Meta:
        verbose_name = "Ficha de Alumno"
        verbose_name_plural = "Fichas de Alumnos"

    def __str__(self):
        return f"{self.nombre_completo} - {self.telefono}"

    @property
    def edad(self):
        hoy = date.today()
        return hoy.year - self.fecha_nacimiento.year - ((hoy.month, hoy.day) < (self.fecha_nacimiento.month, self.fecha_nacimiento.day))

class Reserva(models.Model):
    alumno = models.ForeignKey(FichaAlumno, on_delete=models.CASCADE, related_name="reservas")
    bloque = models.ForeignKey(HorarioBloque, on_delete=models.CASCADE, related_name="reservas_bloque")
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Reserva"
        verbose_name_plural = "Reservas"
        unique_together = ('alumno', 'bloque') 

    def clean(self):
        if not self.pk: 
            reservas_actuales = Reserva.objects.filter(bloque=self.bloque).count()
            if reservas_actuales >= self.bloque.capacidad_maxima:
                raise ValidationError("Este bloque de horario ya ha alcanzado su capacidad máxima.")

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Reserva de {self.alumno.nombre_completo} - {self.bloque}"

