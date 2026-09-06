"""
Cálculos compartidos entre calculadoras de blend de distintos productos
(FernetCalculator, GanciaCalculator). La única pieza que ambas fórmulas
genuinamente comparten: el balance de alcohol puro ponderado por volumen.
"""

from typing import List, Tuple


def alcohol_puro_total(componentes: List[Tuple[float, float]]) -> float:
    """
    Suma el alcohol puro aportado por cada componente de un blend.

    Args:
        componentes: lista de (volumen_ml, abv_pct) por componente.

    Returns:
        float: mililitros de alcohol puro.
    """
    return sum(volumen * (abv / 100) for volumen, abv in componentes)


def abv_resultante(componentes: List[Tuple[float, float]], volumen_total_ml: float) -> float:
    """
    Calcula el ABV resultante de mezclar los componentes dados.

    Args:
        componentes: lista de (volumen_ml, abv_pct) por componente.
        volumen_total_ml: volumen total del blend (incluye todos los
            componentes, aporten o no alcohol).

    Returns:
        float: ABV resultante (%). 0.0 si volumen_total_ml es 0.
    """
    if volumen_total_ml == 0:
        return 0.0
    return (alcohol_puro_total(componentes) / volumen_total_ml) * 100
