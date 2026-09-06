"""Tests para modules/core/db_manager.py"""

import os
import sqlite3
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest

from modules.core.db_manager import DatabaseManager


@pytest.fixture
def db(tmp_path):
    db_path = str(tmp_path / "test.db")
    schema_path = str(tmp_path / "schema" / "schema.sql")
    return DatabaseManager(db_path=db_path, schema_path=schema_path)


def test_crea_esquema_con_tablas_requeridas(db):
    with db.get_connection() as conn:
        cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tablas = {row[0] for row in cursor.fetchall()}

    for requerida in (
        "tinturas",
        "composicion_botanica",
        "parametros_extraccion",
        "registros_curva",
        "compuestos_detectados",
    ):
        assert requerida in tablas


def test_foreign_keys_activadas_por_conexion(db):
    with db.get_connection() as conn:
        fk_status = conn.execute("PRAGMA foreign_keys").fetchone()[0]
    assert fk_status == 1


def _crear_tintura_con_hijos(db, tintura_id="T-TEST-0001"):
    db.insertar(
        "tinturas",
        {
            "id": tintura_id,
            "nombre": "Amargos Test",
            "grupo_funcional": "amargos_estructurales",
            "peso_materia_seca_g": 100,
            "volumen_alcohol_ml": 500,
            "fecha_inicio": "2026-01-01T00:00:00",
        },
    )
    db.insertar(
        "composicion_botanica",
        {
            "tintura_id": tintura_id,
            "especie": "genciana",
            "porcentaje": 100,
            "parte_utilizada": "raiz",
        },
    )
    db.insertar(
        "parametros_extraccion",
        {
            "tintura_id": tintura_id,
            "abv_objetivo": 70.0,
            "ratio_planta_alcohol": 0.2,
            "tiempo_estimado_dias": 18,
        },
    )
    registro_id = db.insertar(
        "registros_curva",
        {
            "tintura_id": tintura_id,
            "dia": 1,
            "fecha": "2026-01-02T00:00:00",
            "intensidad": 20,
        },
    )
    db.insertar(
        "compuestos_detectados",
        {"registro_id": registro_id, "compuesto": "taninos"},
    )


def test_migra_columna_producto_en_bd_preexistente_sin_perder_filas(tmp_path):
    """Simula una BD creada antes de la Fase 2 (sin la columna producto),
    como la instalación real del usuario con 7 tinturas ya guardadas."""
    db_path = str(tmp_path / "vieja.db")
    conn = sqlite3.connect(db_path)
    conn.execute(
        """
        CREATE TABLE tinturas (
            id TEXT PRIMARY KEY,
            nombre TEXT NOT NULL,
            grupo_funcional TEXT NOT NULL,
            version TEXT DEFAULT '1.0.0',
            peso_materia_seca_g REAL NOT NULL,
            volumen_alcohol_ml REAL NOT NULL,
            fecha_inicio TEXT NOT NULL,
            estado TEXT DEFAULT 'en_maceracion'
        )
        """
    )
    conn.execute(
        "INSERT INTO tinturas (id, nombre, grupo_funcional, peso_materia_seca_g, "
        "volumen_alcohol_ml, fecha_inicio) VALUES (?, ?, ?, ?, ?, ?)",
        ("T-OLD-0001", "Amargos Viejo", "amargos_estructurales", 500, 2500, "2026-01-01"),
    )
    conn.commit()
    conn.close()

    db = DatabaseManager(db_path=db_path, schema_path=str(tmp_path / "schema" / "schema.sql"))

    filas = db.ejecutar("SELECT id, nombre, producto FROM tinturas")
    assert filas == [{"id": "T-OLD-0001", "nombre": "Amargos Viejo", "producto": "fernet"}]


def test_eliminar_filas_retorna_cantidad_afectada(db):
    _crear_tintura_con_hijos(db, "T-TEST-0002")

    filas = db.eliminar_filas("tinturas", "id = ?", ("T-TEST-0002",))

    assert filas == 1
    assert db.eliminar_filas("tinturas", "id = ?", ("no-existe",)) == 0


def test_borrar_tintura_elimina_hijos_por_cascada(db):
    tintura_id = "T-TEST-0001"
    _crear_tintura_con_hijos(db, tintura_id)

    db.ejecutar("DELETE FROM tinturas WHERE id = ?", (tintura_id,))

    assert db.ejecutar(
        "SELECT * FROM composicion_botanica WHERE tintura_id = ?", (tintura_id,)
    ) == []
    assert db.ejecutar(
        "SELECT * FROM parametros_extraccion WHERE tintura_id = ?", (tintura_id,)
    ) == []
    assert db.ejecutar(
        "SELECT * FROM registros_curva WHERE tintura_id = ?", (tintura_id,)
    ) == []
    assert db.ejecutar(
        """SELECT cd.* FROM compuestos_detectados cd
           LEFT JOIN registros_curva rc ON cd.registro_id = rc.id
           WHERE rc.id IS NULL"""
    ) == []
