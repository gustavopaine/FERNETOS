#!/usr/bin/env python3
"""
Script para verificar la base de datos de FernetOS.
"""

import sqlite3
import os


def check_database():
    """Verifica el contenido de la base de datos"""

    db_path = "data/fernetos.db"

    print("=" * 60)
    print("🔍 VERIFICACIÓN DE BASE DE DATOS FERNETOS")
    print("=" * 60)

    if not os.path.exists(db_path):
        print(f"❌ Base de datos NO encontrada: {db_path}")
        print("\nEjecuta primero: python inicializar_bd_fernet.py")
        return False

    print(f"✅ Base de datos encontrada: {db_path}")
    print(f"📁 Tamaño: {os.path.getsize(db_path) / 1024:.1f} KB")

    # Conectar a la base de datos
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    # Obtener todas las tablas
    cursor = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;"
    )
    tablas = cursor.fetchall()

    print("\n📋 TABLAS EN LA BASE DE DATOS:")
    print("-" * 40)
    for tabla in tablas:
        nombre = tabla[0]
        cursor = conn.execute(f"SELECT COUNT(*) FROM {nombre}")
        count = cursor.fetchone()[0]
        print(f"   • {nombre}: {count} registros")

    # Mostrar tinturas
    cursor = conn.execute(
        """
        SELECT id, nombre, grupo_funcional, estado, volumen_disponible_ml 
        FROM tinturas 
        ORDER BY grupo_funcional
    """
    )
    tinturas = cursor.fetchall()

    print(f"\n🧪 TINTURAS ({len(tinturas)}):")
    print("-" * 80)
    print(f"{'ID':<20} {'NOMBRE':<25} {'GRUPO':<20} {'ESTADO':<12} {'VOLUMEN':<10}")
    print("-" * 80)

    for t in tinturas:
        print(
            f"{t['id']:<20} {t['nombre'][:23]:<25} {t['grupo_funcional']:<20} {t['estado']:<12} {t['volumen_disponible_ml']:>5} ml"
        )

    # Mostrar composición botánica
    cursor = conn.execute(
        """
        SELECT tintura_id, COUNT(*) as especies, SUM(porcentaje) as total_pct
        FROM composicion_botanica
        GROUP BY tintura_id
    """
    )
    composicion = cursor.fetchall()

    print(f"\n🌿 COMPOSICIÓN BOTÁNICA:")
    print("-" * 60)
    for c in composicion:
        print(
            f"   • {c['tintura_id']}: {c['especies']} especies (total {c['total_pct']}%)"
        )

    # Mostrar registros de curva
    cursor = conn.execute(
        """
        SELECT tintura_id, COUNT(*) as catas, MAX(dia) as ultimo_dia
        FROM registros_curva
        GROUP BY tintura_id
    """
    )
    curvas = cursor.fetchall()

    print(f"\n📈 REGISTROS DE CURVA:")
    print("-" * 60)
    for c in curvas:
        print(
            f"   • {c['tintura_id']}: {c['catas']} catas (último día {c['ultimo_dia']})"
        )

    conn.close()

    print("\n" + "=" * 60)
    print("✅ VERIFICACIÓN COMPLETADA")
    print("=" * 60)

    return True


if __name__ == "__main__":
    check_database()
