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
from families.campari.campari_calculator import CampariBlendResult, ComposicionCampari
from families.gancia.americano_calculator import ComposicionAmericano, VarianteExperimental
from core.tintura_models import ComposicionBotanica, ControlCalidad, Tintura
from core.receta_reportes import (
    _filas_composicion_fernet,
    _filas_composicion_gancia,
    _filas_composicion_campari,
    _filas_botanicos,
    _filas_ingredientes_americano,
    generar_ficha_tecnica_blend_fernet,
    generar_ficha_tecnica_blend_gancia,
    generar_ficha_tecnica_blend_campari,
    generar_ficha_tecnica_variante_americano,
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


# --- _filas_composicion_campari / generar_ficha_tecnica_blend_campari ----


def _ingrediente_campari(especie, gramos, parte="raiz"):
    return ComposicionBotanica(especie=especie, porcentaje=0.0, parte_utilizada=parte, gramos=gramos)


def _resultado_campari(
    alcohol_ml=1000.0,
    agua_ml=500.0,
    ingredientes_maceracion=None,
    ingredientes_incorporacion_tardia=None,
    control_calidad=None,
):
    composicion = ComposicionCampari(
        alcohol_ml=alcohol_ml,
        alcohol_abv=40.0,
        agua_ml=agua_ml,
        azucar_g=225.0,
        ingredientes_maceracion=(
            [_ingrediente_campari("ajenjo", 10, "hoja"), _ingrediente_campari("quina", 5, "corteza")]
            if ingredientes_maceracion is None
            else ingredientes_maceracion
        ),
        ingredientes_incorporacion_tardia=(
            [_ingrediente_campari("hibiscus", 10, "flor")]
            if ingredientes_incorporacion_tardia is None
            else ingredientes_incorporacion_tardia
        ),
    )
    return CampariBlendResult(
        composicion=composicion,
        abv_calculado=26.7,
        azucar_efectiva_gpl=150.0,
        control_calidad=control_calidad,
    )


def test_filas_composicion_campari_alcohol_y_agua_suman_100():
    resultado = _resultado_campari()

    filas = _filas_composicion_campari(resultado)

    nombres = [f[0] for f in filas]
    assert any("Alcohol" in n for n in nombres)
    assert "Agua" in nombres
    total_pct = sum(float(pct.rstrip("%")) for _, _, pct in filas)
    assert total_pct == pytest.approx(100.0, abs=0.1)


def test_filas_botanicos_cascara_se_muestra_en_unidad_no_en_gramos():
    """Regresion: las cascaras de citricos de Campari se cuentan como
    piezas enteras ('1 unidad'), no como peso - mostrar 'g' ahi
    contradice la receta real."""
    ingredientes = [
        ComposicionBotanica(especie="naranja", porcentaje=0.0, parte_utilizada="cascara", gramos=1.0),
        ComposicionBotanica(especie="ajenjo", porcentaje=0.0, parte_utilizada="hoja", gramos=10.0),
    ]

    filas = _filas_botanicos(ingredientes)

    assert filas[0] == ("Naranja (cascara)", "1 unidad")
    assert filas[1] == ("Ajenjo (hoja)", "10 g")


def test_filas_composicion_campari_volumen_cero_lanza():
    resultado = _resultado_campari(alcohol_ml=0.0, agua_ml=0.0)

    with pytest.raises(ValueError):
        _filas_composicion_campari(resultado)


def test_generar_ficha_tecnica_campari_produce_pdf_valido():
    resultado = _resultado_campari()

    pdf = generar_ficha_tecnica_blend_campari(resultado)

    assert isinstance(pdf, bytes)
    assert pdf.startswith(b"%PDF")
    assert len(pdf) > 500


def test_generar_ficha_tecnica_campari_con_control_calidad_no_lanza():
    resultado = _resultado_campari(control_calidad=ControlCalidad(densidad=1060))

    pdf = generar_ficha_tecnica_blend_campari(resultado)

    assert pdf.startswith(b"%PDF")


def test_generar_ficha_tecnica_campari_sin_botanicos_no_lanza():
    resultado = _resultado_campari(
        ingredientes_maceracion=[], ingredientes_incorporacion_tardia=[]
    )

    pdf = generar_ficha_tecnica_blend_campari(resultado)

    assert pdf.startswith(b"%PDF")


# --- _filas_ingredientes_americano / generar_ficha_tecnica_variante_americano ---


def _ingrediente_americano(especie, parte="cascara"):
    return ComposicionBotanica(especie=especie, porcentaje=0, parte_utilizada=parte)


def _composicion_americano(
    ingredientes_variante=None, agua_ml=3000.0, alcohol_ml=500.0, ingredientes_base=None
):
    return ComposicionAmericano(
        alcohol_ml=alcohol_ml,
        alcohol_abv=96.0,
        agua_ml=agua_ml,
        azucar_g=900.0,
        ingredientes_base=(
            [
                _ingrediente_americano("genciana", "raiz"),
                _ingrediente_americano("melisa", "hoja"),
                _ingrediente_americano("canela"),
                _ingrediente_americano("anis_estrellado"),
                _ingrediente_americano("angelica", "raiz"),
                _ingrediente_americano("enebro"),
                _ingrediente_americano("pomelo"),
                _ingrediente_americano("limon"),
                _ingrediente_americano("naranja"),
            ]
            if ingredientes_base is None
            else ingredientes_base
        ),
        ingredientes_variante=ingredientes_variante or [],
    )


def _variante_americano(batch_id="AMERICANO_BASE_v1", referencia_comercial=None, **overrides):
    return VarianteExperimental(
        batch_id=batch_id,
        composicion=_composicion_americano(**overrides),
        referencia_comercial=referencia_comercial,
    )


def test_filas_ingredientes_americano_nombre_y_parte():
    ingredientes = [_ingrediente_americano("genciana", "raiz"), _ingrediente_americano("melisa", "hoja")]

    filas = _filas_ingredientes_americano(ingredientes)

    assert filas == [("Genciana", "raiz"), ("Melisa", "hoja")]


def test_filas_ingredientes_americano_lista_vacia():
    assert _filas_ingredientes_americano([]) == []


def test_generar_ficha_tecnica_americano_produce_pdf_valido():
    variante = _variante_americano()

    pdf = generar_ficha_tecnica_variante_americano(variante)

    assert isinstance(pdf, bytes)
    assert pdf.startswith(b"%PDF")
    assert len(pdf) > 500


def test_generar_ficha_tecnica_americano_con_variante_y_notas_no_lanza():
    variante = _variante_americano(
        batch_id="AMERICANO_CLAVO_v1",
        referencia_comercial="Más herbal que Gancia comercial, menos dulce",
        ingredientes_variante=[_ingrediente_americano("clavo_de_olor")],
    )

    pdf = generar_ficha_tecnica_variante_americano(variante)

    assert pdf.startswith(b"%PDF")


def test_generar_ficha_tecnica_americano_volumen_cero_lanza():
    variante = _variante_americano(agua_ml=0.0, alcohol_ml=0.0)

    with pytest.raises(ValueError):
        generar_ficha_tecnica_variante_americano(variante)


def test_generar_ficha_tecnica_americano_sin_ingredientes_base_no_lanza():
    """Regresion: destildar los 9 checkboxes de ingredientes base en la
    UI deja ingredientes_base=[] - la seccion "Ingredientes base" no
    debe intentar armar una Table([]) vacia (ValueError de reportlab)."""
    variante = _variante_americano(ingredientes_base=[])

    pdf = generar_ficha_tecnica_variante_americano(variante)

    assert pdf.startswith(b"%PDF")
