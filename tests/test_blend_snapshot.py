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
from core.tintura_models import Tintura
from core.blend_snapshot import snapshot_fernet


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
