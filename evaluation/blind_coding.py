"""
Orden de cata aleatorizado por jurado (roadmap, seccion 5.3): cada
jurado cata las muestras de una categoria en un orden distinto, para
evitar el sesgo de "la primera siempre puntua mas alto".
"""

import hashlib
import random
from typing import List

from evaluation.models import Muestra


def _seed_para_jurado(jurado_id: str) -> int:
    """
    Semilla estable a partir del jurado_id. No usa hash() de Python: esta
    salado por proceso (PYTHONHASHSEED) y daria un orden distinto cada
    vez que se reinicia la app, rompiendo la propiedad de que el orden
    de un jurado es reproducible si hay que recargar su sesion de cata.
    """
    digest = hashlib.sha256(jurado_id.encode("utf-8")).hexdigest()
    return int(digest[:16], 16)


def orden_cata_para_jurado(muestras: List[Muestra], jurado_id: str) -> List[Muestra]:
    """
    Devuelve una copia de `muestras` en un orden aleatorio pero
    reproducible para ese `jurado_id` (mismo jurado + mismas muestras =
    mismo orden; jurados distintos = ordenes independientes entre si).
    """
    orden = list(muestras)
    random.Random(_seed_para_jurado(jurado_id)).shuffle(orden)
    return orden
