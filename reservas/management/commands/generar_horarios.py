from django.core.management.base import BaseCommand
from reservas.models import HorarioBloque
from datetime import date, time, timedelta

class Command(BaseCommand):
    help = 'Genera bloques de horario de 30min según la maqueta'

    def add_arguments(self, parser):
        parser.add_argument('fecha', type=str, help='Fecha en formato YYYY-MM-DD')

    def handle(self, *args, **options):
        fecha_str = options['fecha']
        ano, mes, dia = map(int, fecha_str.split('-'))
        fecha_obj = date(ano, mes, dia)

        # Rango Mañana: 06:30 a 11:00 (bloques de 30min)
        hora_inicio_manana = 6
        minutos_inicio_manana = 30
        
        current_time = time(hora_inicio_manana, minutos_inicio_manana)
        end_time_manana = time(11, 0) # El último bloque empieza a las 11:00

        while current_time < end_time_manana:
            inicio = current_time
            # Calculamos el fin añadiendo 30min
            total_minutes = (current_time.hour * 60) + current_time.minute + 30
            fin = time(total_minutes // 60, total_minutes % 60)

            if not HorarioBloque.objects.filter(dia=fecha_obj, inicio=inicio).exists():
                HorarioBloque.objects.create(
                    dia=fecha_obj,
                    inicio=inicio,
                    fin=fin,
                    capacidad_maxima=10  # Ajustado a "8 a 10 por Bloque"
                )
            current_time = fin

        # Rango Tarde: 17:00 a 20:30
        current_time = time(17, 0)
        end_time_tarde = time(20, 30)

        while current_time < end_time_tarde:
            inicio = current_time
            total_minutes = (current_time.hour * 60) + current_time.minute + 30
            fin = time(total_minutes // 60, total_minutes % 60)

            if not HorarioBloque.objects.filter(dia=fecha_obj, inicio=inicio).exists():
                HorarioBloque.objects.create(
                    dia=fecha_obj,
                    inicio=inicio,
                    fin=fin,
                    capacidad_maxima=10
                )
            current_time = fin

        self.stdout.write(self.style.SUCCESS(f'Horarios generados según la maqueta para el {fecha_str}'))