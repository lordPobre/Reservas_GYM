import json
import calendar
from django.shortcuts import render, redirect
from django.utils.dateformat import format
from datetime import date, timedelta, time, datetime
from django.http import JsonResponse
from collections import Counter
from django.contrib import messages
from django.conf import settings
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.template.loader import render_to_string
from weasyprint import HTML
from django.db.models.functions import TruncDate
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from .models import HorarioBloque, FichaAlumno, Reserva
from .forms import FichaAlumnoForm

@login_required
def home(request):
    hoy = timezone.localdate()
    bloques_hoy = HorarioBloque.objects.filter(dia=hoy).prefetch_related('reservas_bloque__alumno').order_by('inicio')
    entrenamientos = bloques_hoy.filter(tipo='ENTRENAMIENTO')
    nutricion = bloques_hoy.filter(tipo='NUTRICION')
    total_alumnos = FichaAlumno.objects.count()
    reservas_mes_raw = Reserva.objects.filter(
        bloque__dia__month=hoy.month,
        bloque__dia__year=hoy.year
    ).values_list('bloque__dia', flat=True)
    
    conteo_dict = Counter(reservas_mes_raw)
    fechas_ordenadas = sorted(conteo_dict.keys())
    
    fechas_grafico = [format(d, 'd-b') for d in fechas_ordenadas]
    totales_grafico = [conteo_dict[d] for d in fechas_ordenadas]
    formulario = FichaAlumnoForm()

    return render(request, 'admin_gym/home.html', {
        'hoy': hoy,
        'entrenamientos': entrenamientos,
        'nutricion': nutricion,
        'kinesiologia': bloques_hoy.filter(tipo='KINESIOLOGIA'),
        'total_alumnos': total_alumnos, 
        'nombre_mes': format(hoy, 'F').upper(), 
        'fechas_grafico': json.dumps(fechas_grafico),
        'totales_grafico': json.dumps(totales_grafico), 
        'form': formulario,
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

    alumno_id = request.GET.get('alumno_id')
    alumno_detalle = None
    if alumno_id:
        try:
            alumno_detalle = FichaAlumno.objects.get(id=alumno_id)
        except FichaAlumno.DoesNotExist:
            alumno_detalle = None

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
    form = FichaAlumnoForm()

    reservas_mes_raw = Reserva.objects.filter(
        bloque__dia__month=fecha_base.month,
        bloque__dia__year=fecha_base.year
    ).values_list('bloque__dia', flat=True)
    conteo_dict = Counter(reservas_mes_raw)
    fechas_ordenadas = sorted(conteo_dict.keys())
    fechas_grafico = [format(d, 'd-b') for d in fechas_ordenadas]
    totales_grafico = [conteo_dict[d] for d in fechas_ordenadas]

    return render(request, 'admin_gym/dashboard.html', {
        'bloques_semana': bloques_semana,
        'dias_semana': dias_semana,
        'lunes': lunes,
        'domingo': domingo,
        'times_slots': generar_slots_entrenamiento(),
        'alumnos_registrados': alumnos_registrados,
        'nombre_mes': format(fecha_base, 'F').capitalize(), 
        'semana_anterior': semana_anterior.strftime('%Y-%m-%d'),
        'semana_siguiente': semana_siguiente.strftime('%Y-%m-%d'),
        'total_alumnos': alumnos_registrados.count(),
        'form': form, 
        'alumno_detalle': alumno_detalle,
        'fechas_grafico': json.dumps(fechas_grafico), 
        'totales_grafico': json.dumps(totales_grafico), 
    })

@login_required
def dashboard_nutricion(request):
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
        tipo='NUTRICION'
    ).prefetch_related('reservas_bloque__alumno')
    
    dias_semana = [lunes + timedelta(days=i) for i in range(7)]

    alumnos_registrados = FichaAlumno.objects.filter(plan_nutricional=True).order_by('nombre_completo')
    
    todos_los_slots = generar_slots_nutricion()
    slots_manana = [slot for slot in todos_los_slots if slot.hour <= 12] 
    slots_tarde = [slot for slot in todos_los_slots if slot.hour >= 13] 

    return render(request, 'admin_gym/dashboard_nutricion.html', {
        'bloques_semana': bloques_semana,
        'dias_semana': dias_semana,
        'slots_manana': slots_manana, 
        'slots_tarde': slots_tarde,   
        'lunes': lunes,
        'domingo': domingo,
        'semana_anterior': semana_anterior.strftime('%Y-%m-%d'),
        'semana_siguiente': semana_siguiente.strftime('%Y-%m-%d'),
        'alumnos_registrados': alumnos_registrados, 
        'nombre_mes': format(fecha_base, 'F').upper(),
    })

@login_required
def dashboard_kinesiologia(request):
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
        tipo='KINESIOLOGIA'
    ).prefetch_related('reservas_bloque__alumno')
    
    dias_semana = [lunes + timedelta(days=i) for i in range(7)]
    alumnos_registrados = FichaAlumno.objects.filter(plan_kinesiologia=True).order_by('nombre_completo')
    
    todos_los_slots = generar_slots_kine()
    slots_manana = [slot for slot in todos_los_slots if slot.hour <= 12] 
    slots_tarde = [slot for slot in todos_los_slots if slot.hour >= 13] 

    return render(request, 'admin_gym/dashboard_kinesiologia.html', {
        'bloques_semana': bloques_semana,
        'dias_semana': dias_semana,
        'slots_manana': slots_manana, 
        'slots_tarde': slots_tarde,   
        'lunes': lunes,
        'domingo': domingo,
        'semana_anterior': semana_anterior.strftime('%Y-%m-%d'),
        'semana_siguiente': semana_siguiente.strftime('%Y-%m-%d'),
        'alumnos_registrados': alumnos_registrados,
        'nombre_mes': format(fecha_base, 'F').upper(),
    })

@login_required
def registrar_alumno(request):
    if request.method == 'POST':
        form = FichaAlumnoForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('calendario_semanal')
    return redirect('calendario_semanal')

def generar_slots_entrenamiento():
    slots = []
    t = time(6, 30)
    while t <= time(11, 0):
        slots.append(t)
        t = (datetime.combine(date.today(), t) + timedelta(minutes=30)).time()
        if t > time(11, 0) or t < time(6, 30): break

    t = time(16, 0)
    while t <= time(20, 30):
        slots.append(t)
        t = (datetime.combine(date.today(), t) + timedelta(minutes=30)).time()
        if t > time(20, 30): break
    return slots

def generar_slots_nutricion():
    slots = []
    t = time(10, 0)
    while t <= time(12, 0):
        slots.append(t)
        t = (datetime.combine(date.today(), t) + timedelta(minutes=30)).time()
        if t > time(12, 0) or t < time(10, 0): break

    t = time(13, 0)
    while t <= time(15, 30):
        slots.append(t)
        t = (datetime.combine(date.today(), t) + timedelta(minutes=30)).time()
        if t > time(15, 30): break
    return slots

def generar_slots_kine():
    slots = []
    t = time(6, 30)
    while t <= time(12, 0):
        slots.append(t)
        t = (datetime.combine(date.today(), t) + timedelta(minutes=30)).time()
        if t > time(12, 0) or t < time(6, 30): break

    t = time(13, 0)
    while t <= time(21, 30):
        slots.append(t)
        t = (datetime.combine(date.today(), t) + timedelta(minutes=30)).time()
        if t > time(21, 30): break
    return slots

@login_required
def agendar_reserva(request):
    if request.method == 'POST':
        bloque_id = request.POST.get('bloque_id')
        alumno_id = request.POST.get('alumno_id')
        dia_str = request.POST.get('dia')
        hora_str = request.POST.get('hora')
        redirect_to = request.POST.get('redirect_to', 'calendario_semanal')
        todo_el_mes = request.POST.get('todo_el_mes') == 'on'

        alumno = get_object_or_404(FichaAlumno, id=alumno_id)

        try:
            # 1. PARSEO SEGURO DE FECHA Y HORA
            if bloque_id and bloque_id != 'nuevo':
                bloque_base = get_object_or_404(HorarioBloque, id=bloque_id)
                fecha_base = bloque_base.dia
                hora_inicio_time = bloque_base.inicio
                tipo_bloque_base = bloque_base.tipo
                capacidad_base = bloque_base.capacidad_maxima
            else:
                fecha_base = datetime.strptime(dia_str, '%Y-%m-%d').date()
                hora_inicio_time = datetime.strptime(hora_str[:5], '%H:%M').time()

                if 'nutricion' in redirect_to:
                    tipo_bloque_base = 'NUTRICION'
                    capacidad_base = 1
                elif 'kinesiologica' in redirect_to:
                    tipo_bloque_base = 'KINESIOLOGIA'
                    capacidad_base = 1
                else:
                    tipo_bloque_base = 'ENTRENAMIENTO'
                    capacidad_base = 10

            hora_fin_dt = datetime.combine(date.today(), hora_inicio_time) + timedelta(minutes=30)
            hora_fin_time = hora_fin_dt.time()

            # 2. DEFINIR LAS FECHAS A PROCESAR (CORREGIDO)
            fechas_a_procesar = []
            hoy = timezone.localdate()

            if todo_el_mes:
                year = fecha_base.year
                month = fecha_base.month
                dia_semana_objetivo = fecha_base.weekday()
                num_days = calendar.monthrange(year, month)[1]

                for d in range(1, num_days + 1):
                    fecha_iter = date(year, month, d)
                    
                    # REGLA CLAVE: Agregamos si es en el futuro O si es exactamente el día que hizo clic (aunque sea lunes y hoy sea viernes)
                    if fecha_iter.weekday() == dia_semana_objetivo and (fecha_iter >= hoy or fecha_iter == fecha_base):
                        fechas_a_procesar.append(fecha_iter)
            else:
                fechas_a_procesar.append(fecha_base)

            # 3. CREAR RESERVAS EVITANDO CRASHEOS
            reservas_creadas = 0
            reservas_omitidas = 0
            limite_semanal = obtener_limite_clases(alumno)

            for fecha in fechas_a_procesar:
                bloque, _ = HorarioBloque.objects.get_or_create(
                    dia=fecha,
                    inicio=hora_inicio_time,
                    tipo=tipo_bloque_base,
                    defaults={
                        'capacidad_maxima': capacidad_base,
                        'fin': hora_fin_time
                    }
                )

                if Reserva.objects.filter(bloque=bloque, alumno=alumno).exists():
                    continue

                # Verificamos cupo de la sala
                if bloque.reservas_bloque.count() >= bloque.capacidad_maxima:
                    reservas_omitidas += 1
                    continue

                # Verificamos límite del plan del alumno
                if tipo_bloque_base == 'ENTRENAMIENTO':
                    lunes = fecha - timedelta(days=fecha.weekday())
                    domingo = lunes + timedelta(days=6)
                    reservas_esta_semana = Reserva.objects.filter(
                        alumno=alumno,
                        bloque__dia__range=[lunes, domingo],
                        bloque__tipo='ENTRENAMIENTO'
                    ).count()

                    if reservas_esta_semana >= limite_semanal:
                        reservas_omitidas += 1
                        continue

                Reserva.objects.create(bloque=bloque, alumno=alumno)
                reservas_creadas += 1

            # 4. FEEDBACK INMEDIATO
            if todo_el_mes:
                if reservas_creadas > 0:
                    messages.success(request, f"¡Éxito! Se agendaron {reservas_creadas} clases para {alumno.nombre_completo}.")
                if reservas_omitidas > 0:
                    messages.warning(request, f"Se omitieron {reservas_omitidas} clases en el mes (Sala llena o límite alcanzado).")
                if reservas_creadas == 0 and reservas_omitidas == 0:
                    messages.info(request, f"{alumno.nombre_completo} ya estaba agendado en todas esas fechas.")
            else:
                if reservas_creadas > 0:
                    messages.success(request, f"Cita de {alumno.nombre_completo} agendada.")
                else:
                    messages.error(request, "No se pudo agendar (El bloque está lleno o límite alcanzado).")

        except Exception as e:
            messages.error(request, f"Ocurrió un error al procesar la reserva: {str(e)}")

        return redirect(redirect_to)

    return redirect('home')

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
        redirect_to = request.POST.get('redirect_to', 'calendario_semanal')
        
        if dia_str and jornada:
            ano, mes, dia = map(int, dia_str.split('-'))
            fecha_obj = date(ano, mes, dia)

            if jornada == 'manana':
                current_time = time(6, 30)
                end_time = time(11, 30) 
            elif jornada == 'tarde':
                current_time = time(16, 0)
                end_time = time(21, 0) 
            else:
                return redirect('calendario_semanal')
                
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
            return redirect('dashboard_nutricion') 
        elif tipo == 'KINESIOLOGIA':
            return redirect('dashboard_kinesiologia') 
        else:
            return redirect(redirect_to)
            
    return redirect('calendario_semanal')

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
        dia__range=[lunes, domingo],
        tipo='ENTRENAMIENTO' 
    ).prefetch_related('reservas_bloque__alumno')

    alumnos_activos = FichaAlumno.objects.filter(activo=True)
    alumnos_habilitados = []
    
    for alumno in alumnos_activos:
        limite = obtener_limite_clases(alumno)

        reservas_semana_actual = Reserva.objects.filter(
            alumno=alumno,
            bloque__dia__range=[lunes, domingo],
            bloque__tipo='ENTRENAMIENTO'
        ).count()

        if reservas_semana_actual < limite:
            alumno.cupos_restantes = limite - reservas_semana_actual
            alumnos_habilitados.append(alumno)
    
    dias_semana = [lunes + timedelta(days=i) for i in range(7)]
    todos_los_slots = generar_slots_entrenamiento()
    slots_manana = [slot for slot in todos_los_slots if slot.hour < 14] 
    slots_tarde = [slot for slot in todos_los_slots if slot.hour >= 16]
    formulario = FichaAlumnoForm()

    return render(request, 'admin_gym/calendario_semanal.html', {
        'bloques_semana': bloques_semana,
        'dias_semana': dias_semana,
        'slots_manana': slots_manana, 
        'slots_tarde': slots_tarde,   
        'lunes': lunes,
        'domingo': domingo,
        'semana_anterior': semana_anterior.strftime('%Y-%m-%d'),
        'semana_siguiente': semana_siguiente.strftime('%Y-%m-%d'),
        'alumnos_registrados': alumnos_habilitados,
        'form': formulario, 
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
        'mes_actual': format(hoy, 'F Y').upper(), 
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


@login_required
def eliminar_bloque(request):
    if request.method == 'POST':
        bloque_id = request.POST.get('bloque_id')
        redirect_to = request.POST.get('redirect_to', 'calendario_semanal')
        
        if bloque_id:
            try:
                bloque = HorarioBloque.objects.get(id=bloque_id)
                bloque.delete() 
                
                messages.success(request, "Bloque individual eliminado exitosamente.")
            except HorarioBloque.DoesNotExist:
                messages.error(request, "El bloque no existe o ya fue eliminado.")
            
        return redirect(redirect_to)
    return redirect('calendario_semanal')

@login_required
def eliminar_reserva(request, reserva_id):
    if request.method == 'POST':
        redirect_to = request.POST.get('redirect_to', 'calendario_semanal')
        try:
            reserva = Reserva.objects.get(id=reserva_id)
            nombre_alumno = reserva.alumno.nombre_completo
            reserva.delete()
            messages.success(request, f"Reserva de {nombre_alumno} eliminada.")
        except Reserva.DoesNotExist:
            messages.error(request, "La reserva no existe.")
            
        return redirect(redirect_to)
    return redirect('calendario_semanal')

@login_required
def toggle_estado_alumno(request, pk):
    if request.method == 'POST':
        alumno = get_object_or_404(FichaAlumno, pk=pk)
        alumno.activo = not alumno.activo  # Invierte el estado actual
        alumno.save()
        
        estado = "habilitado" if alumno.activo else "deshabilitado"
        messages.success(request, f"El alumno {alumno.nombre_completo} ha sido {estado}.")
        
    return redirect('lista_alumnos')

def obtener_limite_clases(alumno):
    if not alumno.plan: 
        return 0
    
    plan_texto = alumno.get_plan_display().lower()
    
    if '1 vez' in plan_texto: return 1
    if '2 veces' in plan_texto: return 2
    if '3 veces' in plan_texto: return 3
    if '4 veces' in plan_texto: return 4
    if '5 veces' in plan_texto: return 5
    if '6 veces' in plan_texto: return 6
    if 'libre' in plan_texto or 'ilimitado' in plan_texto: return 99
    
    return 0

@login_required
def eliminar_alumno(request, pk):
    if request.method == 'POST':
        alumno = get_object_or_404(FichaAlumno, pk=pk)
        nombre = alumno.nombre_completo
        alumno.delete()
        messages.success(request, f"La ficha de {nombre} fue eliminada permanentemente.")
    return redirect('lista_alumnos')