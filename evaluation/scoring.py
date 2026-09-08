"""
Agregacion de puntajes de multiples jurados en un puntaje final por
muestra (roadmap, seccion 5.3): media recortada opcional (poda de
outliers) y ponderacion por `Jurado.peso_voto`.
"""

from typing import List

from evaluation.models import Jurado, Puntaje


def puntaje_final_muestra(
    puntajes: List[Puntaje],
    jurados: List[Jurado],
    podar_outliers: bool = True,
) -> float:
    """
    Combina los `Puntaje` de una misma muestra (uno por jurado) en un
    puntaje final.

    Si `podar_outliers` es True y hay al menos 3 puntajes, se descarta
    el de mayor y el de menor `puntaje_ponderado()` (media recortada)
    antes de promediar - con menos de 3 no hay suficiente margen para
    podar dos y que quede algo, asi que se promedian todos. El promedio
    final pondera cada puntaje restante por el `peso_voto` de su jurado.
    """
    if not puntajes:
        raise ValueError("No hay puntajes para calcular un puntaje final")

    pesos_por_jurado = {j.id: j.peso_voto for j in jurados}
    faltantes = {p.jurado_id for p in puntajes} - pesos_por_jurado.keys()
    if faltantes:
        raise ValueError(f"Jurado(s) desconocido(s) en 'jurados': {sorted(faltantes)}")

    considerados = list(puntajes)
    if podar_outliers and len(considerados) >= 3:
        considerados = sorted(considerados, key=lambda p: p.puntaje_ponderado())
        considerados = considerados[1:-1]

    suma_ponderada = sum(
        p.puntaje_ponderado() * pesos_por_jurado[p.jurado_id] for p in considerados
    )
    suma_pesos = sum(pesos_por_jurado[p.jurado_id] for p in considerados)

    return suma_ponderada / suma_pesos
