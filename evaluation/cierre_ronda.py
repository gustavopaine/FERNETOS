"""
Servicio de cierre de ronda (roadmap, seccion 5.3): conecta los
repositorios SQL de evaluacion con `calcular_ranking` para calcular y
persistir el `Ranking` de una categoria a partir de los `Puntaje` ya
cargados por los jurados.
"""

from collections import defaultdict
from typing import List

from evaluation.models import Ranking
from evaluation.ranking import calcular_ranking
from evaluation.repository import (
    JuradoRepository,
    MuestraRepository,
    PuntajeRepository,
    RankingRepository,
)


def cerrar_ronda_categoria(
    categoria_id: str,
    muestra_repo: MuestraRepository,
    puntaje_repo: PuntajeRepository,
    jurado_repo: JuradoRepository,
    ranking_repo: RankingRepository,
    podar_outliers: bool = True,
) -> List[Ranking]:
    """
    Calcula el Ranking de `categoria_id` a partir de los Puntaje
    persistidos de sus muestras y lo persiste via `ranking_repo`.
    Devuelve la lista de Ranking calculada (ya ordenada, ver
    `evaluation.ranking.calcular_ranking`).

    Si alguna muestra de la categoria todavia no tiene ningun Puntaje
    cargado, no se persiste nada y se propaga el ValueError de
    `calcular_ranking` que identifica esa muestra - cerrar una ronda
    con jurados faltantes es un error de proceso, no un caso a tolerar
    en silencio.
    """
    muestras = muestra_repo.listar(categoria_id=categoria_id)

    # Una sola consulta para todos los Puntaje en vez de una por muestra
    # (evita N+1 en categorias con muchas muestras).
    puntajes_por_id_de_muestra = defaultdict(list)
    for puntaje in puntaje_repo.listar():
        puntajes_por_id_de_muestra[puntaje.muestra_id].append(puntaje)
    puntajes_por_muestra = {
        muestra.id: puntajes_por_id_de_muestra[muestra.id] for muestra in muestras
    }
    jurados = jurado_repo.listar()

    ranking = calcular_ranking(
        categoria_id, puntajes_por_muestra, jurados, podar_outliers=podar_outliers
    )

    for posicion in ranking:
        ranking_repo.guardar(posicion)

    return ranking
