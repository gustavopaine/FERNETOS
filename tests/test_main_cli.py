"""
Tests para main.py (CLI): la composición inválida debe dar un mensaje
amigable en vez de un traceback crudo (regresión encontrada en code review
tras conectar la validación de utils/validators.py a Tintura.__post_init__).
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import FernetOS


def test_cmd_crear_tintura_con_composicion_invalida_no_lanza(capsys):
    args = argparse.Namespace(
        nombre="Amargos Test",
        grupo="amargos",
        composicion="genciana:60,ruibarbo:30",  # suma 90%, no 100%
        parte="raiz",
        abv=70.0,
        ratio=5.0,
        tiempo=18,
        peso_g=500,
        volumen_ml=2500,
        observaciones="",
    )

    # No necesita self.tinturas_repo: el ValueError se lanza antes de
    # llegar a guardar(), así que un stand-in sin base de datos alcanza.
    resultado = FernetOS.cmd_crear_tintura(object(), args)

    assert resultado is None
    assert "inválid" in capsys.readouterr().out
