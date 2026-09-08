"""
Progreso de puntajes de una categoria (roadmap, seccion 5.4, "planilla
de puntajes en vivo"): cuantos de los pares (muestra, jurado)
esperados ya tienen un Puntaje cargado.
"""

from typing import List

from evaluation.models import Jurado, Muestra, ProgresoCategoria, Puntaje


def calcular_progreso_categoria(
    muestras: List[Muestra], jurados: List[Jurado], puntajes: List[Puntaje]
) -> ProgresoCategoria:
    """
    `puntajes_esperados` es `len(muestras) * len(jurados)` (cada jurado
    puntua cada muestra). Un `Puntaje` de un `jurado_id` que no esta en
    `jurados` no cuenta como cargado - la lista de jurados de la
    categoria es la fuente de verdad de que pares se esperan, no lo
    que ya se cargo.
    """
    ids_jurados = {j.id for j in jurados}
    cargados = {
        (p.muestra_id, p.jurado_id) for p in puntajes if p.jurado_id in ids_jurados
    }

    pendientes = [
        (muestra.id, jurado.id)
        for muestra in muestras
        for jurado in jurados
        if (muestra.id, jurado.id) not in cargados
    ]

    return ProgresoCategoria(
        puntajes_cargados=len(muestras) * len(jurados) - len(pendientes),
        puntajes_esperados=len(muestras) * len(jurados),
        pendientes=pendientes,
    )
