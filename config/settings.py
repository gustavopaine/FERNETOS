"""
Configuración global del sistema FernetOS.
Carga parámetros desde archivo YAML con defaults.
"""

import os
import yaml
from datetime import datetime
from typing import Dict, Any, Optional
from dataclasses import dataclass, field, fields, is_dataclass

BACKUP_TIMESTAMP_FORMAT = "%d/%m/%Y %H:%M"
FRECUENCIA_A_DIAS = {"diario": 1, "semanal": 7, "mensual": 30}


@dataclass
class SystemSettings:
    """Configuración del sistema"""

    version: str = "1.0"
    default_alcohol_base: float = 96.0
    default_water_source: str = "osmotizada"


@dataclass
class ParameterRanges:
    """Rangos de parámetros técnicos por defecto para nuevos blends"""

    abv_min: float = 38.0
    abv_max: float = 42.0
    abv_default: float = 40.0
    azucar_min: int = 160
    azucar_max: int = 220
    azucar_default: int = 195
    ph_min: float = 4.8
    ph_max: float = 5.6
    ph_default: float = 5.2


@dataclass
class ScalingSettings:
    """Configuración de escalado"""

    base_batch_size: float = 10.0  # litros
    pilot_batch_size: float = 0.5  # 500ml
    industrial_min: float = 100.0  # litros


@dataclass
class CurveSettings:
    """Configuración de análisis de curvas"""

    sampling_frequency_days: int = 2
    optimal_threshold: float = 2.0  # Pendiente mínima para óptimo
    overextraction_warning_days: int = 3  # Días después de óptimo para alertar


@dataclass
class SensorySettings:
    """Configuración de evaluación sensorial"""

    attribute_weights: Dict = field(
        default_factory=lambda: {
            "ataque": 0.2,
            "complejidad": 0.2,
            "equilibrio": 0.25,
            "persistencia": 0.2,
            "amargor": 0.15,
        }
    )


@dataclass
class BackupSettings:
    """Configuración de backup de la base de datos"""

    auto_backup: bool = True
    frecuencia: str = "semanal"  # "diario", "semanal", "mensual"
    ultimo_backup: Optional[str] = None  # "%d/%m/%Y %H:%M"


@dataclass
class GanciaParameterRanges:
    """Rangos de parámetros técnicos por defecto para blends de Gancia"""

    vino_pct_min: float = 0.75
    vino_pct_max: float = 0.80
    vino_pct_default: float = 0.78
    vino_abv_default: float = 12.0
    alcohol_fortificacion_abv_default: float = 96.0
    abv_min: float = 15.0
    abv_max: float = 18.0
    abv_objetivo_default: float = 17.0
    azucar_pct_min: float = 8.0
    azucar_pct_max: float = 12.0
    azucar_pct_default: float = 10.0
    acido_citrico_default_g_l: float = 0.0
    caramelo_default_ml: float = 0.0


@dataclass
class FernetOSConfig:
    """Configuración completa del sistema"""

    system: SystemSettings = field(default_factory=SystemSettings)
    parameters: ParameterRanges = field(default_factory=ParameterRanges)
    scaling: ScalingSettings = field(default_factory=ScalingSettings)
    curves: CurveSettings = field(default_factory=CurveSettings)
    sensory: SensorySettings = field(default_factory=SensorySettings)
    backup: BackupSettings = field(default_factory=BackupSettings)
    gancia: GanciaParameterRanges = field(default_factory=GanciaParameterRanges)

    @classmethod
    def from_yaml(cls, yaml_path: str = "config/settings.yaml") -> "FernetOSConfig":
        """Carga configuración desde archivo YAML"""
        config = cls()

        if os.path.exists(yaml_path):
            try:
                with open(yaml_path, "r", encoding="utf-8") as f:
                    data = yaml.safe_load(f)

                # Mapear cada sección presente en el YAML a su dataclass
                # correspondiente (system, parameters, scaling, curves,
                # sensory, backup comparten esta misma forma: atributos
                # planos o dict, uno a uno por nombre).
                if data:
                    for seccion in fields(config):
                        valores = data.get(seccion.name)
                        destino = getattr(config, seccion.name)
                        if valores and is_dataclass(destino):
                            for k, v in valores.items():
                                if hasattr(destino, k):
                                    setattr(destino, k, v)
            except Exception as e:
                print(f"Error cargando configuración: {e}")

        return config


# Configuración global
_settings = None


def load_settings() -> FernetOSConfig:
    """Carga la configuración (singleton)"""
    global _settings
    if _settings is None:
        _settings = FernetOSConfig.from_yaml()
    return _settings


def save_settings(config: FernetOSConfig, yaml_path: str = "config/settings.yaml"):
    """Guarda configuración en archivo YAML"""
    os.makedirs(os.path.dirname(yaml_path), exist_ok=True)

    data = {
        "system": {
            "version": config.system.version,
            "default_alcohol_base": config.system.default_alcohol_base,
            "default_water_source": config.system.default_water_source,
        },
        "parameters": {
            "abv_min": config.parameters.abv_min,
            "abv_max": config.parameters.abv_max,
            "abv_default": config.parameters.abv_default,
            "azucar_min": config.parameters.azucar_min,
            "azucar_max": config.parameters.azucar_max,
            "azucar_default": config.parameters.azucar_default,
            "ph_min": config.parameters.ph_min,
            "ph_max": config.parameters.ph_max,
            "ph_default": config.parameters.ph_default,
        },
        "scaling": {
            "base_batch_size": config.scaling.base_batch_size,
            "pilot_batch_size": config.scaling.pilot_batch_size,
            "industrial_min": config.scaling.industrial_min,
        },
        "curves": {
            "sampling_frequency_days": config.curves.sampling_frequency_days,
            "optimal_threshold": config.curves.optimal_threshold,
            "overextraction_warning_days": config.curves.overextraction_warning_days,
        },
        "sensory": {"attribute_weights": config.sensory.attribute_weights},
        "backup": {
            "auto_backup": config.backup.auto_backup,
            "frecuencia": config.backup.frecuencia,
            "ultimo_backup": config.backup.ultimo_backup,
        },
        "gancia": {
            "vino_pct_min": config.gancia.vino_pct_min,
            "vino_pct_max": config.gancia.vino_pct_max,
            "vino_pct_default": config.gancia.vino_pct_default,
            "vino_abv_default": config.gancia.vino_abv_default,
            "alcohol_fortificacion_abv_default": config.gancia.alcohol_fortificacion_abv_default,
            "abv_min": config.gancia.abv_min,
            "abv_max": config.gancia.abv_max,
            "abv_objetivo_default": config.gancia.abv_objetivo_default,
            "azucar_pct_min": config.gancia.azucar_pct_min,
            "azucar_pct_max": config.gancia.azucar_pct_max,
            "azucar_pct_default": config.gancia.azucar_pct_default,
            "acido_citrico_default_g_l": config.gancia.acido_citrico_default_g_l,
            "caramelo_default_ml": config.gancia.caramelo_default_ml,
        },
    }

    with open(yaml_path, "w", encoding="utf-8") as f:
        yaml.dump(data, f, default_flow_style=False, allow_unicode=True)


def backup_es_necesario(backup: BackupSettings, ahora: datetime) -> bool:
    """Decide si corresponde disparar un backup automático.

    Nunca se hizo backup, o el formato guardado es inválido -> hace falta uno.
    Frecuencia desconocida cae al valor semanal por seguridad.
    """
    if not backup.auto_backup:
        return False

    if not backup.ultimo_backup:
        return True

    try:
        ultimo = datetime.strptime(backup.ultimo_backup, BACKUP_TIMESTAMP_FORMAT)
    except ValueError:
        return True

    dias_frecuencia = FRECUENCIA_A_DIAS.get(backup.frecuencia, 7)
    return (ahora - ultimo).days >= dias_frecuencia
