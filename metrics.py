"""
Módulo de cálculo de métricas para el Dashboard de Créditos.

Lógica de Negocio:
-----------------
Estados base:
- RECHAZADA: Consulta no calificada.
- INCOMPLETA: Tuvo oferta pero no avanzó/incompleta.
- EN_ANALISIS: Aprobado, pendiente de subir remito/factura.
- APROBADA: Aprobado, listo para liquidar.
- LIQUIDADA: Crédito liquidado y desembolsado.

Agrupaciones:
- Total Consultas = Rechazadas + Incompletas + En Análisis + Aprobadas + Liquidadas
- Total con Oferta = Incompletas + En Análisis + Aprobadas + Liquidadas
- Venta Total (Pipeline Comercial) = En Análisis + Aprobadas + Liquidadas
- Total Liquidado (Cierre Efectivo) = Liquidadas

Totales económicos:
- Venta Total $ = Monto En Análisis + Monto Aprobadas + Monto Liquidadas
- Total Liquidado $ = Monto Liquidadas

KPIs calculados:
- % Aprobación (Tasa de Oferta) = (Total con Oferta / Total Consultas) * 100
- % Conversión Bruta (Efectiva) = (Liquidadas / Total Consultas) * 100
- % Conversión Bruta (Total Ventas) = (Venta Total / Total Consultas) * 100
- % Conversión sobre Oferta = (Venta Total / Total con Oferta) * 100
- % Liquidación sobre Oferta = (Liquidadas / Total con Oferta) * 100
"""

from typing import Dict, Any, List, Union


def normalizar_estado(estado: str) -> str:
    """Normaliza el nombre del estado para evitar inconsistencias de tildes o mayúsculas."""
    if not estado:
        return "DESCONOCIDO"
    e = str(estado).strip().upper()
    if "RECHAZ" in e:
        return "RECHAZADA"
    if "INCOMPL" in e:
        return "INCOMPLETA"
    if "ANALIS" in e or "ANÁLIS" in e:
        return "EN_ANALISIS"
    if "APROB" in e:
        return "APROBADA"
    if "LIQUID" in e:
        return "LIQUIDADA"
    return e


def calcular_metricas(registros: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Calcula los conteos, totales y métricas porcentuales para una lista de registros.
    Cada registro es un dict con claves como 'estado', 'monto' (opcional), etc.
    """
    total_consultas = len(registros)
    if total_consultas == 0:
        return {
            "total_consultas": 0,
            "rechazadas": 0,
            "incompletas": 0,
            "en_analisis": 0,
            "aprobadas": 0,
            "liquidadas": 0,
            "total_con_oferta": 0,
            "venta_total_cant": 0,
            "total_liquidado_cant": 0,
            "monto_rechazadas": 0.0,
            "monto_incompletas": 0.0,
            "monto_en_analisis": 0.0,
            "monto_aprobadas": 0.0,
            "monto_liquidadas": 0.0,
            "monto_total_con_oferta": 0.0,
            "monto_venta_total": 0.0,
            "monto_liquidado": 0.0,
            "pct_aprobacion": 0.0,
            "pct_conversion_bruta": 0.0,
            "pct_conversion_bruta_total": 0.0,
            "pct_conversion_sobre_oferta": 0.0,
            "pct_liquidacion_sobre_oferta": 0.0,
        }

    conteos = {
        "RECHAZADA": 0,
        "INCOMPLETA": 0,
        "EN_ANALISIS": 0,
        "APROBADA": 0,
        "LIQUIDADA": 0,
        "OTRO": 0,
    }

    montos = {
        "RECHAZADA": 0.0,
        "INCOMPLETA": 0.0,
        "EN_ANALISIS": 0.0,
        "APROBADA": 0.0,
        "LIQUIDADA": 0.0,
        "OTRO": 0.0,
    }

    for reg in registros:
        st = normalizar_estado(reg.get("estado", ""))
        key = st if st in conteos else "OTRO"
        conteos[key] += 1
        
        monto_val = reg.get("monto", 0.0)
        try:
            monto_float = float(monto_val) if monto_val is not None else 0.0
        except (ValueError, TypeError):
            monto_float = 0.0
        montos[key] += monto_float

    rechazadas = conteos["RECHAZADA"]
    incompletas = conteos["INCOMPLETA"]
    en_analisis = conteos["EN_ANALISIS"]
    aprobadas = conteos["APROBADA"]
    liquidadas = conteos["LIQUIDADA"]

    # Agrupaciones clave solicitadas:
    # 1. Total con Oferta = Incompleta + En Análisis + Aprobada + Liquidada
    total_con_oferta = incompletas + en_analisis + aprobadas + liquidadas
    
    # 2. Venta Total (Pipeline comercial) = En Análisis + Aprobada + Liquidada
    venta_total_cant = en_analisis + aprobadas + liquidadas
    
    # 3. Total Liquidado = Liquidada
    total_liquidado_cant = liquidadas

    # Montos agrupados:
    monto_total_con_oferta = montos["INCOMPLETA"] + montos["EN_ANALISIS"] + montos["APROBADA"] + montos["LIQUIDADA"]
    monto_venta_total = montos["EN_ANALISIS"] + montos["APROBADA"] + montos["LIQUIDADA"]
    monto_liquidado = montos["LIQUIDADA"]

    # Porcentajes y Ratios:
    pct_aprobacion = (total_con_oferta / total_consultas * 100) if total_consultas > 0 else 0.0
    pct_conversion_bruta = (liquidadas / total_consultas * 100) if total_consultas > 0 else 0.0
    pct_conversion_bruta_total = (venta_total_cant / total_consultas * 100) if total_consultas > 0 else 0.0
    pct_conversion_sobre_oferta = (venta_total_cant / total_con_oferta * 100) if total_con_oferta > 0 else 0.0
    pct_liquidacion_sobre_oferta = (liquidadas / total_con_oferta * 100) if total_con_oferta > 0 else 0.0

    return {
        "total_consultas": total_consultas,
        "rechazadas": rechazadas,
        "incompletas": incompletas,
        "en_analisis": en_analisis,
        "aprobadas": aprobadas,
        "liquidadas": liquidadas,
        "total_con_oferta": total_con_oferta,
        "venta_total_cant": venta_total_cant,
        "total_liquidado_cant": total_liquidado_cant,
        # Montos
        "monto_rechazadas": round(montos["RECHAZADA"], 2),
        "monto_incompletas": round(montos["INCOMPLETA"], 2),
        "monto_en_analisis": round(montos["EN_ANALISIS"], 2),
        "monto_aprobadas": round(montos["APROBADA"], 2),
        "monto_liquidadas": round(montos["LIQUIDADA"], 2),
        "monto_total_con_oferta": round(monto_total_con_oferta, 2),
        "monto_venta_total": round(monto_venta_total, 2),
        "monto_liquidado": round(monto_liquidado, 2),
        # Ratios
        "pct_aprobacion": round(pct_aprobacion, 2),
        "pct_conversion_bruta": round(pct_conversion_bruta, 2),
        "pct_conversion_bruta_total": round(pct_conversion_bruta_total, 2),
        "pct_conversion_sobre_oferta": round(pct_conversion_sobre_oferta, 2),
        "pct_liquidacion_sobre_oferta": round(pct_liquidacion_sobre_oferta, 2),
    }


def calcular_dias_laborables(
    fecha_inicio: Any,
    fecha_fin: Any,
    incluir_sabados: bool = True
) -> int:
    """
    Calcula los días laborables entre fecha_inicio y fecha_fin (ambas inclusive).
    incluir_sabados: True para comercios que abren de Lunes a Sábado.
    """
    import datetime
    
    if isinstance(fecha_inicio, str):
        fecha_inicio = datetime.date.fromisoformat(fecha_inicio)
    if isinstance(fecha_fin, str):
        fecha_fin = datetime.date.fromisoformat(fecha_fin)
        
    if fecha_inicio > fecha_fin:
        return 0

    limite_dia = 5 if incluir_sabados else 4  # 0=Lunes, 4=Viernes, 5=Sábado
    
    dias = 0
    actual = fecha_inicio
    un_dia = datetime.timedelta(days=1)
    while actual <= fecha_fin:
        if actual.weekday() <= limite_dia:
            dias += 1
        actual += un_dia
    return dias


def calcular_proyeccion(
    monto_acumulado: float,
    cant_acumulada: int,
    dias_trabajados: int,
    dias_restantes: int
) -> Dict[str, Any]:
    """
    Calcula la proyección (Run-Rate) a fin de mes/período.
    
    Fórmula:
    Promedio Diario = Acumulado / Días Trabajados
    Proyección Restante = Promedio Diario * Días Restantes
    Total Proyectado = Acumulado + Proyección Restante
    """
    if dias_trabajados <= 0:
        return {
            "dias_trabajados": dias_trabajados,
            "dias_restantes": dias_restantes,
            "dias_totales": dias_trabajados + dias_restantes,
            "promedio_diario_monto": 0.0,
            "promedio_diario_cant": 0.0,
            "proyectado_monto_restante": 0.0,
            "proyectado_cant_restante": 0,
            "proyeccion_total_monto": round(monto_acumulado, 2),
            "proyeccion_total_cant": cant_acumulada,
        }

    prom_monto = monto_acumulado / dias_trabajados
    prom_cant = cant_acumulada / dias_trabajados

    proy_monto_restante = prom_monto * dias_restantes
    proy_cant_restante = round(prom_cant * dias_restantes)

    proy_total_monto = monto_acumulado + proy_monto_restante
    proy_total_cant = cant_acumulada + proy_cant_restante

    return {
        "dias_trabajados": dias_trabajados,
        "dias_restantes": dias_restantes,
        "dias_totales": dias_trabajados + dias_restantes,
        "promedio_diario_monto": round(prom_monto, 2),
        "promedio_diario_cant": round(prom_cant, 2),
        "proyectado_monto_restante": round(proy_monto_restante, 2),
        "proyectado_cant_restante": proy_cant_restante,
        "proyeccion_total_monto": round(proy_total_monto, 2),
        "proyeccion_total_cant": proy_total_cant,
    }

