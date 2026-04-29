import json
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
    
    # --- Datos de bloques de hoy ---
    bloques_hoy = HorarioBloque.objects.filter(dia=hoy).prefetch_related('reservas_bloque__alumno').order_by('inicio')
    entrenamientos = bloques_hoy.filter(tipo='ENTRENAMIENTO')
    nutricion = bloques_hoy.filter(tipo='NUTRICION')

    # --- NUEVO: Conteo de alumnos ---
    total_alumnos = FichaAlumno.objects.count()

    # --- NUEVO: Datos para el gráfico mensual ---
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
        'total_alumnos': total_alumnos, # Variable para el conteo
        'nombre_mes': format(hoy, 'F').upper(), # Ej: ABRIL
        'fechas_grafico': json.dumps(fechas_grafico), # Datos para Chart.js
        'totales_grafico': json.dumps(totales_grafico), # Datos para Chart.js
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
        'times_slots': generar_slots_tiempo(),
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
    
    todos_los_slots = generar_slots_tiempo()
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
        'alumnos_registrados': alumnos_registrados, # Lista universal de alumnos
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
    
    todos_los_slots = generar_slots_tiempo()
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

def generar_slots_tiempo():
    slots = []
    # BLOQUE MAÑANA: 06:30 a 12:00
    t = time(6, 30)
    while t <= time(11, 0): # Termina a las 11:00
        slots.append(t)
        total_min = (t.hour * 60) + t.minute + 30
        if total_min > 1439: break 
        t = time(total_min // 60, total_min % 60)
        if t > time(11, 0): break

    # BLOQUE TARDE: 13:00 a 21:30
    t = time(16, 0) # Inicia a las 16:00
    while t <= time(20, 30): # Termina a las 20:30
        slots.append(t)
        total_min = (t.hour * 60) + t.minute + 30
        if total_min > 1439: break
        t = time(total_min // 60, total_min % 60)
        if t > time(20, 30): break
        
    return slots

@login_required
def agendar_reserva(request):
    if request.method == 'POST':
        bloque_id = request.POST.get('bloque_id')
        alumno_id = request.POST.get('alumno_id')
        dia_str = request.POST.get('dia')   
        hora_str = request.POST.get('hora') 
        redirect_to = request.POST.get('redirect_to', 'calendario_semanal')
        
        alumno = get_object_or_404(FichaAlumno, id=alumno_id)

        # --- LÓGICA DE BLOQUE AUTOMÁTICO ---
        if bloque_id == 'nuevo':
            if 'nutricion' in redirect_to:
                tipo_bloque = 'NUTRICION'
                capacidad = 1
            elif 'kinesiologica' in redirect_to:
                tipo_bloque = 'KINESIOLOGIA'
                capacidad = 1
            else:
                tipo_bloque = 'ENTRENAMIENTO'
                capacidad = 10
            
            # 1. Calculamos la hora de fin
            formato_hora = '%H:%M:%S' if len(hora_str) > 5 else '%H:%M'
            hora_inicio_dt = datetime.strptime(hora_str, formato_hora)
            hora_fin_dt = hora_inicio_dt + timedelta(minutes=30)
            hora_fin_str = hora_fin_dt.time()
            
            # 2. Convertimos el día (texto) a una Fecha real de Python
            dia_date = datetime.strptime(dia_str, '%Y-%m-%d').date()
            
            # 3. Creamos el bloque con la Fecha real (dia_date)
            bloque, created = HorarioBloque.objects.get_or_create(
                dia=dia_date,  # <--- SOLUCIÓN AL ERROR DEL WEEKDAY
                inicio=hora_str,
                tipo=tipo_bloque,
                defaults={
                    'capacidad_maxima': capacidad,
                    'fin': hora_fin_str
                }
            )
        else:
            bloque = get_object_or_404(HorarioBloque, id=bloque_id)
        
        # --- 1. VALIDACIÓN DE LÍMITE SEMANAL ---
        if bloque.tipo == 'ENTRENAMIENTO':
            # Seguro extra: Nos aseguramos de que sea una fecha real antes de calcular
            fecha_bloque = bloque.dia if not isinstance(bloque.dia, str) else datetime.strptime(bloque.dia, '%Y-%m-%d').date()
            
            lunes = fecha_bloque - timedelta(days=fecha_bloque.weekday())
            domingo = lunes + timedelta(days=6)
            
            reservas_semana = Reserva.objects.filter(
                alumno=alumno,
                bloque__dia__range=[lunes, domingo],
                bloque__tipo='ENTRENAMIENTO'
            ).count()
            
            limite = obtener_limite_clases(alumno)
            
            if reservas_semana >= limite:
                messages.error(request, f"Rechazado: {alumno.nombre_completo} alcanzó su límite de {limite} clases esta semana.")
                return redirect(redirect_to)

        # --- 2. VALIDACIÓN DE CUPOS DEL BLOQUE ---
        if bloque.reservas_bloque.count() >= bloque.capacidad_maxima:
            messages.error(request, "El bloque ya está lleno.")
            return redirect(redirect_to)
            
        # --- 3. CREACIÓN DE LA RESERVA ---
        Reserva.objects.get_or_create(bloque=bloque, alumno=alumno)
        messages.success(request, f"Cita de {alumno.nombre_completo} agendada correctamente.")
            
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
        
        if dia_str and jornada:
            ano, mes, dia = map(int, dia_str.split('-'))
            fecha_obj = date(ano, mes, dia)

            # --- NUEVOS RANGOS HORARIOS ---
            if jornada == 'manana':
                current_time = time(6, 30)
                end_time = time(11, 30) # Para incluir el bloque de las 11:00
            elif jornada == 'tarde':
                current_time = time(16, 0)
                end_time = time(21, 0) # Llega hasta las 22:00 para incluir el bloque de las 21:30
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
            return redirect('reserva_nutricional')
        elif tipo == 'KINESIOLOGIA':
            return redirect('reserva_kinesiologica') 
        else:
            return redirect('calendario_semanal')
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
    
    # --- LA MAGIA DEL FILTRO ---
    alumnos_activos = FichaAlumno.objects.filter(activo=True)
    alumnos_habilitados = []
    
    for alumno in alumnos_activos:
        limite = obtener_limite_clases(alumno)
        
        # Contamos cuántas veces ha reservado ENTRE ESTE LUNES Y DOMINGO
        reservas_semana_actual = Reserva.objects.filter(
            alumno=alumno,
            bloque__dia__range=[lunes, domingo],
            bloque__tipo='ENTRENAMIENTO'
        ).count()
        
        # Si aún le quedan clases, lo agregamos a la lista
        if reservas_semana_actual < limite:
            # Le agregamos una propiedad temporal para mostrar cuántas le quedan
            alumno.cupos_restantes = limite - reservas_semana_actual
            alumnos_habilitados.append(alumno)
    # ---------------------------
    
    dias_semana = [lunes + timedelta(days=i) for i in range(7)]
    todos_los_slots = generar_slots_tiempo()
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