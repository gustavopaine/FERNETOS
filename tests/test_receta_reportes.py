"""
Tests para core/receta_reportes.py: ficha tecnica exportable de un
blend de Fernet ya calculado (roadmap Fase 3, ultimo item de "Salidas
del modulo" - "Exportacion de ficha tecnica de receta"). Opera sobre
el BlendResult que ya devuelve FernetCalculator (los blends no se
persisten todavia, ver docs/specs/2026-09-08-fase3-ficha-tecnica-blend.md),
no sobre el modelo generico Receta (sin datos reales, sin UI). TDD:
escritos antes que la implementacion.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest

from families.fernet.calculator import BlendParams, BlendResult, ComposicionBlend
from core.tintura_models import Tintura
from core.receta_reportes import _filas_composicion_fernet, generar_ficha_tecnica_blend_fernet


def _resultado(tinturas_ml=None):
    composicion = ComposicionBlend(
        alcohol_base_ml=400.0,
        agua_base_ml=550.0,
        tinturas=tinturas_ml or {"T-1": 30.0, "T-2": 20.0},
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
