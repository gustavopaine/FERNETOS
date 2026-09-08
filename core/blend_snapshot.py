"""
Snapshot de un blend calculado, listo para guardar en
`BlendGuardado.datos` (ver core/blend_models.py). Una funcion por
familia (mismo criterio que evaluation/reportes.py y
core/receta_reportes.py: cada familia tiene su propia forma de
composicion, no una compartida forzada).
"""

from typing import Dict

from core.tintura_models import Tintura
from families.campari.campari_calculator import CampariBlendResult
from families.fernet.calculator import BlendResult
from families.gancia.americano_calculator import AmericanoCalculator, VarianteExperimental
from families.gancia.gancia_calculator import GanciaBlendResult


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


def snapshot_gancia(resultado: GanciaBlendResult, tinturas: Dict[str, Tintura]) -> dict:
    """
    Igual criterio que `snapshot_fernet`: tinturas resueltas a nombre,
    no `tintura_id`. Incluye los aditivos (azucar/acido citrico/
    caramelo) porque son parte de la receta de Gancia, no volumen de
    la base - mismo criterio que `_filas_composicion_gancia` en
    core/receta_reportes.py (que los separa en su propia seccion).
    """
    return {
        "params": {
            "volumen_objetivo_litros": resultado.params.volumen_objetivo_litros,
            "abv_objetivo": resultado.params.abv_objetivo,
            "vino_pct": resultado.params.vino_pct,
            "vino_abv": resultado.params.vino_abv,
            "alcohol_fortificacion_abv": resultado.params.alcohol_fortificacion_abv,
            "azucar_pct_wv": resultado.params.azucar_pct_wv,
        },
        "composicion": {
            "vino_ml": resultado.composicion.vino_ml,
            "alcohol_fortificacion_ml": resultado.composicion.alcohol_fortificacion_ml,
            "agua_ml": resultado.composicion.agua_ml,
            "azucar_g": resultado.composicion.azucar_g,
            "acido_citrico_g": resultado.composicion.acido_citrico_g,
            "caramelo_ml": resultado.composicion.caramelo_ml,
            "tinturas": [
                {"nombre": tinturas[tintura_id].nombre, "ml": ml}
                for tintura_id, ml in resultado.composicion.tinturas.items()
                if tintura_id in tinturas
            ],
        },
        "resultado_calculado": {
            "abv_calculado": resultado.abv_calculado,
            "azucar_efectiva_g_l": resultado.azucar_efectiva_g_l,
            "volumen_real_ml": resultado.volumen_real_ml,
        },
        "version": resultado.version,
        "fecha_calculo": resultado.fecha_calculo.isoformat(),
    }


def snapshot_campari(resultado: CampariBlendResult) -> dict:
    """
    Campari no tiene tinturas de stock que resolver a nombre (a
    diferencia de Fernet/Gancia) - los botanicos ya son nombres
    directos, asi que no hace falta el parametro `tinturas` que
    llevan `snapshot_fernet`/`snapshot_gancia`. Se serializan via
    `ComposicionBotanica.to_dict()` (ya existe en
    core/tintura_models.py, mismo criterio que el resto del modelo).
    Sin `params`: Campari no resuelve la composicion contra un target,
    la composicion ingresada ES la receta (mismo criterio documentado
    en `generar_ficha_tecnica_blend_campari`). Sin `version`:
    `CampariBlendResult` no tiene ese campo.
    """
    return {
        "composicion": {
            "alcohol_ml": resultado.composicion.alcohol_ml,
            "alcohol_abv": resultado.composicion.alcohol_abv,
            "agua_ml": resultado.composicion.agua_ml,
            "azucar_g": resultado.composicion.azucar_g,
            "ingredientes_maceracion": [
                i.to_dict() for i in resultado.composicion.ingredientes_maceracion
            ],
            "ingredientes_incorporacion_tardia": [
                i.to_dict() for i in resultado.composicion.ingredientes_incorporacion_tardia
            ],
        },
        "resultado_calculado": {
            "abv_calculado": resultado.abv_calculado,
            "azucar_efectiva_gpl": resultado.azucar_efectiva_gpl,
            "densidad": (
                resultado.control_calidad.densidad if resultado.control_calidad else None
            ),
        },
        "fecha_calculo": resultado.fecha_calculo.isoformat(),
    }


def snapshot_americano(variante: VarianteExperimental) -> dict:
    """
    Igual criterio que `snapshot_campari`: sin tinturas de stock que
    resolver, ingredientes ya son nombres directos, sin `params`
    (la composicion ingresada ES la receta). Incluye `batch_id` y
    `referencia_comercial` - propios de `VarianteExperimental`, sin
    equivalente en Fernet/Gancia/Campari. La azucar efectiva se
    recalcula con `AmericanoCalculator.calcular_azucar_efectiva_gpl`
    (misma fuente unica que usa la ficha tecnica en vivo y la UI, no
    se duplica la formula - ver docs/specs/2026-09-08-fase3-
    ensamblaje-americano.md, hallazgo de /code-review high de esa
    fase) en vez de guardarla ya calculada en `VarianteExperimental`
    (que no la tiene como campo propio).
    """
    composicion = variante.composicion
    return {
        "batch_id": variante.batch_id,
        "referencia_comercial": variante.referencia_comercial,
        "composicion": {
            "alcohol_ml": composicion.alcohol_ml,
            "alcohol_abv": composicion.alcohol_abv,
            "agua_ml": composicion.agua_ml,
            "azucar_g": composicion.azucar_g,
            "ingredientes_base": [i.to_dict() for i in composicion.ingredientes_base],
            "ingredientes_variante": [i.to_dict() for i in composicion.ingredientes_variante],
        },
        "resultado_calculado": {
            "abv_calculado": variante.abv_calculado,
            "azucar_efectiva_gpl": AmericanoCalculator.calcular_azucar_efectiva_gpl(
                composicion.azucar_g, composicion.volumen_total_ml
            ),
        },
        "fecha_calculo": variante.fecha_creacion.isoformat(),
    }
