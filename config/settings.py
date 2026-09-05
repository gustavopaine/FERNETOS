"""
Configuración global del sistema FernetOS.
Carga parámetros desde archivo YAML con defaults.
"""

import os
import yaml
from typing import Dict, Any, Optional
from dataclasses import dataclass, field


@dataclass
class SystemSettings:
    """Configuración del sistema"""

    version: str = "1.0"
    default_alcohol_base: float = 96.0
    default_water_source: str = "osmotizada"


@dataclass
class ParameterRanges:
    """Rangos de parámetros técnicos"""

    abv_ranges: Dict = field(
        default_factory=lambda: {
            "min_final": 38.0,
            "max_final": 42.0,
            "min_tintura": 40.0,
            "max_tintura": 75.0,
        }
    )
    sugar_ranges: Dict = field(
        default_factory=lambda: {"min_gpl": 160, "max_gpl": 220, "default": 195}
    )
    ph_ranges: Dict = field(
        default_factory=lambda: {
            "min_final": 4.8,
            "max_final": 5.6,
            "min_tintura": 4.5,
            "max_tintura": 6.0,
        }
    )


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
class FernetOSConfig:
    """Configuración completa del sistema"""

    system: SystemSettings = field(default_factory=SystemSettings)
    parameters: ParameterRanges = field(default_factory=ParameterRanges)
    scaling: ScalingSettings = field(default_factory=ScalingSettings)
    curves: CurveSettings = field(default_factory=CurveSettings)
    sensory: SensorySettings = field(default_factory=SensorySettings)

    @classmethod
    def from_yaml(cls, yaml_path: str = "config/settings.yaml") -> "FernetOSConfig":
        """Carga configuración desde archivo YAML"""
        config = cls()

        if os.path.exists(yaml_path):
            try:
                with open(yaml_path, "r", encoding="utf-8") as f:
                    data = yaml.safe_load(f)

                # Mapear datos cargados a la estructura
                if data:
                    if "system" in data:
                        for k, v in data["system"].items():
                            if hasattr(config.system, k):
                                setattr(config.system, k, v)

                    # Similar para otras secciones
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
            "abv_ranges": config.parameters.abv_ranges,
            "sugar_ranges": config.parameters.sugar_ranges,
            "ph_ranges": config.parameters.ph_ranges,
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
    }

    with open(yaml_path, "w", encoding="utf-8") as f:
        yaml.dump(data, f, default_flow_style=False, allow_unicode=True)
