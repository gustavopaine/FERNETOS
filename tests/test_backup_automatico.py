"""Tests para la lógica de decisión de backup automático (config/settings.py)."""

import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.settings import BackupSettings, backup_es_necesario


def test_no_hace_backup_si_auto_backup_desactivado():
    backup = BackupSettings(auto_backup=False, ultimo_backup=None)
    assert backup_es_necesario(backup, datetime(2026, 9, 5)) is False


def test_hace_backup_si_nunca_se_hizo_uno():
    backup = BackupSettings(auto_backup=True, ultimo_backup=None)
    assert backup_es_necesario(backup, datetime(2026, 9, 5)) is True


def test_no_hace_backup_si_frecuencia_semanal_no_vencio():
    backup = BackupSettings(
        auto_backup=True, frecuencia="semanal", ultimo_backup="01/09/2026 10:00"
    )
    assert backup_es_necesario(backup, datetime(2026, 9, 5, 10, 0)) is False


def test_hace_backup_si_frecuencia_semanal_vencio():
    backup = BackupSettings(
        auto_backup=True, frecuencia="semanal", ultimo_backup="01/09/2026 10:00"
    )
    assert backup_es_necesario(backup, datetime(2026, 9, 9, 10, 0)) is True


def test_frecuencia_diaria_vence_en_un_dia():
    backup = BackupSettings(
        auto_backup=True, frecuencia="diario", ultimo_backup="04/09/2026 10:00"
    )
    assert backup_es_necesario(backup, datetime(2026, 9, 5, 12, 0)) is True


def test_ultimo_backup_con_formato_invalido_dispara_backup():
    backup = BackupSettings(auto_backup=True, ultimo_backup="fecha-invalida")
    assert backup_es_necesario(backup, datetime(2026, 9, 5)) is True
