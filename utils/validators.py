# -*- coding: utf-8 -*-
"""Validaciones de datos para tinturas."""

from typing import List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from modules.tinturas.models import (
        ComposicionBotanica,
        GrupoFuncional,
        ParametrosExtraccion,
        Producto,
    )

PORCENTAJE_TOLERANCIA = 0.5


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

    from modules.tinturas.models import GRUPOS_POR_PRODUCTO

    if grupo not in GRUPOS_POR_PRODUCTO[producto]:
        raise ValueError(
            f"El grupo '{grupo.value}' no es válido para el producto '{producto.value}'"
        )
