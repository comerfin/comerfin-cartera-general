"""
Módulo de Analítica Avanzada: Semáforos, Objetivos y Tendencias Históricas Mes a Mes.
"""

from typing import Dict, Any, List, Optional
import datetime


# Reglas de semáforo por defecto (configurables)
UMBRALES_DEFAULT = {
    "pct_conversion_bruta": {"rojo": 20.0, "amarillo": 35.0},      # <20% Rojo, 20-35% Amarillo, >=35% Verde
    "pct_aprobacion": {"rojo": 50.0, "amarillo": 65.0},            # <50% Rojo, 50-65% Amarillo, >=65% Verde
    "cumplimiento_objetivo": {"rojo": 70.0, "amarillo": 90.0},     # <70% Rojo, 70-90% Amarillo, >=90% Verde
}


def calcular_semaforo(valor: float, metrica: str = "pct_conversion_bruta", umbrales: Optional[Dict[str, float]] = None) -> Dict[str, str]:
    """
    Retorna el estado de semáforo: 'ROJO', 'AMARILLO' o 'VERDE' junto con un icono y color hexadecimal.
    """
    if umbrales is None:
        umbrales = UMBRALES_DEFAULT.get(metrica, {"rojo": 20.0, "amarillo": 35.0})
        
    rojo_max = umbrales.get("rojo", 20.0)
    amarillo_max = umbrales.get("amarillo", 35.0)

    if valor < rojo_max:
        return {"estado": "ROJO", "icono": "🔴", "color": "#FF4B4B", "mensaje": "Crítico / Requiere Acción"}
    elif valor < amarillo_max:
        return {"estado": "AMARILLO", "icono": "🟡", "color": "#FFAA00", "mensaje": "En Observación / Regular"}
    else:
        return {"estado": "VERDE", "icono": "🟢", "color": "#09AB3B", "mensaje": "Óptimo / Saludable"}


def evaluar_cumplimiento_objetivo(monto_proyectado: float, monto_objetivo: float) -> Dict[str, Any]:
    """
    Evalúa el cumplimiento del objetivo proyectado para un comercio.
    """
    if monto_objetivo <= 0:
        return {
            "monto_objetivo": 0.0,
            "monto_proyectado": round(monto_proyectado, 2),
            "pct_cumplimiento": 0.0,
            "semaforo": {"estado": "GRIS", "icono": "⚪", "mensaje": "Sin Objetivo Definido"}
        }

    pct_cumplimiento = (monto_proyectado / monto_objetivo) * 100
    semaforo = calcular_semaforo(pct_cumplimiento, metrica="cumplimiento_objetivo")

    return {
        "monto_objetivo": round(monto_objetivo, 2),
        "monto_proyectado": round(monto_proyectado, 2),
        "pct_cumplimiento": round(pct_cumplimiento, 1),
        "semaforo": semaforo
    }


def calcular_semaforo_variacion(delta_pct: float, tipo: str = "general") -> Dict[str, str]:
    """
    Asigna un semáforo a la variación porcentual (+/- X%):
    - Crecimiento positivo notable: 🟢 Verde
    - Crecimiento leve o estancamiento (+/- umbral neutro): 🟡 Amarillo
    - Caída / retroceso: 🔴 Rojo
    """
    # Umbrales de variación porcentual
    if delta_pct >= 3.0:
        return {"estado": "VERDE", "icono": "🟢", "color": "#09AB3B", "texto": f"Creciendo (+{delta_pct:.1f}%)"}
    elif delta_pct > -3.0:
        signo = "+" if delta_pct > 0 else ""
        return {"estado": "AMARILLO", "icono": "🟡", "color": "#FFAA00", "texto": f"Estable ({signo}{delta_pct:.1f}%)"}
    else:
        return {"estado": "ROJO", "icono": "🔴", "color": "#FF4B4B", "texto": f"En caída ({delta_pct:.1f}%)"}


def calcular_tendencia_mes_a_mes(
    mes_actual: Dict[str, Any],
    mes_anterior: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Compara la performance de dos períodos/meses para un comercio y calcula variaciones:
    - Consultas (% aumento/disminución con semáforo)
    - Colocación / Venta Total en $ (% aumento/disminución con semáforo)
    - Conversión Bruta (% aumento/disminución con semáforo)
    - Approval Rate / Tasa de Aprobación (% aumento/disminución con semáforo)
    - Conversión sobre Oferta (% aumento/disminución con semáforo)
    """
    def _analizar_variable(nombre: str, actual: float, anterior: float) -> Dict[str, Any]:
        if anterior == 0:
            pct_var = 100.0 if actual > 0 else 0.0
        else:
            pct_var = ((actual - anterior) / anterior) * 100.0

        semaforo = calcular_semaforo_variacion(pct_var)
        signo = "+" if pct_var > 0 else ""

        return {
            "nombre": nombre,
            "valor_actual": round(actual, 2),
            "valor_anterior": round(anterior, 2),
            "delta_absoluto": round(actual - anterior, 2),
            "delta_porcentaje": round(pct_var, 1),
            "texto_delta": f"{signo}{pct_var:.1f}%",
            "semaforo": semaforo,
            "icono": semaforo["icono"],
            "estado": semaforo["estado"]
        }

    return {
        "consultas": _analizar_variable(
            "Cantidad de Consultas",
            actual=float(mes_actual.get("total_consultas", 0)),
            anterior=float(mes_anterior.get("total_consultas", 0))
        ),
        "colocacion_monto": _analizar_variable(
            "Colocación ($ Venta Total)",
            actual=float(mes_actual.get("monto_venta_total", 0)),
            anterior=float(mes_anterior.get("monto_venta_total", 0))
        ),
        "approval_rate": _analizar_variable(
            "Approval Rate (% Aprobación)",
            actual=float(mes_actual.get("pct_aprobacion", 0)),
            anterior=float(mes_anterior.get("pct_aprobacion", 0))
        ),
        "conversion_bruta": _analizar_variable(
            "Conversión Bruta (%)",
            actual=float(mes_actual.get("pct_conversion_bruta", 0)),
            anterior=float(mes_anterior.get("pct_conversion_bruta", 0))
        ),
        "conversion_sobre_oferta": _analizar_variable(
            "Conversión sobre Oferta (%)",
            actual=float(mes_actual.get("pct_conversion_sobre_oferta", 0)),
            anterior=float(mes_anterior.get("pct_conversion_sobre_oferta", 0))
        )
    }

