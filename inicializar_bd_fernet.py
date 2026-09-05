#!/usr/bin/env python3
"""
Script completo para inicializar la base de datos de FernetOS con todas las tinturas
necesarias para preparar un fernet competitivo.
"""

import sys
import os
from datetime import datetime, timedelta

# Asegurar que Python encuentra los módulos
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from modules.core.db_manager import DatabaseManager
from modules.tinturas.repository_sql import TinturaSQLRepository
from modules.tinturas.models import (
    Tintura,
    GrupoFuncional,
    ComposicionBotanica,
    ParametrosExtraccion,
    RegistroExtraccion,
    EstadoTintura,
    ControlCalidad,
)


def crear_tinturas_fernet_competitivo():
    """
    Crea todas las tinturas necesarias para un fernet competitivo,
    siguiendo la arquitectura modular optimizada.
    """

    print("=" * 70)
    print("🌿 FERNETOS - INICIALIZACIÓN DE BASE DE DATOS")
    print("=" * 70)
    print("\n📦 Creando tinturas para fernet competitivo...")

    # Inicializar base de datos
    db = DatabaseManager()
    repo = TinturaSQLRepository(db)

    todas_tinturas = []

    # =========================================================
    # 1. TINTURA DE AMARGOS ESTRUCTURALES (OPTIMIZADA)
    # =========================================================
    print("\n" + "-" * 50)
    print("1️⃣  TINTURA DE AMARGOS ESTRUCTURALES")
    print("-" * 50)

    amargos = Tintura(
        nombre="Amargos Estructurales Premium",
        grupo_funcional=GrupoFuncional.AMARGOS_ESTRUCTURALES,
        composicion=[
            ComposicionBotanica(
                especie="genciana",
                porcentaje=55,
                parte_utilizada="raiz",
                lote_origen="GEN-2026-001",
            ),
            ComposicionBotanica(
                especie="ruibarbo",
                porcentaje=35,
                parte_utilizada="raiz",
                lote_origen="RUI-2026-001",
            ),
            ComposicionBotanica(
                especie="quina",
                porcentaje=5,
                parte_utilizada="corteza",
                lote_origen="QUI-2026-001",
            ),
            ComposicionBotanica(
                especie="angelica",
                porcentaje=5,
                parte_utilizada="raiz",
                lote_origen="ANG-2026-001",
            ),
        ],
        peso_total_materia_seca_g=500,
        volumen_alcohol_ml=2500,  # 2.5L (ratio 1:5)
        parametros=ParametrosExtraccion(
            abv_objetivo=70.0,
            ratio_planta_alcohol=0.2,
            temperatura_maceracion=20.0,
            agitacion_diaria=True,
            tiempo_estimado_dias=18,
            proteccion_luz=True,
            recipiente_material="vidrio",
        ),
        observaciones_iniciales="Tintura base de amargos optimizada para competencia. Proporciones: G55/R35/Q5/A5",
    )

    # Simular registros de curva (días 2,4,6,8,10,12,14,16,18)
    registros_amargos = [
        (2, 15, ["glucosidos_ligeros"], "ambar_claro", "claro", "Aroma herbal suave"),
        (
            4,
            35,
            ["glucosidos", "taninos_ligeros"],
            "ambar",
            "claro",
            "Comienza a aparecer amargor",
        ),
        (
            6,
            55,
            ["glucosidos", "taninos"],
            "ambar",
            "ligera",
            "Amargor definido, taninos suaves",
        ),
        (
            8,
            72,
            ["glucosidos", "taninos", "resinas"],
            "ambar_oscuro",
            "ligera",
            "Punto óptimo de amargor",
        ),
        (
            10,
            82,
            ["glucosidos", "taninos", "resinas"],
            "ambar_oscuro",
            "ligera",
            "Amargor profundo",
        ),
        (
            12,
            88,
            ["glucosidos", "taninos", "resinas"],
            "miel",
            "claro",
            "Máxima expresión de amargor",
        ),
        (
            14,
            92,
            ["glucosidos", "taninos", "resinas"],
            "miel_oscuro",
            "claro",
            "Muy estable",
        ),
        (
            16,
            94,
            ["glucosidos", "taninos", "resinas"],
            "caoba",
            "claro",
            "Punto óptimo - DÍA DE CORTE",
        ),
        (
            18,
            95,
            ["glucosidos", "taninos", "resinas", "terrosos_ligeros"],
            "caoba",
            "claro",
            "Inicio de notas terrosas",
        ),
    ]

    for dia, intensidad, compuestos, color, turbidez, aroma in registros_amargos:
        registro = RegistroExtraccion(
            dia=dia,
            fecha=datetime.now() - timedelta(days=(18 - dia)),
            intensidad_estimada=intensidad,
            notas_sensoriales=f"Día {dia}: {aroma}",
            compuestos_detectados=compuestos,
            color=color,
            turbidez=turbidez,
            aroma_descripcion=aroma,
            momento_optimo_candidato=(dia == 16),
        )
        amargos.agregar_registro_extraccion(registro)

    # Finalizar y estabilizar
    amargos.finalizar_maceracion(datetime.now() - timedelta(days=2))
    amargos.estabilizar(dias_estabilizacion=15, temperatura=5)
    amargos.control_calidad = ControlCalidad(
        ph=5.5, densidad=0.98, alcohol_medido=69.8, rendimiento_volumen_ml=2400
    )
    amargos.marcar_como_lista(volumen_final_ml=2400)
    amargos.ubicacion_almacen = "Estante A1"

    repo.guardar(amargos)
    todas_tinturas.append(amargos)
    print(f"   ✅ Amargos: {amargos.id} - {amargos.nombre}")
    print(
        f"      Volumen: {amargos.volumen_disponible_ml} ml | ABV: {amargos.parametros.abv_objetivo}%"
    )

    # =========================================================
    # 2. TINTURA AROMÁTICA ALTA
    # =========================================================
    print("\n" + "-" * 50)
    print("2️⃣  TINTURA AROMÁTICA ALTA")
    print("-" * 50)

    aromatica = Tintura(
        nombre="Aromática Alta Premium",
        grupo_funcional=GrupoFuncional.AROMATICA_ALTA,
        composicion=[
            ComposicionBotanica(
                especie="cardo_mariano",
                porcentaje=40,
                parte_utilizada="hoja",
                lote_origen="CAR-2026-001",
            ),
            ComposicionBotanica(
                especie="menta_piperita",
                porcentaje=30,
                parte_utilizada="hoja",
                lote_origen="MEN-2026-001",
            ),
            ComposicionBotanica(
                especie="romero",
                porcentaje=20,
                parte_utilizada="hoja",
                lote_origen="ROM-2026-001",
            ),
            ComposicionBotanica(
                especie="azafran",
                porcentaje=10,
                parte_utilizada="estigma",
                lote_origen="AZA-2026-001",
            ),
        ],
        peso_total_materia_seca_g=400,
        volumen_alcohol_ml=2000,  # 2L
        parametros=ParametrosExtraccion(
            abv_objetivo=55.0,
            ratio_planta_alcohol=0.2,
            temperatura_maceracion=18.0,
            agitacion_diaria=True,
            tiempo_estimado_dias=7,
            proteccion_luz=True,
            recipiente_material="vidrio",
        ),
        observaciones_iniciales="Tintura aromática base para perfil herbal fresco",
    )

    # Simular registros de curva (días 1,3,5,7)
    registros_aromatica = [
        (1, 25, ["terpenos_volatiles"], "verde_claro", "claro", "Aroma fresco intenso"),
        (
            3,
            58,
            ["terpenos_volatiles", "clorofila_ligera"],
            "verde",
            "ligera",
            "Notas herbales definidas",
        ),
        (
            5,
            82,
            ["terpenos", "clorofila"],
            "verde_oscuro",
            "ligera",
            "PUNTO ÓPTIMO - Máximo aroma",
        ),
        (
            7,
            88,
            ["terpenos", "clorofila", "herbaceos"],
            "verde_oscuro",
            "media",
            "Inicio de notas a pasto",
        ),
    ]

    for dia, intensidad, compuestos, color, turbidez, aroma in registros_aromatica:
        registro = RegistroExtraccion(
            dia=dia,
            fecha=datetime.now() - timedelta(days=(7 - dia)),
            intensidad_estimada=intensidad,
            notas_sensoriales=f"Día {dia}: {aroma}",
            compuestos_detectados=compuestos,
            color=color,
            turbidez=turbidez,
            aroma_descripcion=aroma,
            momento_optimo_candidato=(dia == 5),
        )
        aromatica.agregar_registro_extraccion(registro)

    # Finalizar y estabilizar
    aromatica.finalizar_maceracion(datetime.now() - timedelta(days=5))
    aromatica.estabilizar(dias_estabilizacion=10, temperatura=5)
    aromatica.control_calidad = ControlCalidad(
        ph=5.8, densidad=0.96, alcohol_medido=54.8, rendimiento_volumen_ml=1900
    )
    aromatica.marcar_como_lista(volumen_final_ml=1900)
    aromatica.ubicacion_almacen = "Estante B2"

    repo.guardar(aromatica)
    todas_tinturas.append(aromatica)
    print(f"   ✅ Aromática: {aromatica.id} - {aromatica.nombre}")
    print(
        f"      Volumen: {aromatica.volumen_disponible_ml} ml | ABV: {aromatica.parametros.abv_objetivo}%"
    )

    # =========================================================
    # 3. TINTURA AROMÁTICA DE ALTO IMPACTO (SPLIT - 48h)
    # =========================================================
    print("\n" + "-" * 50)
    print("3️⃣  TINTURA AROMÁTICA DE ALTO IMPACTO (48h)")
    print("-" * 50)

    aromatica_alto_impacto = Tintura(
        nombre="Aromática Alto Impacto - 48h",
        grupo_funcional=GrupoFuncional.AROMATICA_ALTA,
        composicion=[
            ComposicionBotanica(
                especie="limon_cascara",
                porcentaje=50,
                parte_utilizada="cascara_seca",
                lote_origen="LIM-2026-001",
            ),
            ComposicionBotanica(
                especie="menta_piperita",
                porcentaje=30,
                parte_utilizada="hoja",
                lote_origen="MEN-2026-002",
            ),
            ComposicionBotanica(
                especie="azafran",
                porcentaje=20,
                parte_utilizada="estigma",
                lote_origen="AZA-2026-002",
            ),
        ],
        peso_total_materia_seca_g=200,
        volumen_alcohol_ml=1000,  # 1L
        parametros=ParametrosExtraccion(
            abv_objetivo=75.0,  # Alcohol más alto para extracción rápida
            ratio_planta_alcohol=0.2,
            temperatura_maceracion=18.0,
            agitacion_diaria=True,
            tiempo_estimado_dias=2,
            proteccion_luz=True,
            recipiente_material="vidrio",
        ),
        observaciones_iniciales="Tintura de alto impacto para ataque inicial. Maceración ultra-corta.",
    )

    # Simular registros de curva (días 1,2)
    registros_alto_impacto = [
        (
            1,
            40,
            ["aceites_esenciales", "limoneno"],
            "amarillo_claro",
            "claro",
            "Aroma cítrico intenso",
        ),
        (
            2,
            72,
            ["aceites_esenciales", "limoneno", "mentol"],
            "amarillo",
            "claro",
            "PUNTO ÓPTIMO - Lista para filtrar",
        ),
    ]

    for dia, intensidad, compuestos, color, turbidez, aroma in registros_alto_impacto:
        registro = RegistroExtraccion(
            dia=dia,
            fecha=datetime.now() - timedelta(days=(2 - dia)),
            intensidad_estimada=intensidad,
            notas_sensoriales=f"Día {dia}: {aroma}",
            compuestos_detectados=compuestos,
            color=color,
            turbidez=turbidez,
            aroma_descripcion=aroma,
            momento_optimo_candidato=(dia == 2),
        )
        aromatica_alto_impacto.agregar_registro_extraccion(registro)

    # Finalizar y estabilizar (menos tiempo por ser volátil)
    aromatica_alto_impacto.finalizar_maceracion(datetime.now() - timedelta(days=1))
    aromatica_alto_impacto.estabilizar(dias_estabilizacion=5, temperatura=5)
    aromatica_alto_impacto.control_calidad = ControlCalidad(
        ph=4.9, densidad=0.92, alcohol_medido=74.5, rendimiento_volumen_ml=950
    )
    aromatica_alto_impacto.marcar_como_lista(volumen_final_ml=950)
    aromatica_alto_impacto.ubicacion_almacen = "Estante B3"

    repo.guardar(aromatica_alto_impacto)
    todas_tinturas.append(aromatica_alto_impacto)
    print(
        f"   ✅ Alto Impacto: {aromatica_alto_impacto.id} - {aromatica_alto_impacto.nombre}"
    )
    print(
        f"      Volumen: {aromatica_alto_impacto.volumen_disponible_ml} ml | ABV: {aromatica_alto_impacto.parametros.abv_objetivo}%"
    )

    # =========================================================
    # 4. TINTURA DE ESPECIAS CÁLIDAS
    # =========================================================
    print("\n" + "-" * 50)
    print("4️⃣  TINTURA DE ESPECIAS CÁLIDAS")
    print("-" * 50)

    especias = Tintura(
        nombre="Especias Cálidas Premium",
        grupo_funcional=GrupoFuncional.ESPECIAS_CALIDAS,
        composicion=[
            ComposicionBotanica(
                especie="canela_ceylon",
                porcentaje=55,
                parte_utilizada="corteza",
                lote_origen="CAN-2026-001",
            ),
            ComposicionBotanica(
                especie="cardamomo",
                porcentaje=25,
                parte_utilizada="semilla",
                lote_origen="CARD-2026-001",
            ),
            ComposicionBotanica(
                especie="clavo",
                porcentaje=5,
                parte_utilizada="cogollo",
                lote_origen="CLA-2026-001",
            ),
            ComposicionBotanica(
                especie="nuez_moscada",
                porcentaje=15,
                parte_utilizada="semilla",
                lote_origen="NUE-2026-001",
            ),
        ],
        peso_total_materia_seca_g=300,
        volumen_alcohol_ml=1500,  # 1.5L
        parametros=ParametrosExtraccion(
            abv_objetivo=65.0,
            ratio_planta_alcohol=0.2,
            temperatura_maceracion=20.0,
            agitacion_diaria=True,
            tiempo_estimado_dias=14,
            proteccion_luz=True,
            recipiente_material="vidrio",
        ),
        observaciones_iniciales="Tintura base de especias con clavo controlado (5%)",
    )

    # Simular registros de curva (días 2,4,6,8,10,12,14)
    registros_especias = [
        (2, 20, ["aceites_esenciales"], "ambar_claro", "claro", "Aroma dulce inicial"),
        (
            4,
            42,
            ["aceites_esenciales", "eugenol_ligero"],
            "ambar",
            "claro",
            "Aparece clavo",
        ),
        (
            6,
            63,
            ["aceites_esenciales", "eugenol"],
            "ambar",
            "ligera",
            "Notas especiadas definidas",
        ),
        (
            8,
            78,
            ["aceites_esenciales", "eugenol", "resinas"],
            "ambar_oscuro",
            "ligera",
            "Excelente balance",
        ),
        (
            10,
            86,
            ["resinas", "taninos"],
            "miel",
            "claro",
            "PUNTO ÓPTIMO - Complejidad máxima",
        ),
        (12, 90, ["resinas", "taninos"], "miel_oscuro", "claro", "Muy estable"),
        (
            14,
            91,
            ["resinas", "taninos", "leñoso"],
            "caoba",
            "claro",
            "Inicio de notas leñosas",
        ),
    ]

    for dia, intensidad, compuestos, color, turbidez, aroma in registros_especias:
        registro = RegistroExtraccion(
            dia=dia,
            fecha=datetime.now() - timedelta(days=(14 - dia)),
            intensidad_estimada=intensidad,
            notas_sensoriales=f"Día {dia}: {aroma}",
            compuestos_detectados=compuestos,
            color=color,
            turbidez=turbidez,
            aroma_descripcion=aroma,
            momento_optimo_candidato=(dia == 10),
        )
        especias.agregar_registro_extraccion(registro)

    # Finalizar y estabilizar
    especias.finalizar_maceracion(datetime.now() - timedelta(days=4))
    especias.estabilizar(dias_estabilizacion=12, temperatura=5)
    especias.control_calidad = ControlCalidad(
        ph=5.2, densidad=0.97, alcohol_medido=64.7, rendimiento_volumen_ml=1450
    )
    especias.marcar_como_lista(volumen_final_ml=1450)
    especias.ubicacion_almacen = "Estante C1"

    repo.guardar(especias)
    todas_tinturas.append(especias)
    print(f"   ✅ Especias: {especias.id} - {especias.nombre}")
    print(
        f"      Volumen: {especias.volumen_disponible_ml} ml | ABV: {especias.parametros.abv_objetivo}%"
    )

    # =========================================================
    # 5. TINTURA DE CLAVO CONTROLADO (48h - PARA MICRODOSIS)
    # =========================================================
    print("\n" + "-" * 50)
    print("5️⃣  TINTURA DE CLAVO CONTROLADO (48h)")
    print("-" * 50)

    clavo = Tintura(
        nombre="Clavo Controlado - 48h",
        grupo_funcional=GrupoFuncional.ESPECIAS_CALIDAS,
        composicion=[
            ComposicionBotanica(
                especie="clavo",
                porcentaje=100,
                parte_utilizada="cogollo",
                lote_origen="CLA-2026-002",
            )
        ],
        peso_total_materia_seca_g=50,
        volumen_alcohol_ml=500,  # 0.5L
        parametros=ParametrosExtraccion(
            abv_objetivo=65.0,
            ratio_planta_alcohol=0.1,  # 1:10 (más diluida para control)
            temperatura_maceracion=20.0,
            agitacion_diaria=True,
            tiempo_estimado_dias=2,
            proteccion_luz=True,
            recipiente_material="vidrio",
        ),
        observaciones_iniciales="Tintura de clavo para microdosificación. Maceración ultra-corta para evitar dominancia.",
    )

    # Simular registros de curva (días 1,2)
    registros_clavo = [
        (1, 35, ["eugenol_ligero"], "ambar_claro", "claro", "Aroma a clavo suave"),
        (
            2,
            68,
            ["eugenol"],
            "ambar",
            "claro",
            "PUNTO ÓPTIMO - Clavo definido no dominante",
        ),
    ]

    for dia, intensidad, compuestos, color, turbidez, aroma in registros_clavo:
        registro = RegistroExtraccion(
            dia=dia,
            fecha=datetime.now() - timedelta(days=(2 - dia)),
            intensidad_estimada=intensidad,
            notas_sensoriales=f"Día {dia}: {aroma}",
            compuestos_detectados=compuestos,
            color=color,
            turbidez=turbidez,
            aroma_descripcion=aroma,
            momento_optimo_candidato=(dia == 2),
        )
        clavo.agregar_registro_extraccion(registro)

    # Finalizar y estabilizar
    clavo.finalizar_maceracion(datetime.now() - timedelta(days=1))
    clavo.estabilizar(dias_estabilizacion=7, temperatura=5)
    clavo.control_calidad = ControlCalidad(
        ph=5.0, densidad=0.95, alcohol_medido=64.5, rendimiento_volumen_ml=480
    )
    clavo.marcar_como_lista(volumen_final_ml=480)
    clavo.ubicacion_almacen = "Estante C2"

    repo.guardar(clavo)
    todas_tinturas.append(clavo)
    print(f"   ✅ Clavo controlado: {clavo.id} - {clavo.nombre}")
    print(
        f"      Volumen: {clavo.volumen_disponible_ml} ml | ABV: {clavo.parametros.abv_objetivo}%"
    )

    # =========================================================
    # 6. TINTURA CÍTRICA
    # =========================================================
    print("\n" + "-" * 50)
    print("6️⃣  TINTURA CÍTRICA")
    print("-" * 50)

    citricos = Tintura(
        nombre="Cítricos Premium",
        grupo_funcional=GrupoFuncional.CITRICOS,
        composicion=[
            ComposicionBotanica(
                especie="naranja_amarga",
                porcentaje=60,
                parte_utilizada="cascara_seca",
                lote_origen="NAR-2026-001",
            ),
            ComposicionBotanica(
                especie="limon",
                porcentaje=40,
                parte_utilizada="cascara_seca",
                lote_origen="LIM-2026-002",
            ),
        ],
        peso_total_materia_seca_g=300,
        volumen_alcohol_ml=1500,  # 1.5L
        parametros=ParametrosExtraccion(
            abv_objetivo=75.0,
            ratio_planta_alcohol=0.2,
            temperatura_maceracion=18.0,
            agitacion_diaria=True,
            tiempo_estimado_dias=4,
            proteccion_luz=True,
            recipiente_material="vidrio",
        ),
        observaciones_iniciales="Tintura cítrica con cold crash para estabilidad",
    )

    # Simular registros de curva (días 1,2,3,4)
    registros_citricos = [
        (
            1,
            40,
            ["limoneno", "aceites_esenciales"],
            "amarillo_claro",
            "claro",
            "Aroma cítrico fresco",
        ),
        (
            2,
            72,
            ["limoneno", "aceites_esenciales"],
            "amarillo",
            "ligera",
            "Notas brillantes",
        ),
        (
            3,
            85,
            ["limoneno", "aceites_esenciales", "terpenos"],
            "amarillo_oscuro",
            "media",
            "PUNTO ÓPTIMO - Máximo aroma",
        ),
        (
            4,
            88,
            ["limoneno", "terpenos", "ceras"],
            "ambar",
            "alta",
            "Inicio de extracción de ceras",
        ),
    ]

    for dia, intensidad, compuestos, color, turbidez, aroma in registros_citricos:
        registro = RegistroExtraccion(
            dia=dia,
            fecha=datetime.now() - timedelta(days=(4 - dia)),
            intensidad_estimada=intensidad,
            notas_sensoriales=f"Día {dia}: {aroma}",
            compuestos_detectados=compuestos,
            color=color,
            turbidez=turbidez,
            aroma_descripcion=aroma,
            momento_optimo_candidato=(dia == 3),
        )
        citricos.agregar_registro_extraccion(registro)

    # Finalizar y estabilizar
    citricos.finalizar_maceracion(datetime.now() - timedelta(days=3))
    citricos.estabilizar(dias_estabilizacion=10, temperatura=5)
    citricos.control_calidad = ControlCalidad(
        ph=4.8, densidad=0.93, alcohol_medido=74.2, rendimiento_volumen_ml=1420
    )
    citricos.marcar_como_lista(volumen_final_ml=1420)
    citricos.ubicacion_almacen = "Estante D1"

    repo.guardar(citricos)
    todas_tinturas.append(citricos)
    print(f"   ✅ Cítricos: {citricos.id} - {citricos.nombre}")
    print(
        f"      Volumen: {citricos.volumen_disponible_ml} ml | ABV: {citricos.parametros.abv_objetivo}%"
    )

    # =========================================================
    # 7. TINTURA CORRECTIVA DE REGALIZ
    # =========================================================
    print("\n" + "-" * 50)
    print("7️⃣  TINTURA CORRECTIVA DE REGALIZ")
    print("-" * 50)

    regaliz = Tintura(
        nombre="Regaliz Correctivo",
        grupo_funcional=GrupoFuncional.CORRECTIVOS,
        composicion=[
            ComposicionBotanica(
                especie="regaliz",
                porcentaje=100,
                parte_utilizada="raiz",
                lote_origen="REG-2026-001",
            )
        ],
        peso_total_materia_seca_g=100,
        volumen_alcohol_ml=500,  # 0.5L
        parametros=ParametrosExtraccion(
            abv_objetivo=40.0,  # Alcohol más bajo para extraer dulzor
            ratio_planta_alcohol=0.2,
            temperatura_maceracion=20.0,
            agitacion_diaria=True,
            tiempo_estimado_dias=14,
            proteccion_luz=True,
            recipiente_material="vidrio",
        ),
        observaciones_iniciales="Tintura de regaliz para corrección de amargor y redondez",
    )

    # Simular registros de curva
    registros_regaliz = [
        (4, 30, ["glucosidos_dulces"], "ambar_claro", "claro", "Dulzor inicial"),
        (
            8,
            55,
            ["glucosidos_dulces", "saponinas"],
            "ambar",
            "claro",
            "Perfil definido",
        ),
        (
            12,
            75,
            ["glucosidos_dulces", "saponinas"],
            "ambar_oscuro",
            "claro",
            "PUNTO ÓPTIMO",
        ),
        (
            14,
            80,
            ["glucosidos_dulces", "saponinas", "taninos"],
            "miel",
            "ligera",
            "Inicio taninos",
        ),
    ]

    for dia, intensidad, compuestos, color, turbidez, aroma in registros_regaliz:
        registro = RegistroExtraccion(
            dia=dia,
            fecha=datetime.now() - timedelta(days=(14 - dia)),
            intensidad_estimada=intensidad,
            notas_sensoriales=f"Día {dia}: {aroma}",
            compuestos_detectados=compuestos,
            color=color,
            turbidez=turbidez,
            aroma_descripcion=aroma,
            momento_optimo_candidato=(dia == 12),
        )
        regaliz.agregar_registro_extraccion(registro)

    # Finalizar y estabilizar
    regaliz.finalizar_maceracion(datetime.now() - timedelta(days=2))
    regaliz.estabilizar(dias_estabilizacion=10, temperatura=5)
    regaliz.control_calidad = ControlCalidad(
        ph=5.8, densidad=1.02, alcohol_medido=39.5, rendimiento_volumen_ml=480
    )
    regaliz.marcar_como_lista(volumen_final_ml=480)
    regaliz.ubicacion_almacen = "Estante E1"

    repo.guardar(regaliz)
    todas_tinturas.append(regaliz)
    print(f"   ✅ Regaliz: {regaliz.id} - {regaliz.nombre}")
    print(
        f"      Volumen: {regaliz.volumen_disponible_ml} ml | ABV: {regaliz.parametros.abv_objetivo}%"
    )

    # =========================================================
    # RESUMEN FINAL
    # =========================================================
    print("\n" + "=" * 70)
    print("✅ BASE DE DATOS INICIALIZADA CORRECTAMENTE")
    print("=" * 70)

    print(f"\n📊 TOTAL: {len(todas_tinturas)} TINTURAS CREADAS")
    print("\n📋 LISTADO COMPLETO:")
    print("-" * 70)
    print(f"{'ID':<20} {'NOMBRE':<30} {'GRUPO':<20} {'VOLUMEN':<10}")
    print("-" * 70)

    for t in todas_tinturas:
        print(
            f"{t.id:<20} {t.nombre[:28]:<30} {t.grupo_funcional.value:<20} {t.volumen_disponible_ml:>5} ml"
        )

    print("-" * 70)

    # Estadísticas por grupo
    from collections import Counter

    grupos = [t.grupo_funcional.value for t in todas_tinturas]
    conteo = Counter(grupos)

    print("\n📊 DISTRIBUCIÓN POR GRUPO:")
    for grupo, cantidad in conteo.items():
        print(f"   • {grupo}: {cantidad} tintura(s)")

    print(f"\n💾 Base de datos: {db.db_path}")
    print(f"📁 Tamaño: {os.path.getsize(db.db_path) / 1024:.1f} KB")

    return todas_tinturas


def verificar_base_datos():
    """Verifica el contenido de la base de datos sin usar get_by_id"""
    print("\n" + "=" * 70)
    print("🔍 VERIFICACIÓN DE BASE DE DATOS")
    print("=" * 70)

    db = DatabaseManager()

    # Ver tablas
    with db.get_connection() as conn:
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;"
        )
        tablas = cursor.fetchall()

        print("\n📋 TABLAS EN LA BASE DE DATOS:")
        for tabla in tablas:
            nombre = tabla[0]
            cursor = conn.execute(f"SELECT COUNT(*) FROM {nombre}")
            count = cursor.fetchone()[0]
            print(f"   • {nombre}: {count} registros")

    # Ver tinturas directamente con SQL
    print(f"\n🧪 VERIFICANDO TINTURAS...")

    with db.get_connection() as conn:
        cursor = conn.execute(
            """
            SELECT t.id, t.nombre, t.grupo_funcional, t.estado, 
                   t.volumen_disponible_ml,
                   COUNT(DISTINCT c.id) as compuestos,
                   COUNT(DISTINCT cb.id) as botanica
            FROM tinturas t
            LEFT JOIN composicion_botanica cb ON t.id = cb.tintura_id
            LEFT JOIN registros_curva c ON t.id = c.tintura_id
            GROUP BY t.id
            ORDER BY t.grupo_funcional
        """
        )
        tinturas = cursor.fetchall()

        print(f"\n📋 TINTURAS EN BASE DE DATOS:")
        print("-" * 90)
        print(
            f"{'ID':<20} {'NOMBRE':<25} {'GRUPO':<20} {'ESTADO':<12} {'VOL':<6} {'COMP':<5}"
        )
        print("-" * 90)

        for t in tinturas:
            print(
                f"{t['id']:<20} {t['nombre'][:23]:<25} {t['grupo_funcional']:<20} "
                f"{t['estado']:<12} {t['volumen_disponible_ml']:>4} {t['compuestos']:>4}"
            )

    return True


if __name__ == "__main__":
    # Crear todas las tinturas
    tinturas = crear_tinturas_fernet_competitivo()

    # Verificar
    verificar_base_datos()

    print("\n" + "=" * 70)
    print("🚀 LISTO PARA EJECUTAR STREAMLIT")
    print("=" * 70)
    print("\nEjecuta el siguiente comando para iniciar la interfaz:")
    print("\n   streamlit run app.py")
    print("\n" + "=" * 70)
