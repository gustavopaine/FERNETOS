"""
Tests para core/blend_snapshot.py: arma el dict de forma libre que se
guarda en BlendGuardado.datos para un blend de Fernet ya calculado.
TDD: escritos antes que la implementacion.
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
from core.blend_snapshot import snapshot_fernet, snapshot_gancia


def _resultado(tinturas_ml=None):
    composicion = ComposicionBlend(
        alcohol_base_ml=400.0,
        agua_base_ml=550.0,
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


def test_snapshot_resuelve_tinturas_a_nombre_no_a_id():
    resultado = _resultado()
    tinturas = {"T-1": Tintura(nombre="Ajenjo"), "T-2": Tintura(nombre="Genciana")}

    snapshot = snapshot_fernet(resultado, tinturas)

    nombres = [t["nombre"] for t in snapshot["composicion"]["tinturas"]]
    assert "Ajenjo" in nombres
    assert "Genciana" in nombres
    assert not any("T-1" in n or "T-2" in n for n in nombres)


def test_snapshot_omite_tintura_id_desconocido():
    resultado = _resultado(tinturas_ml={"T-1": 30.0, "T-FANTASMA": 10.0})
    tinturas = {"T-1": Tintura(nombre="Ajenjo")}

    snapshot = snapshot_fernet(resultado, tinturas)

    nombres = [t["nombre"] for t in snapshot["composicion"]["tinturas"]]
    assert nombres == ["Ajenjo"]


def test_snapshot_incluye_parametros_y_resultado_calculado():
    resultado = _resultado()
    tinturas = {"T-1": Tintura(nombre="Ajenjo"), "T-2": Tintura(nombre="Genciana")}

    snapshot = snapshot_fernet(resultado, tinturas)

    assert snapshot["params"]["volumen_objetivo_litros"] == pytest.approx(1.0)
    assert snapshot["resultado_calculado"]["abv_calculado"] == pytest.approx(40.1)
    assert snapshot["composicion"]["alcohol_base_ml"] == pytest.approx(400.0)
    assert snapshot["composicion"]["agua_base_ml"] == pytest.approx(550.0)


def test_snapshot_es_serializable_a_json():
    import json

    resultado = _resultado()
    tinturas = {"T-1": Tintura(nombre="Ajenjo"), "T-2": Tintura(nombre="Genciana")}

    snapshot = snapshot_fernet(resultado, tinturas)

    # No debe lanzar - todo tiene que ser tipos nativos de JSON.
    json.dumps(snapshot)


# --- snapshot_gancia -------------------------------------------------


def _resultado_gancia(tinturas_ml=None):
    composicion = ComposicionBlendGancia(
        vino_ml=7800.0,
        alcohol_fortificacion_ml=1200.0,
        tinturas={"T-1": 30.0} if tinturas_ml is None else tinturas_ml,
        agua_ml=970.0,
        azucar_g=1000.0,
        acido_citrico_g=5.0,
        caramelo_ml=2.0,
    )
    return GanciaBlendResult(
        params=GanciaBlendParams(volumen_objetivo_litros=10.0),
        composicion=composicion,
        abv_calculado=17.1,
        azucar_efectiva_g_l=100.0,
    )


def test_snapshot_gancia_resuelve_tinturas_a_nombre():
    resultado = _resultado_gancia()
    tinturas = {"T-1": Tintura(nombre="Cascara de naranja")}

    snapshot = snapshot_gancia(resultado, tinturas)

    nombres = [t["nombre"] for t in snapshot["composicion"]["tinturas"]]
    assert nombres == ["Cascara de naranja"]


def test_snapshot_gancia_omite_tintura_id_desconocido():
    resultado = _resultado_gancia(tinturas_ml={"T-1": 30.0, "T-FANTASMA": 10.0})
    tinturas = {"T-1": Tintura(nombre="Cascara de naranja")}

    snapshot = snapshot_gancia(resultado, tinturas)

    nombres = [t["nombre"] for t in snapshot["composicion"]["tinturas"]]
    assert nombres == ["Cascara de naranja"]


def test_snapshot_gancia_incluye_aditivos_y_resultado_calculado():
    resultado = _resultado_gancia()
    tinturas = {"T-1": Tintura(nombre="Cascara de naranja")}

    snapshot = snapshot_gancia(resultado, tinturas)

    assert snapshot["composicion"]["azucar_g"] == pytest.approx(1000.0)
    assert snapshot["composicion"]["acido_citrico_g"] == pytest.approx(5.0)
    assert snapshot["composicion"]["caramelo_ml"] == pytest.approx(2.0)
    assert snapshot["resultado_calculado"]["abv_calculado"] == pytest.approx(17.1)
    assert snapshot["resultado_calculado"]["azucar_efectiva_g_l"] == pytest.approx(100.0)


def test_snapshot_gancia_es_serializable_a_json():
    import json

    resultado = _resultado_gancia()
    tinturas = {"T-1": Tintura(nombre="Cascara de naranja")}

    snapshot = snapshot_gancia(resultado, tinturas)

    json.dumps(snapshot)
