from datetime import datetime

def calculate_stats(db):
    tarifa = 50.0
    vehiculos_hoy = 0
    ingresos_totales = 0.0
    promedio_por_hora = 0.0
    hora_pico = "Sin datos"
    max_hora_conteo = 0
    ultima_actualizacion = "Sin datos"
    tiempo_promedio_min = None

    # Obtener lista completa de automóviles para estadísticas
    all_automoviles = db.obtener_automoviles()
    
    # Calcular estadísticas basadas en todos los automóviles
    vehiculos_hoy = len(all_automoviles)
    ingresos_totales = sum(auto['saldo'] for auto in all_automoviles)

    # Promedio por hora (promedio de saldos)
    if all_automoviles:
        promedio_por_hora = ingresos_totales / len(all_automoviles)
    else:
        promedio_por_hora = 0.0

    # Calcular cambios porcentuales basados en datos actuales
    vehiculos_con_saldo = sum(1 for auto in all_automoviles if auto['saldo'] > 0)
    change_vehiculos = (vehiculos_con_saldo / vehiculos_hoy * 100) if vehiculos_hoy > 0 else 0.0

    # Porcentaje de ingresos respecto al saldo inicial posible (50 por vehículo)
    saldo_posible_total = vehiculos_hoy * 50
    change_ingresos = (ingresos_totales / saldo_posible_total * 100) if saldo_posible_total > 0 else 0.0

    # Para promedio: coeficiente de variación (desviación estándar / media * 100)
    if all_automoviles and promedio_por_hora > 0:
        saldos = [auto['saldo'] for auto in all_automoviles]
        mean = sum(saldos) / len(saldos)
        variance = sum((x - mean) ** 2 for x in saldos) / len(saldos)
        std_dev = variance ** 0.5
        change_promedio = (std_dev / mean * 100) if mean > 0 else 0.0
    else:
        change_promedio = 0.0

    # Obtener últimos 10 automóviles para la tabla (ordenados por ID descendente)
    automoviles = all_automoviles[-10:][::-1]  # Últimos 10, ordenados del más reciente al más antiguo
    
    # Derivar métricas visibles en la sección "Estadísticas de Tiempo"
    hora_pico = f"{vehiculos_con_saldo} vehículos"
    max_hora_conteo = vehiculos_con_saldo
    tiempo_promedio_min = promedio_por_hora

    # Datos para el gráfico: saldo por vehículo (últimos 10)
    labels = [auto['placa'] for auto in automoviles]
    data = [auto['saldo'] for auto in automoviles]

    ultima_actualizacion = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    ingresos_totales_str = f"${ingresos_totales:,.0f}"

    return {
        'vehiculos_hoy': vehiculos_hoy,
        'ingresos_totales_str': ingresos_totales_str,
        'promedio_por_hora': promedio_por_hora,
        'hora_pico': hora_pico,
        'max_hora_conteo': max_hora_conteo,
        'tiempo_promedio_min': tiempo_promedio_min,
        'ultima_actualizacion': ultima_actualizacion,
        'automoviles': automoviles,
        'change_vehiculos': change_vehiculos,
        'change_ingresos': change_ingresos,
        'change_promedio': change_promedio,
        'labels': labels,
        'data': data
    }