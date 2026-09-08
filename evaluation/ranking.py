"""
Calculo del Ranking de una categoria a partir de los Puntaje de sus
muestras (roadmap, seccion 5.1/5.4).
"""

from typing import Dict, List

from evaluation.models import Jurado, Puntaje, Ranking
from evaluation.scoring import puntaje_final_muestra


def calcular_ranking(
    categoria_id: str,
    puntajes_por_muestra: Dict[str, List[Puntaje]],
    jurados: List[Jurado],
    podar_outliers: bool = True,
) -> List[Ranking]:
    """
    Calcula el puntaje final de cada muestra (ver
    `evaluation.scoring.puntaje_final_muestra`) y devuelve el `Ranking`
    de la categoria ordenado de mayor a menor puntaje, con posiciones
    secuenciales desde 1. El desempate entre puntajes finales iguales es
    por `muestra_id` (orden estable, no hay regla de empate en el
    roadmap).
    """
    finales = {}
    for muestra_id, puntajes in puntajes_por_muestra.items():
        if not puntajes:
            raise ValueError(f"Muestra '{muestra_id}' no tiene puntajes para calcular su ranking")
        finales[muestra_id] = puntaje_final_muestra(
            puntajes, jurados, podar_outliers=podar_outliers
        )

    orden = sorted(finales.items(), key=lambda item: (-item[1], item[0]))

    return [
        Ranking(categoria_id=categoria_id, muestra_id=muestra_id, puntaje_final=puntaje_final, posicion=posicion)
        for posicion, (muestra_id, puntaje_final) in enumerate(orden, start=1)
    ]
