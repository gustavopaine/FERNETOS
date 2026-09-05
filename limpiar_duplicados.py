#!/usr/bin/env python3
"""
Script para limpiar tinturas duplicadas (opcional)
"""

import sqlite3


def limpiar_duplicados():
    """Elimina tinturas duplicadas manteniendo las más recientes"""

    db_path = "data/fernetos.db"
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    print("🔍 Buscando duplicados...")

    # Encontrar grupos de nombres duplicados
    cursor = conn.execute(
        """
        SELECT nombre, COUNT(*) as count, MIN(id) as primer_id
        FROM tinturas
        GROUP BY nombre
        HAVING count > 1
    """
    )

    duplicados = cursor.fetchall()

    if not duplicados:
        print("✅ No hay duplicados")
        return

    print(f"\n📊 Encontrados {len(duplicados)} grupos de duplicados")

    for dup in duplicados:
        print(f"\n   • {dup['nombre']} ({dup['count']} copias)")

        # Mantener el más reciente (por ID), eliminar los otros
        cursor = conn.execute(
            """
            SELECT id FROM tinturas 
            WHERE nombre = ? 
            ORDER BY id DESC 
            LIMIT ? OFFSET 1
        """,
            (dup["nombre"], dup["count"] - 1),
        )

        a_eliminar = cursor.fetchall()

        for t in a_eliminar:
            print(f"     Eliminando: {t['id']}")
            conn.execute("DELETE FROM tinturas WHERE id = ?", (t["id"],))

    conn.commit()
    print("\n✅ Limpieza completada")
    conn.close()


if __name__ == "__main__":
    limpiar_duplicados()
