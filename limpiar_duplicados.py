#!/usr/bin/env python3
"""
Script para limpiar tinturas duplicadas (opcional)
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from modules.core.db_manager import DatabaseManager
from modules.tinturas.repository_sql import TinturaSQLRepository


def limpiar_duplicados():
    """Elimina tinturas duplicadas manteniendo las más recientes"""

    db = DatabaseManager()
    repo = TinturaSQLRepository(db)

    print("🔍 Buscando duplicados...")

    # Encontrar grupos de nombres duplicados
    duplicados = db.ejecutar(
        """
        SELECT nombre, COUNT(*) as count
        FROM tinturas
        GROUP BY nombre
        HAVING count > 1
        """
    )

    if not duplicados:
        print("✅ No hay duplicados")
        return

    print(f"\n📊 Encontrados {len(duplicados)} grupos de duplicados")

    for dup in duplicados:
        print(f"\n   • {dup['nombre']} ({dup['count']} copias)")

        # Mantener el más reciente (por ID), eliminar los otros
        a_eliminar = db.ejecutar(
            """
            SELECT id FROM tinturas
            WHERE nombre = ?
            ORDER BY id DESC
            LIMIT ? OFFSET 1
            """,
            (dup["nombre"], dup["count"] - 1),
        )

        for t in a_eliminar:
            print(f"     Eliminando: {t['id']}")
            # Vía el repositorio: mismo camino de borrado que usa la app,
            # con PRAGMA foreign_keys activado y cascada real a los hijos.
            repo.eliminar(t["id"])

    print("\n✅ Limpieza completada")


if __name__ == "__main__":
    limpiar_duplicados()
