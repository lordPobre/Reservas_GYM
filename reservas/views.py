import json
from django.shortcuts import render, redirect
from django.utils.dateformat import format
from .models import HorarioBloque, FichaAlumno, Reserva
from .forms import FichaAlumnoForm
from datetime import date, timedelta, time, datetime
from django.http import JsonResponse
from collections import Counter
from django.conf import settings
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.template.loader import render_to_string
from weasyprint import HTML
from django.db.models.functions import TruncDate
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone

@login_required
def home(request):
    hoy = timezone.localdate()
    bloques_hoy = HorarioBloque.objects.filter(dia=hoy).prefetch_related('reservas_bloque__alumno').order_by('inicio')
    entrenamientos = bloques_hoy.filter(tipo='ENTRENAMIENTO')
    nutricion = bloques_hoy.filter(tipo='NUTRICION')

    return render(request, 'admin_gym/home.html', {
        'hoy': hoy,
        'entrenamientos': entrenamientos,
        'nutricion': nutricion,
    })

@login_required
def dashboard_admin(request):
    fecha_str = request.GET.get('fecha')
    if fecha_str:
        try:
            fecha_base = datetime.strptime(fecha_str, '%Y-%m-%d').date()
        except ValueError:
            fecha_base = timezone.localdate()
    else:
        fecha_base = timezone.localdate()

    lunes = fecha_base - timedelta(days=fecha_base.weekday())
    domingo = lunes + timedelta(days=6)
    semana_anterior = lunes - timedelta(days=7)
    semana_siguiente = lunes + timedelta(days=7)
    bloques_semana = HorarioBloque.objects.filter(
        dia__range=[lunes, domingo], 
        tipo='ENTRENAMIENTO'
    ).prefetch_related('reservas_bloque')
    
    dias_semana = [lunes + timedelta(days=i) for i in range(7)]
    alumnos_registrados = FichaAlumno.objects.all().order_by('nombre_completo')

    return render(request, 'admin_gym/dashboard.html', {
        'bloques_semana': bloques_semana,
        'dias_semana': dias_semana,
        'lunes': lunes,
        'domingo': domingo,
        'times_slots': generar_slots_tiempo(),
        'alumnos_registrados': alumnos_registrados,
        'nombre_mes': format(fecha_base, 'F').capitalize(), 
        'semana_anterior': semana_anterior.strftime('%Y-%m-%d'),
        'semana_siguiente': semana_siguiente.strftime('%Y-%m-%d'),
        'total_alumnos': alumnos_registrados.count(),
    })

@login_required
def dashboard_nutricion(request):
    hoy = timezone.localdate()
    lunes = hoy - timedelta(days=hoy.weekday())
    domingo = lunes + timedelta(days=6)
    bloques_semana = HorarioBloque.objects.filter(
        dia__range=[lunes, domingo], 
        tipo='NUTRICION'
    ).prefetch_related('reservas_bloque')
    
    dias_semana = [lunes + timedelta(days=i) for i in range(7)]
    alumnos_registrados = FichaAlumno.objects.all().order_by('nombre_completo')

    return render(request, 'admin_gym/dashboard_nutricion.html', {
        'bloques_semana': bloques_semana,
        'dias_semana': dias_semana,
        'lunes': lunes,
        'domingo': domingo,
        'times_slots': generar_slots_tiempo(),
        'alumnos_registrados': alumnos_registrados,
        'nombre_mes': format(hoy, 'F').capitalize(),
    })

@login_required
def registrar_alumno(request):
    if request.method == 'POST':
        form = FichaAlumnoForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('dashboard_admin')
    return redirect('dashboard_admin')

def generar_slots_tiempo():
    slots = []
    t = time(6, 30)
    while t < time(11, 0):
        slots.append(t)
        total_min = (t.hour * 60) + t.minute + 30
        t = time(total_min // 60, total_min % 60)
    # Tarde
    t = time(17, 0)
    while t < time(20, 30):
        slots.append(t)
        total_min = (t.hour * 60) + t.minute + 30
        t = time(total_min // 60, total_min % 60)
    return slots

@login_required
def agendar_reserva(request):
    if request.method == 'POST':
        bloque_id = request.POST.get('bloque_id')
        alumno_id = request.POST.get('alumno_id')
        
        if bloque_id and alumno_id:
            try:
                bloque = HorarioBloque.objects.get(id=bloque_id)
                alumno = FichaAlumno.objects.get(id=alumno_id)
                Reserva.objects.create(alumno=alumno, bloque=bloque)
            except Exception as e:
                pass
                
    return redirect('dashboard_admin')

@login_required
def lista_alumnos(request):
    alumnos = FichaAlumno.objects.all().order_by('nombre_completo')
    form = FichaAlumnoForm()
    return render(request, 'admin_gym/lista_alumnos.html', {
        'alumnos': alumnos,
        'form': form
    })

@login_required
def obtener_bloques_disponibles(request):
    fecha_str = request.GET.get('fecha')
    if fecha_str:
        bloques = HorarioBloque.objects.filter(dia=fecha_str).order_by('inicio')
        data = []
        for b in bloques:
            ocupacion = b.reservas_bloque.count()
            if ocupacion < b.capacidad_maxima:
                data.append({
                    'id': b.id,
                    'texto': f"{b.inicio.strftime('%H:%M')} ({b.capacidad_maxima - ocupacion} cupos libres)"
                })
        return JsonResponse({'bloques': data})
    return JsonResponse({'bloques': []})

@login_required
def detalle_alumno(request, pk):
    alumno = get_object_or_404(FichaAlumno, pk=pk)
    return render(request, 'admin_gym/detalle_alumno.html', {'alumno': alumno})

@login_required
def editar_alumno(request, pk):
    alumno = get_object_or_404(FichaAlumno, pk=pk)
    
    if request.method == 'POST':
        form = FichaAlumnoForm(request.POST, instance=alumno)
        if form.is_valid():
            form.save()
            return redirect('lista_alumnos')
    else:
        form = FichaAlumnoForm(instance=alumno)
        
    return render(request, 'admin_gym/editar_alumno.html', {'form': form, 'alumno': alumno})

@login_required
def crear_bloque_manual(request):
    if request.method == 'POST':
        dia_str = request.POST.get('dia')
        jornada = request.POST.get('jornada')
        capacidad = int(request.POST.get('capacidad', 10))
        tipo = request.POST.get('tipo', 'ENTRENAMIENTO') 
        
        if dia_str and jornada:
            ano, mes, dia = map(int, dia_str.split('-'))
            fecha_obj = date(ano, mes, dia)

            if jornada == 'manana':
                current_time = time(6, 30)
                end_time = time(11, 0)
            elif jornada == 'tarde':
                current_time = time(17, 0)
                end_time = time(20, 30)
            else:
                return redirect('dashboard_admin')
            while current_time < end_time:
                inicio = current_time
                total_minutes = (current_time.hour * 60) + current_time.minute + 30
                fin = time(total_minutes // 60, total_minutes % 60)

                if not HorarioBloque.objects.filter(dia=fecha_obj, inicio=inicio, tipo=tipo).exists():
                    HorarioBloque.objects.create(
                        dia=fecha_obj,
                        inicio=inicio,
                        fin=fin,
                        capacidad_maxima=capacidad,
                        tipo=tipo 
                    )
                current_time = fin

        if tipo == 'NUTRICION':
            return redirect('reserva_nutricional')
        else:
            return redirect('dashboard_admin')

    return redirect('dashboard_admin')

@login_required
def calendario_semanal(request):
    fecha_str = request.GET.get('fecha')
    
    if fecha_str:
        try:
            fecha_base = datetime.strptime(fecha_str, '%Y-%m-%d').date()
        except ValueError:
            fecha_base = timezone.localdate()
    else:
        fecha_base = timezone.localdate()

    lunes = fecha_base - timedelta(days=fecha_base.weekday())
    domingo = lunes + timedelta(days=6)
    
    semana_anterior = lunes - timedelta(days=7)
    semana_siguiente = lunes + timedelta(days=7)
    
    bloques_semana = HorarioBloque.objects.filter(
        dia__range=[lunes, domingo]
    ).prefetch_related('reservas_bloque__alumno')
    
    dias_semana = [lunes + timedelta(days=i) for i in range(7)]
    todos_los_slots = generar_slots_tiempo()
    slots_manana = [slot for slot in todos_los_slots if slot.hour < 14] 
    slots_tarde = [slot for slot in todos_los_slots if slot.hour >= 14] 
    
    return render(request, 'admin_gym/calendario_semanal.html', {
        'bloques_semana': bloques_semana,
        'dias_semana': dias_semana,
        'slots_manana': slots_manana, 
        'slots_tarde': slots_tarde,   
        'lunes': lunes,
        'domingo': domingo,
        'semana_anterior': semana_anterior.strftime('%Y-%m-%d'),
        'semana_siguiente': semana_siguiente.strftime('%Y-%m-%d'),
    })

@login_required
def detalle_bloque_json(request, bloque_id):
    bloque = get_object_or_404(HorarioBloque, id=bloque_id)
    reservas = Reserva.objects.filter(bloque=bloque).select_related('alumno')
    
    asistentes = [
        {'id': r.id, 'nombre': r.alumno.nombre_completo, 'telefono': r.alumno.telefono} 
        for r in reservas
    ]
    
    return JsonResponse({
        'capacidad_maxima': bloque.capacidad_maxima,
        'ocupacion': reservas.count(),
        'asistentes': asistentes
    })

@login_required
def reportes_admin(request):
    hoy = timezone.localdate()
    reservas_mes_raw = Reserva.objects.filter(
        bloque__dia__month=hoy.month,
        bloque__dia__year=hoy.year
    ).values_list('bloque__dia', flat=True)
    conteo_dict = Counter(reservas_mes_raw)
    fechas_ordenadas = sorted(conteo_dict.keys())
    fechas_grafico = [format(d, 'd-b') for d in fechas_ordenadas]
    totales_grafico = [conteo_dict[d] for d in fechas_ordenadas]
    datos_tabla = [{'fecha': d, 'total': conteo_dict[d]} for d in reversed(fechas_ordenadas)]
    total_reservas_mes = sum(totales_grafico)
    dias_con_reservas = len(fechas_ordenadas)
    promedio_diario = round(total_reservas_mes / dias_con_reservas, 1) if dias_con_reservas > 0 else 0

    return render(request, 'admin_gym/reportes.html', {
        'fechas_grafico': json.dumps(fechas_grafico),
        'totales_grafico': json.dumps(totales_grafico),
        'mes_actual': format(hoy, 'F Y').upper(), # Ej: ABRIL 2026
        'total_reservas_mes': total_reservas_mes,
        'promedio_diario': promedio_diario,
        'datos_tabla': datos_tabla,
    })

@login_required
def exportar_ficha_pdf(request, pk):
    alumno = get_object_or_404(FichaAlumno, pk=pk)
    html_string = render_to_string('admin_gym/ficha_pdf_template.html', {'alumno': alumno})
    html = HTML(string=html_string, base_url=request.build_absolute_uri())
    pdf = html.write_pdf()
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="Ficha_{alumno.nombre_completo}.pdf"'
    return response

@login_required
def radio_popup(request):
    return render(request, 'admin_gym/radio.html')