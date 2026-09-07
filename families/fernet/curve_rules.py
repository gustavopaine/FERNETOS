"""
Heurística de día de corte específica de Fernet.
Extraída de core/curve_analysis.py: CurveAnalyzer.sugerir_dia_corte()
despacha acá cuando la tintura es Producto.FERNET.
"""

from typing import Optional

from core.tintura_models import GrupoFuncional, RegistroExtraccion


def sugerir_dia_corte_fernet(
    grupo: Optional[GrupoFuncional], ultimo_registro: RegistroExtraccion
) -> Optional[int]:
    """
    Heurística de día de corte por grupo funcional para Fernet, quien no
    tiene todavía un punto óptimo detectado por inflexión de curva.

    Args:
        grupo: Grupo funcional de la tintura (puede ser None)
        ultimo_registro: Último registro de extracción disponible

    Returns:
        Optional[int]: Día sugerido, o None si el grupo no tiene heurística
            de Fernet (el llamador cae al fallback genérico).
    """
    if grupo == GrupoFuncional.AMARGOS_ESTRUCTURALES:
        # Amargos: entre 16-21 días, preferible antes si ya hay intensidad suficiente
        if ultimo_registro.intensidad_estimada > 80 and ultimo_registro.dia >= 16:
            return ultimo_registro.dia
        return min(21, ultimo_registro.dia + 2)

    elif grupo == GrupoFuncional.AROMATICA_ALTA:
        # Aromáticos: máximo 7 días
        return min(7, ultimo_registro.dia)

    elif grupo == GrupoFuncional.ESPECIAS_CALIDAS:
        # Especias: 14-18 días
        if ultimo_registro.dia >= 14:
            return ultimo_registro.dia
        return 14

    elif grupo == GrupoFuncional.CITRICOS:
        # Cítricos: 5-7 días
        return min(7, ultimo_registro.dia + 1)

    return None
