"""
Heurística de día de corte específica de Gancia.
Extraída de core/curve_analysis.py: CurveAnalyzer.sugerir_dia_corte()
despacha acá cuando la tintura es Producto.GANCIA.
"""

from typing import Optional

from core.tintura_models import GrupoFuncional, RegistroExtraccion


def sugerir_dia_corte_gancia(
    grupo: Optional[GrupoFuncional], ultimo_registro: RegistroExtraccion
) -> Optional[int]:
    """
    Dato real de receta de Gancia casero (infusión directa de cáscaras
    cítricas, romero y clavo en alcohol+agua): 40 días de maceración,
    agitación cada 2 días. Se aplica igual a los 4 grupos de Gancia porque
    en esta receta todo macera junto en un solo lote, no por separado
    como en Fernet.

    Args:
        grupo: Grupo funcional de la tintura (no se usa, ver docstring)
        ultimo_registro: Último registro de extracción disponible

    Returns:
        Optional[int]: Día sugerido
    """
    if ultimo_registro.dia >= 40:
        return ultimo_registro.dia
    return 40
