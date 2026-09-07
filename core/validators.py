# -*- coding: utf-8 -*-
"""Validaciones de datos para tinturas."""

from typing import List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from core.tintura_models import (
        ComposicionBotanica,
        CompatibilidadFamilia,
        GrupoFuncional,
        ParametrosExtraccion,
        Producto,
    )

PORCENTAJE_TOLERANCIA = 0.5

# Nombres de familia públicos (fernet/americano/campari), no los valores del
# enum Producto (que todavía dice 'gancia' internamente) - son dos
# vocabularios distintos a propósito, ver
# docs/specs/2026-09-06-americano-variantes-experimentales.md.
FAMILIAS_COMPATIBLES_VALIDAS = frozenset({"fernet", "americano", "campari"})


def validar_composicion_botanica(composicion: List["ComposicionBotanica"]) -> None:
    """Valida que la composición botánica sea físicamente posible.

    Una composición vacía es válida (estado transitorio antes de completar el
    wizard, o al rehidratar una tintura desde la base de datos).
    """
    if not composicion:
        return

    for c in composicion:
        if c.porcentaje < 0:
            raise ValueError(
                f"Porcentaje negativo para '{c.especie}': {c.porcentaje}%"
            )

    total = sum(c.porcentaje for c in composicion)
    if abs(total - 100) > PORCENTAJE_TOLERANCIA:
        raise ValueError(
            f"La composición botánica debe sumar 100% (actual: {total}%)"
        )


def validar_parametros_extraccion(parametros: "ParametrosExtraccion") -> None:
    """Valida que los parámetros de extracción sean físicamente posibles."""
    if not (0 < parametros.abv_objetivo <= 100):
        raise ValueError(
            f"abv_objetivo fuera de rango (0, 100]: {parametros.abv_objetivo}"
        )

    if parametros.tiempo_estimado_dias <= 0:
        raise ValueError(
            f"tiempo_estimado_dias debe ser positivo: {parametros.tiempo_estimado_dias}"
        )


def validar_grupo_funcional_para_producto(
    producto: "Producto", grupo: Optional["GrupoFuncional"]
) -> None:
    """Valida que el grupo funcional corresponda al producto de la tintura.

    Sin grupo asignado todavía es válido (mismo criterio que una
    composición vacía: estado transitorio del wizard o rehidratación).
    """
    if grupo is None:
        return

    from core.tintura_models import GRUPOS_POR_PRODUCTO

    if grupo not in GRUPOS_POR_PRODUCTO[producto]:
        raise ValueError(
            f"El grupo '{grupo.value}' no es válido para el producto '{producto.value}'"
        )


def _validar_nombre_familia(familia: str, contexto: str) -> None:
    """Valida un nombre de familia contra FAMILIAS_COMPATIBLES_VALIDAS.

    `contexto` (p.ej. "compatible", "de receta") solo cambia el mensaje de
    error para indicar de dónde vino el valor inválido.
    """
    if familia not in FAMILIAS_COMPATIBLES_VALIDAS:
        raise ValueError(
            f"Familia {contexto} desconocida: '{familia}'. "
            f"Válidas: {sorted(FAMILIAS_COMPATIBLES_VALIDAS)}"
        )


def validar_familias_compatibles(
    compatibilidades: List["CompatibilidadFamilia"],
) -> None:
    """Valida las CompatibilidadFamilia de una tintura.

    Chequea nombre de familia reconocido, sin duplicados (la tabla
    `compatibilidad_familias` tiene UNIQUE(tintura_id, familia)) y rango
    de dosis coherente.
    """
    vistas = set()
    for compat in compatibilidades:
        _validar_nombre_familia(compat.familia, "compatible")

        if compat.familia in vistas:
            raise ValueError(
                f"Familia compatible duplicada: '{compat.familia}'"
            )
        vistas.add(compat.familia)

        dosis_min = compat.dosis_min_ml_l
        dosis_max = compat.dosis_max_ml_l
        if dosis_min is not None and dosis_min < 0:
            raise ValueError(
                f"dosis_min_ml_l negativa para familia '{compat.familia}': {dosis_min}"
            )
        if dosis_max is not None and dosis_max < 0:
            raise ValueError(
                f"dosis_max_ml_l negativa para familia '{compat.familia}': {dosis_max}"
            )
        if dosis_min is not None and dosis_max is not None and dosis_min > dosis_max:
            raise ValueError(
                f"Rango de dosis inválido para familia '{compat.familia}': "
                f"dosis_min_ml_l ({dosis_min}) > dosis_max_ml_l ({dosis_max})"
            )


def validar_familia_receta(familia: str) -> None:
    """Valida que una Receta use un nombre de familia reconocido."""
    _validar_nombre_familia(familia, "de receta")
