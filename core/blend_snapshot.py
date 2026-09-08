"""
Snapshot de un blend calculado, listo para guardar en
`BlendGuardado.datos` (ver core/blend_models.py). Una funcion por
familia (mismo criterio que evaluation/reportes.py y
core/receta_reportes.py: cada familia tiene su propia forma de
composicion, no una compartida forzada).
"""

from typing import Dict

from core.tintura_models import Tintura
from families.fernet.calculator import BlendResult


def snapshot_fernet(resultado: BlendResult, tinturas: Dict[str, Tintura]) -> dict:
    """
    Arma el dict a guardar para un blend de Fernet. Las tinturas se
    resuelven a nombre (no se guarda `tintura_id`): un blend guardado
    debe seguir siendo legible aunque la tintura original se borre o
    se renombre despues - un `tintura_id` sin `Tintura` correspondiente
    se omite, mismo criterio que `_filas_composicion_fernet` en
    core/receta_reportes.py.
    """
    return {
        "params": {
            "volumen_objetivo_litros": resultado.params.volumen_objetivo_litros,
            "abv_objetivo": resultado.params.abv_objetivo,
            "azucar_objetivo_gpl": resultado.params.azucar_objetivo_gpl,
            "alcohol_base_abv": resultado.params.alcohol_base_abv,
            "ph_objetivo": resultado.params.ph_objetivo,
        },
        "composicion": {
            "alcohol_base_ml": resultado.composicion.alcohol_base_ml,
            "agua_base_ml": resultado.composicion.agua_base_ml,
            "azucar_g": resultado.composicion.azucar_g,
            "tinturas": [
                {"nombre": tinturas[tintura_id].nombre, "ml": ml}
                for tintura_id, ml in resultado.composicion.tinturas.items()
                if tintura_id in tinturas
            ],
        },
        "resultado_calculado": {
            "abv_calculado": resultado.abv_calculado,
            "azucar_efectiva_gpl": resultado.azucar_efectiva_gpl,
            "ph_estimado": resultado.ph_estimado,
            "volumen_real_ml": resultado.volumen_real_ml,
            "margen_error_ml": resultado.margen_error_ml,
        },
        "version": resultado.version,
        "fecha_calculo": resultado.fecha_calculo.isoformat(),
    }
