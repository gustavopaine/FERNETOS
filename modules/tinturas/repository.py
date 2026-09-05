# -*- coding: utf-8 -*-
# Archivo en desarrollo
# M�dulo: repository.py

"""
Repositorio para gestión de tinturas en base de datos.
"""

import json
import os
from typing import Dict, List, Optional
from datetime import datetime

from modules.tinturas.models import Tintura


class TinturaRepository:
    """Repositorio simple basado en archivos JSON"""

    def __init__(self, data_dir: str = "data/tinturas"):
        self.data_dir = data_dir
        os.makedirs(data_dir, exist_ok=True)
        self.cache: Dict[str, Tintura] = {}
        self._cargar_todas()

    def _cargar_todas(self):
        """Carga todas las tinturas desde archivos"""
        for filename in os.listdir(self.data_dir):
            if filename.endswith(".json"):
                filepath = os.path.join(self.data_dir, filename)
                with open(filepath, "r") as f:
                    data = json.load(f)
                    # Aquí habría que reconstruir el objeto Tintura
                    # Por simplicidad, solo guardamos ID
                    self.cache[data.get("id", filename)] = None

    def guardar(self, tintura: Tintura) -> str:
        """Guarda una tintura en archivo"""
        filepath = os.path.join(self.data_dir, f"{tintura.id}.json")
        with open(filepath, "w") as f:
            json.dump(tintura.to_dict(), f, indent=2, default=str)
        self.cache[tintura.id] = tintura
        return tintura.id

    def get_by_id(self, tintura_id: str) -> Optional[Tintura]:
        """Obtiene una tintura por ID"""
        if tintura_id in self.cache and self.cache[tintura_id]:
            return self.cache[tintura_id]

        filepath = os.path.join(self.data_dir, f"{tintura_id}.json")
        if os.path.exists(filepath):
            with open(filepath, "r") as f:
                data = json.load(f)
                # Simplificado - en implementación real habría que reconstruir
                tintura = Tintura()
                tintura.id = data.get("id", tintura_id)
                tintura.nombre = data.get("nombre", "")
                self.cache[tintura_id] = tintura
                return tintura

        return None

    def actualizar(self, tintura: Tintura):
        """Actualiza una tintura existente"""
        self.guardar(tintura)
