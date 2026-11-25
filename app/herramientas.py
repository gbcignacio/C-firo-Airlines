"""Herramientas locales del agente calculadora de la aerolínea.

Una herramienta es una función normal con el decorador @tool. El modelo lee
el docstring para saber cuándo usarla y los tipos para saber qué pasarle.

Las reglas (precios de maletas, importes de compensación, porcentajes de reembolso,
coeficientes de millas...) NO están escritas aquí: se pasan como parámetros. Así la
calculadora depende de lo que el documentalista encuentre en las normas de la
aerolínea, igual que en el manual los pesos venían de la guía docente.
"""
import math
from datetime import datetime

from langchain_core.tools import tool


def _euros(cantidad: float) -> str:
    return f"{cantidad:,.2f} €".replace(",", "X").replace(".", ",").replace("X", ".")


@tool
def coste_equipaje(
    trayectos: int,
    maletas_extra: int,
    precio_maleta_extra: float,
    maletas_con_sobrepeso: int = 0,
    precio_sobrepeso: float = 0,
    otros_suplementos_por_trayecto: float = 0,
) -> str:
    """Calcula lo que se paga por equipaje en un viaje.
    trayectos: 1 si es solo ida, 2 si es ida y vuelta.
    maletas_extra: maletas facturadas que NO incluye la tarifa (por trayecto).
    precio_maleta_extra: precio de cada maleta extra por trayecto según la normativa.
    maletas_con_sobrepeso y precio_sobrepeso: maletas de más peso del permitido y su suplemento.
    otros_suplementos_por_trayecto: suma de otros suplementos (bicicleta, mascota, maleta de cabina...)."""
    por_trayecto = (maletas_extra * precio_maleta_extra + maletas_con_sobrepeso * precio_sobrepeso
                    + otros_suplementos_por_trayecto)
    total = por_trayecto * trayectos
    return (f"Por trayecto: {maletas_extra} maleta(s) extra × {_euros(precio_maleta_extra)} + "
            f"{maletas_con_sobrepeso} sobrepeso × {_euros(precio_sobrepeso)} + otros "
            f"{_euros(otros_suplementos_por_trayecto)} = {_euros(por_trayecto)}. "
            f"Con {trayectos} trayecto(s): {_euros(total)} en total.")


@tool
def compensacion_retraso(
    distancia_km: float,
    horas_retraso_llegada: float,
    horas_minimas: float,
    limite_corto_km: float,
    limite_medio_km: float,
    importe_corto: float,
    importe_medio: float,
    importe_largo: float,
) -> str:
    """Calcula la compensación por retraso de un vuelo.
    Si el retraso en la llegada es menor que horas_minimas, no hay compensación.
    Si no: importe_corto hasta limite_corto_km, importe_medio hasta limite_medio_km,
    e importe_largo para distancias mayores. Todas las reglas salen de la normativa."""
    if horas_retraso_llegada < horas_minimas:
        return (f"Retraso de {horas_retraso_llegada:g} h: menos de {horas_minimas:g} h, "
                "no hay derecho a compensación.")
    if distancia_km <= limite_corto_km:
        importe, tramo = importe_corto, f"hasta {limite_corto_km:g} km"
    elif distancia_km <= limite_medio_km:
        importe, tramo = importe_medio, f"entre {limite_corto_km:g} y {limite_medio_km:g} km"
    else:
        importe, tramo = importe_largo, f"más de {limite_medio_km:g} km"
    return (f"Vuelo de {distancia_km:g} km ({tramo}) con {horas_retraso_llegada:g} h de retraso: "
            f"compensación de {_euros(importe)} por pasajero.")


@tool
def reembolso_cancelacion(precio_tarifa: float, tasas: float, porcentaje_reembolso_tarifa: float) -> str:
    """Calcula cuánto se devuelve al cancelar un billete: el porcentaje de la tarifa que diga
    la normativa (porcentaje_reembolso_tarifa, p. ej. 80 para un 80 %) más las tasas
    aeroportuarias (que se devuelven completas). precio_tarifa NO incluye las tasas."""
    tarifa = precio_tarifa * porcentaje_reembolso_tarifa / 100
    return (f"Tarifa: {porcentaje_reembolso_tarifa:g} % de {_euros(precio_tarifa)} = {_euros(tarifa)}. "
            f"Tasas: {_euros(tasas)}. Total a devolver: {_euros(tarifa + tasas)}.")


@tool
def coste_cambio_vuelo(cargo_por_trayecto: float, trayectos_cambiados: int, precio_actual: float, precio_nuevo: float) -> str:
    """Calcula lo que cuesta cambiar un vuelo: el cargo de cambio por cada trayecto cambiado
    más la diferencia de tarifa si el nuevo vuelo es más caro (si es más barato no se devuelve nada)."""
    cargo = cargo_por_trayecto * trayectos_cambiados
    diferencia = max(0.0, precio_nuevo - precio_actual)
    return (f"Cargo de cambio: {trayectos_cambiados} × {_euros(cargo_por_trayecto)} = {_euros(cargo)}. "
            f"Diferencia de tarifa: {_euros(diferencia)}. Total a pagar: {_euros(cargo + diferencia)}.")


@tool
def millas_ganadas(distancia_km: float, trayectos: int, millas_por_km: float, bonus_nivel_pct: float = 0) -> str:
    """Calcula las millas de Céfiro Club que se ganan en un viaje.
    distancia_km: distancia de UN trayecto. trayectos: 1 ida, 2 ida y vuelta.
    millas_por_km: coeficiente de la tarifa. bonus_nivel_pct: extra del nivel (p. ej. 25 para +25 %).
    Redondea hacia abajo."""
    base = distancia_km * trayectos * millas_por_km
    total = math.floor(base * (1 + bonus_nivel_pct / 100))
    return (f"{distancia_km:g} km × {trayectos} trayecto(s) × {millas_por_km:g} = {base:g} millas base; "
            f"con +{bonus_nivel_pct:g} % de nivel: {total} millas.")


@tool
def horas_entre(fecha_hora_inicio: str, fecha_hora_fin: str) -> str:
    """Calcula las horas que hay entre dos momentos, en formato AAAA-MM-DD HH:MM.
    Sirve para saber con cuánta antelación se cancela o cuánto retraso ha habido."""
    inicio = datetime.fromisoformat(fecha_hora_inicio.strip())
    fin = datetime.fromisoformat(fecha_hora_fin.strip())
    horas = (fin - inicio).total_seconds() / 3600
    return f"Entre {inicio:%d/%m/%Y %H:%M} y {fin:%d/%m/%Y %H:%M} hay {horas:.1f} horas ({horas / 24:.1f} días)."


HERRAMIENTAS_CALCULO = [
    coste_equipaje,
    compensacion_retraso,
    reembolso_cancelacion,
    coste_cambio_vuelo,
    millas_ganadas,
    horas_entre,
]
