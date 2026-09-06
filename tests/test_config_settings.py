"""Tests para config/settings.py: round-trip completo de persistencia YAML."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.settings import FernetOSConfig, save_settings


def test_roundtrip_conserva_todas_las_secciones(tmp_path):
    yaml_path = str(tmp_path / "settings.yaml")

    config = FernetOSConfig()
    config.system.default_alcohol_base = 95.5
    config.parameters.abv_max = 43.0
    config.scaling.base_batch_size = 20.0
    config.curves.optimal_threshold = 3.5
    config.sensory.attribute_weights["amargor"] = 0.30
    config.backup.auto_backup = False
    config.backup.frecuencia = "diario"
    config.backup.ultimo_backup = "01/09/2026 10:00"

    save_settings(config, yaml_path)
    recargado = FernetOSConfig.from_yaml(yaml_path)

    assert recargado.system.default_alcohol_base == 95.5
    assert recargado.parameters.abv_max == 43.0
    assert recargado.scaling.base_batch_size == 20.0
    assert recargado.curves.optimal_threshold == 3.5
    assert recargado.sensory.attribute_weights["amargor"] == 0.30
    assert recargado.backup.auto_backup is False
    assert recargado.backup.frecuencia == "diario"
    assert recargado.backup.ultimo_backup == "01/09/2026 10:00"


def test_from_yaml_sin_archivo_usa_defaults(tmp_path):
    config = FernetOSConfig.from_yaml(str(tmp_path / "no_existe.yaml"))

    assert config.system.default_alcohol_base == 96.0
    assert config.backup.auto_backup is True
    assert config.backup.frecuencia == "semanal"
