"""
Tests para core/receta_reportes.py: ficha tecnica exportable de un
blend de Fernet o Gancia ya calculado (roadmap Fase 3, ultimo item de
"Salidas del modulo" - "Exportacion de ficha tecnica de receta").
Opera sobre el BlendResult/GanciaBlendResult que ya devuelven los
calculators respectivos (los blends no se persisten todavia, ver
docs/specs/2026-09-08-fase3-ficha-tecnica-blend.md), no sobre el
modelo generico Receta (sin datos reales, sin UI). TDD: escritos antes
que la implementacion.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest

from families.fernet.calculator import BlendParams, BlendResult, ComposicionBlend
from families.gancia.gancia_calculator import (
    ComposicionBlendGancia,
    GanciaBlendParams,
    GanciaBlendResult,
)
from core.tintura_models import Tintura
from core.receta_reportes import (
    _filas_composicion_fernet,
    _filas_composicion_gancia,
    generar_ficha_tecnica_blend_fernet,
    generar_ficha_tecnica_blend_gancia,
)


def _resultado(tinturas_ml=None, alcohol_base_ml=400.0, agua_base_ml=550.0):
    composicion = ComposicionBlend(
        alcohol_base_ml=alcohol_base_ml,
        agua_base_ml=agua_base_ml,
        tinturas={"T-1": 30.0, "T-2": 20.0} if tinturas_ml is None else tinturas_ml,
        azucar_g=195.0,
    )
    return BlendResult(
        params=BlendParams(volumen_objetivo_litros=1.0),
        composicion=composicion,
        abv_calculado=40.1,
        azucar_efectiva_gpl=195,
        ph_estimado=5.2,
        margen_error_ml=0.5,
    )


# --- _filas_composicion_fernet -------------------------------------------


def test_filas_composicion_incluye_tinturas_alcohol_y_agua():
    resultado = _resultado()
    tinturas = {"T-1": Tintura(nombre="Ajenjo"), "T-2": Tintura(nombre="Genciana")}

    filas = _filas_composicion_fernet(resultado, tinturas)

    nombres = [f[0] for f in filas]
    assert "Ajenjo" in nombres
    assert "Genciana" in nombres
    assert "Alcohol base" in nombres
    assert "Agua" in nombres


def test_filas_composicion_porcentajes_suman_100():
    resultado = _resultado()
    tinturas = {"T-1": Tintura(nombre="Ajenjo"), "T-2": Tintura(nombre="Genciana")}

    filas = _filas_composicion_fernet(resultado, tinturas)

    total_pct = sum(float(pct.rstrip("%")) for _, _, pct in filas)
    assert total_pct == pytest.approx(100.0, abs=0.1)


def test_filas_composicion_omite_tintura_id_desconocido():
    resultado = _resultado(tinturas_ml={"T-1": 30.0, "T-FANTASMA": 10.0})
    tinturas = {"T-1": Tintura(nombre="Ajenjo")}

    filas = _filas_composicion_fernet(resultado, tinturas)

    nombres = [f[0] for f in filas]
    assert "Ajenjo" in nombres
    assert not any("FANTASMA" in n for n in nombres)


def test_filas_composicion_sin_tinturas_solo_alcohol_y_agua():
    resultado = _resultado(tinturas_ml={})

    filas = _filas_composicion_fernet(resultado, tinturas={})

    assert [f[0] for f in filas] == ["Alcohol base", "Agua"]


def test_filas_composicion_volumen_total_cero_lanza():
    resultado = _resultado(tinturas_ml={}, alcohol_base_ml=0.0, agua_base_ml=0.0)

    with pytest.raises(ValueError):
        _filas_composicion_fernet(resultado, tinturas={})


# --- generar_ficha_tecnica_blend_fernet -----------------------------------


def test_generar_ficha_tecnica_produce_pdf_valido():
    resultado = _resultado()
    tinturas = {"T-1": Tintura(nombre="Ajenjo"), "T-2": Tintura(nombre="Genciana")}

    pdf = generar_ficha_tecnica_blend_fernet(resultado, tinturas)

    assert isinstance(pdf, bytes)
    assert pdf.startswith(b"%PDF")
    assert len(pdf) > 500


def test_generar_ficha_tecnica_sin_tinturas_no_lanza():
    resultado = _resultado(tinturas_ml={})

    pdf = generar_ficha_tecnica_blend_fernet(resultado, tinturas={})

    assert pdf.startswith(b"%PDF")


# --- _filas_composicion_gancia / generar_ficha_tecnica_blend_gancia -------


def _resultado_gancia(tinturas_ml=None, vino_ml=7800.0, alcohol_fortificacion_ml=1200.0, agua_ml=970.0):
    composicion = ComposicionBlendGancia(
        vino_ml=vino_ml,
        alcohol_fortificacion_ml=alcohol_fortificacion_ml,
        tinturas={"T-1": 30.0} if tinturas_ml is None else tinturas_ml,
        agua_ml=agua_ml,
        azucar_g=1000.0,
        acido_citrico_g=5.0,
        caramelo_ml=2.0,
    )
    return GanciaBlendResult(
        params=GanciaBlendParams(volumen_objetivo_litros=10.0),
        composicion=composicion,
        abv_calculado=17.1,
    )


def test_filas_composicion_gancia_incluye_todos_los_componentes():
    resultado = _resultado_gancia()
    tinturas = {"T-1": Tintura(nombre="Cascara de naranja")}

    filas = _filas_composicion_gancia(resultado, tinturas)

    nombres = [f[0] for f in filas]
    assert nombres == [
        "Cascara de naranja", "Vino base", "Alcohol de fortificación", "Agua",
    ]


def test_filas_composicion_gancia_porcentajes_suman_100():
    resultado = _resultado_gancia()
    tinturas = {"T-1": Tintura(nombre="Cascara de naranja")}

    filas = _filas_composicion_gancia(resultado, tinturas)

    total_pct = sum(float(pct.rstrip("%")) for _, _, pct in filas)
    assert total_pct == pytest.approx(100.0, abs=0.1)


def test_filas_composicion_gancia_omite_tintura_id_desconocido():
    resultado = _resultado_gancia(tinturas_ml={"T-1": 30.0, "T-FANTASMA": 10.0})
    tinturas = {"T-1": Tintura(nombre="Cascara de naranja")}

    filas = _filas_composicion_gancia(resultado, tinturas)

    nombres = [f[0] for f in filas]
    assert "Cascara de naranja" in nombres
    assert not any("FANTASMA" in n for n in nombres)


def test_generar_ficha_tecnica_gancia_produce_pdf_valido():
    resultado = _resultado_gancia()
    tinturas = {"T-1": Tintura(nombre="Cascara de naranja")}

    pdf = generar_ficha_tecnica_blend_gancia(resultado, tinturas)

    assert isinstance(pdf, bytes)
    assert pdf.startswith(b"%PDF")
    assert len(pdf) > 500


def test_generar_ficha_tecnica_gancia_sin_tinturas_no_lanza():
    resultado = _resultado_gancia(tinturas_ml={})

    pdf = generar_ficha_tecnica_blend_gancia(resultado, tinturas={})

    assert pdf.startswith(b"%PDF")


def test_filas_composicion_gancia_volumen_total_cero_lanza():
    resultado = _resultado_gancia(
        tinturas_ml={}, vino_ml=0.0, alcohol_fortificacion_ml=0.0, agua_ml=0.0
    )

    with pytest.raises(ValueError):
        _filas_composicion_gancia(resultado, tinturas={})
