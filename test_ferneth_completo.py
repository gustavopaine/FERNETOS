#!/usr/bin/env python3
"""
Script de prueba integral para FernetOS.
Simula el desarrollo completo de un fernet competitivo desde cero.
"""

import os
import sys
import tempfile
from datetime import datetime, timedelta
from pprint import pprint

# Asegurar que Python encuentra los módulos
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from modules.tinturas.models import (
    Tintura,
    GrupoFuncional,
    ComposicionBotanica,
    ParametrosExtraccion,
    RegistroExtraccion,
    EstadoTintura,
)
from modules.tinturas.repository import TinturaRepository
from modules.curvas.analyzer import CurveAnalyzer, CurveVisualizer, HistoricalCurveDB
from modules.ensamblaje.calculator import (
    FernetCalculator,
    BlendParams,
    ImpactSimulator,
    SugarOptimizer,
)
from modules.microblending.pilot_batch import PilotBatch
from modules.microblending.ab_testing import ABTesting, CompetitiveAnalyzer
from modules.sensory.models import EvaluacionSensorial, SensoryAnalyzer
from config.settings import load_settings


def test_flujo_completo():
    """Ejecuta prueba completa del sistema"""

    print("=" * 70)
    print("🧪 FERNETOS - PRUEBA DE SISTEMA COMPLETO")
    print("=" * 70)

    # Configuración temporal para prueba
    temp_dir = tempfile.mkdtemp()
    print(f"\n📁 Usando directorio temporal: {temp_dir}")

    # Inicializar componentes
    config = load_settings()
    repo = TinturaRepository(data_dir=os.path.join(temp_dir, "tinturas"))
    calculator = FernetCalculator(repo)
    visualizer = CurveVisualizer(output_dir=os.path.join(temp_dir, "curves"))
    historical_db = HistoricalCurveDB(db_path=os.path.join(temp_dir, "historical.json"))
    ab_testing = ABTesting(output_dir=os.path.join(temp_dir, "tests"))
    sensory_analyzer = SensoryAnalyzer()

    print("\n✅ Componentes inicializados")

    # =========================================================
    # PASO 1: CREAR TINTURAS (4 tinturas base)
    # =========================================================
    print("\n" + "-" * 50)
    print("📦 PASO 1: Creando tinturas base")
    print("-" * 50)

    # 1.1 Tintura de Amargos Estructurales
    print("\n🔬 Creando tintura de AMARGOS...")

    amargos = Tintura(
        nombre="Amargos Estructurales Test",
        grupo_funcional=GrupoFuncional.AMARGOS_ESTRUCTURALES,
        composicion=[
            ComposicionBotanica(
                especie="genciana", porcentaje=55, parte_utilizada="raiz"
            ),
            ComposicionBotanica(
                especie="ruibarbo", porcentaje=35, parte_utilizada="raiz"
            ),
            ComposicionBotanica(
                especie="quina", porcentaje=5, parte_utilizada="corteza"
            ),
            ComposicionBotanica(
                especie="angelica", porcentaje=5, parte_utilizada="raiz"
            ),
        ],
        peso_total_materia_seca_g=200,  # 200g
        volumen_alcohol_ml=1000,  # 1L (ratio 1:5)
        parametros=ParametrosExtraccion(
            abv_objetivo=70.0, ratio_planta_alcohol=0.2, tiempo_estimado_dias=18
        ),
        observaciones_iniciales="Prueba de amargos optimizados",
    )
    repo.guardar(amargos)
    print(f"   ✅ ID: {amargos.id}")

    # 1.2 Tintura Aromática Alta
    print("\n🔬 Creando tintura AROMÁTICA...")

    aromatica = Tintura(
        nombre="Aromática Alta Test",
        grupo_funcional=GrupoFuncional.AROMATICA_ALTA,
        composicion=[
            ComposicionBotanica(
                especie="cardo_mariano", porcentaje=40, parte_utilizada="hoja"
            ),
            ComposicionBotanica(
                especie="menta_piperita", porcentaje=30, parte_utilizada="hoja"
            ),
            ComposicionBotanica(
                especie="romero", porcentaje=20, parte_utilizada="hoja"
            ),
            ComposicionBotanica(
                especie="azafran", porcentaje=10, parte_utilizada="estigma"
            ),
        ],
        peso_total_materia_seca_g=250,  # 250g
        volumen_alcohol_ml=1000,  # 1L
        parametros=ParametrosExtraccion(
            abv_objetivo=55.0, ratio_planta_alcohol=0.25, tiempo_estimado_dias=7
        ),
    )
    repo.guardar(aromatica)
    print(f"   ✅ ID: {aromatica.id}")

    # 1.3 Tintura de Especias
    print("\n🔬 Creando tintura de ESPECIAS...")

    especias = Tintura(
        nombre="Especias Cálidas Test",
        grupo_funcional=GrupoFuncional.ESPECIAS_CALIDAS,
        composicion=[
            ComposicionBotanica(
                especie="canela", porcentaje=55, parte_utilizada="corteza"
            ),
            ComposicionBotanica(
                especie="cardamomo", porcentaje=25, parte_utilizada="semilla"
            ),
            ComposicionBotanica(
                especie="clavo", porcentaje=5, parte_utilizada="cogollo"
            ),
            ComposicionBotanica(
                especie="nuez_moscada", porcentaje=15, parte_utilizada="semilla"
            ),
        ],
        peso_total_materia_seca_g=200,
        volumen_alcohol_ml=1000,
        parametros=ParametrosExtraccion(
            abv_objetivo=65.0, ratio_planta_alcohol=0.2, tiempo_estimado_dias=14
        ),
    )
    repo.guardar(especias)
    print(f"   ✅ ID: {especias.id}")

    # 1.4 Tintura Cítrica
    print("\n🔬 Creando tintura CÍTRICA...")

    citricos = Tintura(
        nombre="Cítricos Test",
        grupo_funcional=GrupoFuncional.CITRICOS,
        composicion=[
            ComposicionBotanica(
                especie="naranja_amarga", porcentaje=60, parte_utilizada="cascara_seca"
            ),
            ComposicionBotanica(
                especie="limon", porcentaje=40, parte_utilizada="cascara_seca"
            ),
        ],
        peso_total_materia_seca_g=250,
        volumen_alcohol_ml=1000,
        parametros=ParametrosExtraccion(
            abv_objetivo=75.0, ratio_planta_alcohol=0.25, tiempo_estimado_dias=4
        ),
    )
    repo.guardar(citricos)
    print(f"   ✅ ID: {citricos.id}")

    print("\n✅ 4 tinturas creadas correctamente")

    # =========================================================
    # PASO 2: SIMULAR REGISTROS DE CURVA (microcatas cada 48h)
    # =========================================================
    print("\n" + "-" * 50)
    print("📈 PASO 2: Registrando curvas de extracción")
    print("-" * 50)

    # Función para simular registros
    def simular_registros(tintura, dias, intensidades, compuestos_por_dia):
        for i, dia in enumerate(dias):
            registro = RegistroExtraccion(
                dia=dia,
                fecha=datetime.now() + timedelta(days=dia),
                intensidad_estimada=intensidades[i],
                notas_sensoriales=f"Cata día {dia}",
                compuestos_detectados=compuestos_por_dia[i],
                color="ambar" if dia < 10 else "ambar_oscuro",
                turbidez="ligera" if dia < 7 else "clara",
                aroma_descripcion=f"Aroma {tintura.grupo_funcional.value} día {dia}",
            )
            tintura.agregar_registro_extraccion(registro)
        repo.actualizar(tintura)

    # Simular registros para amargos (días 2,4,6,8,10,12,14,16,18)
    simular_registros(
        amargos,
        dias=[2, 4, 6, 8, 10, 12, 14, 16, 18],
        intensidades=[15, 35, 55, 72, 82, 88, 92, 94, 95],
        compuestos_por_dia=[
            ["glucosidos"],  # día 2
            ["glucosidos", "taninos_ligeros"],  # día 4
            ["glucosidos", "taninos"],  # día 6
            ["glucosidos", "taninos"],  # día 8
            ["glucosidos", "taninos", "resinas"],  # día 10
            ["glucosidos", "taninos", "resinas"],  # día 12
            ["glucosidos", "taninos", "resinas"],  # día 14
            ["glucosidos", "taninos", "resinas"],  # día 16
            [
                "glucosidos",
                "taninos",
                "resinas",
                "terrosos",
            ],  # día 18 (inicio sobreextracción)
        ],
    )

    # Simular registros para aromática (días 1,3,5,7)
    simular_registros(
        aromatica,
        dias=[1, 3, 5, 7],
        intensidades=[25, 58, 82, 88],
        compuestos_por_dia=[
            ["terpenos_volatiles"],  # día 1
            ["terpenos_volatiles", "clorofila_ligera"],  # día 3
            ["terpenos_volatiles", "clorofila"],  # día 5
            ["terpenos", "clorofila", "herbaceos_pesados"],  # día 7
        ],
    )

    # Simular registros para especias (días 2,4,6,8,10,12,14)
    simular_registros(
        especias,
        dias=[2, 4, 6, 8, 10, 12, 14],
        intensidades=[20, 42, 63, 78, 86, 90, 91],
        compuestos_por_dia=[
            ["aceites_esenciales"],  # día 2
            ["aceites_esenciales", "eugenol_ligero"],  # día 4
            ["aceites_esenciales", "eugenol"],  # día 6
            ["aceites_esenciales", "eugenol", "resinas"],  # día 8
            ["resinas", "taninos"],  # día 10
            ["resinas", "taninos"],  # día 12
            ["resinas", "taninos", "leñoso"],  # día 14
        ],
    )

    # Simular registros para cítricos (días 1,2,3,4)
    simular_registros(
        citricos,
        dias=[1, 2, 3, 4],
        intensidades=[40, 72, 85, 88],
        compuestos_por_dia=[
            ["aceites_esenciales", "limoneno"],  # día 1
            ["aceites_esenciales", "limoneno"],  # día 2
            ["aceites_esenciales", "limoneno", "terpenos"],  # día 3
            ["aceites_esenciales", "terpenos", "ceras"],  # día 4
        ],
    )

    print("✅ Registros de curva simulados para todas las tinturas")

    # =========================================================
    # PASO 3: ANALIZAR CURVAS Y DETERMINAR PUNTOS DE CORTE
    # =========================================================
    print("\n" + "-" * 50)
    print("🔍 PASO 3: Analizando curvas de extracción")
    print("-" * 50)

    tinturas_analizar = [amargos, aromatica, especias, citricos]

    for t in tinturas_analizar:
        analyzer = CurveAnalyzer(t)
        analisis = analyzer.analizar_completo()

        print(f"\n📊 {t.nombre} ({t.id})")
        print(f"   Registros: {len(t.registros_extraccion)}")
        print(f"   Día óptimo sugerido: {analisis.dia_optimo_sugerido}")
        print(f"   Área bajo curva: {analisis.area_bajo_curva:.1f}")

        # Generar gráfico
        filepath = visualizer.generar_grafico(analyzer, guardar=True, mostrar=False)
        print(f"   📈 Gráfico: {os.path.basename(filepath)}")

        if analisis.alertas:
            for alerta in analisis.alertas:
                print(f"   ⚠️ {alerta}")

        # Registrar en base histórica
        historical_db.registrar_curva(analyzer)

    print("\n✅ Análisis de curvas completado")

    # =========================================================
    # PASO 4: SIMULAR FINALIZACIÓN DE MACERACIÓN
    # =========================================================
    print("\n" + "-" * 50)
    print("✂️ PASO 4: Finalizando maceraciones")
    print("-" * 50)

    try:
        # Finalizar según puntos óptimos
        print("\n   Finalizando Amargos...")
        amargos.finalizar_maceracion(datetime.now() + timedelta(days=16))
        amargos.estabilizar(dias_estabilizacion=15, temperatura=5)
        amargos.marcar_como_lista(volumen_final_ml=950)  # Pérdida 5%
        repo.actualizar(amargos)
        print("   ✅ Amargos finalizados")

        print("   Finalizando Aromática...")
        aromatica.finalizar_maceracion(datetime.now() + timedelta(days=5))
        aromatica.estabilizar(dias_estabilizacion=10, temperatura=5)
        aromatica.marcar_como_lista(volumen_final_ml=960)
        repo.actualizar(aromatica)
        print("   ✅ Aromática finalizada")

        print("   Finalizando Especias...")
        especias.finalizar_maceracion(datetime.now() + timedelta(days=12))
        especias.estabilizar(dias_estabilizacion=12, temperatura=5)
        especias.marcar_como_lista(volumen_final_ml=940)
        repo.actualizar(especias)
        print("   ✅ Especias finalizadas")

        print("   Finalizando Cítricos...")
        citricos.finalizar_maceracion(datetime.now() + timedelta(days=4))
        citricos.estabilizar(dias_estabilizacion=8, temperatura=5)
        citricos.marcar_como_lista(volumen_final_ml=970)
        repo.actualizar(citricos)
        print("   ✅ Cítricos finalizados")

        print("\n✅ Todas las tinturas finalizadas y estabilizadas")
    except Exception as e:
        print(f"\n❌ Error en Paso 4: {e}")
        print(f"   Tipo de error: {type(e).__name__}")
        import traceback

        traceback.print_exc()
        raise

    # =========================================================
    # PASO 5: CREAR BLEND BASE (para 10L)
    # =========================================================
    print("\n" + "-" * 50)
    print("🧪 PASO 5: Creando blend base para 10L")
    print("-" * 50)

    params = BlendParams(
        volumen_objetivo_litros=10.0, abv_objetivo=40.0, azucar_objetivo_gpl=195
    )

    # Obtener datos actualizados de tinturas
    amargos_actualizada = repo.get_by_id(amargos.id)
    aromatica_actualizada = repo.get_by_id(aromatica.id)
    especias_actualizada = repo.get_by_id(especias.id)
    citricos_actualizada = repo.get_by_id(citricos.id)

    tinturas_dict = {
        amargos_actualizada.id: 200,  # 200ml
        aromatica_actualizada.id: 150,  # 150ml
        especias_actualizada.id: 120,  # 120ml
        citricos_actualizada.id: 70,  # 70ml
    }

    tinturas_data = {
        amargos_actualizada.id: amargos_actualizada,
        aromatica_actualizada.id: aromatica_actualizada,
        especias_actualizada.id: especias_actualizada,
        citricos_actualizada.id: citricos_actualizada,
    }

    blend_inicial = calculator.calcular_blend_completo(
        params, tinturas_dict, tinturas_data
    )

    print(f"\n📋 Blend calculado: {blend_inicial.id}")
    print(f"   Versión: {blend_inicial.version}")
    print(f"   ABV calculado: {blend_inicial.abv_calculado:.2f}%")
    print(f"   Azúcar: {blend_inicial.azucar_efectiva_gpl} g/L")
    print(f"   Volumen: {blend_inicial.volumen_real_ml/1000:.2f}L")

    print("\n   Composición:")
    for tid, ml in blend_inicial.composicion.tinturas.items():
        nombre = tinturas_data[tid].nombre
        print(f"      {nombre}: {ml:.1f}ml")

    # =========================================================
    # PASO 6: MICROBLENDING EN LOTE PILOTO (500ml)
    # =========================================================
    print("\n" + "-" * 50)
    print("🎯 PASO 6: Microblending iterativo en lote piloto (500ml)")
    print("-" * 50)

    # Crear lote piloto
    piloto = PilotBatch(
        nombre="Fernet Test Pilot",
        blend_base=blend_inicial,
        tinturas_data=tinturas_data,
        volumen_piloto_ml=500,
    )

    print(f"\n✅ Lote piloto creado: {piloto.id}")

    # Iteración 1: Ajuste de ataque (aumentar cítricos)
    print("\n🔄 Iteración 1: Ajustando ataque (+0.3ml cítricos)")

    blend_it1 = piloto.aplicar_ajuste(
        tintura_id=citricos_actualizada.id,
        incremento_ml=0.3,
        razon="ataque_insuficiente",
        observacion="Buscar más brillo inicial",
    )

    # Iteración 2: Ajuste de complejidad (microdosis de clavo)
    print("🔄 Iteración 2: Añadiendo microdosis de clavo (+0.1ml)")

    # Crear tintura de clavo separada (simulada)
    class MockTintura:
        def __init__(self, id, nombre, abv):
            self.id = id
            self.nombre = nombre
            # Crear un objeto parametros con los atributos necesarios
            self.parametros = type(
                "obj",
                (object,),
                {
                    "abv_objetivo": abv,
                    "ratio_planta_alcohol": 0.2,
                    "tiempo_estimado_dias": 14,
                },
            )

    clavo_tintura = MockTintura("T-CLAVO-001", "Clavo Controlado", 65.0)
    tinturas_data["T-CLAVO-001"] = clavo_tintura

    blend_it2 = piloto.aplicar_ajuste(
        tintura_id="T-CLAVO-001",
        incremento_ml=0.1,
        razon="complejidad",
        observacion="Toque de clavo para profundidad",
    )

    # Iteración 3: Ajuste múltiple
    print("🔄 Iteración 3: Ajuste múltiple (equilibrio)")

    blend_it3 = piloto.aplicar_ajustes_multiples(
        [
            (amargos_actualizada.id, -0.2),  # Reducir amargor
            (aromatica_actualizada.id, 0.2),  # Aumentar aroma
            (citricos_actualizada.id, 0.1),  # Más cítricos
        ],
        razon="equilibrio_general",
    )

    print(f"\n✅ {len(piloto.iteraciones)} iteraciones completadas")

    # Mostrar historial de ajustes
    print("\n📜 Historial de ajustes:")
    historial = piloto.get_historial_ajustes()
    for h in historial:
        print(
            f"   Iter {h['iteracion']}: {h['tintura_id'][-6:]} {h['incremento_ml']:+.2f}ml - {h['razon']}"
        )

    print(f"\n📊 Ajustes acumulados: {piloto.ajustes_acumulados}")

    # =========================================================
    # PASO 7: SIMULAR EVALUACIONES SENSORIALES
    # =========================================================
    print("\n" + "-" * 50)
    print("👃 PASO 7: Simulando evaluaciones sensoriales")
    print("-" * 50)

    # Evaluar iteración 2 (la que tiene clavo)
    eval_it2 = EvaluacionSensorial(
        muestra_id=blend_it2.id,
        muestra_descripcion="Iteración 2 - Con clavo",
        catador="Sistema Test",
        ataque=8.2,
        complejidad=8.5,
        equilibrio=7.8,
        persistencia=8.3,
        amargor=7.9,
        dulzor=7.5,
        astringencia=6.5,
        alcohol_sensacion=7.0,
        notas_herbaceas=8.0,
        notas_especiadas=7.5,
        notas_citricas=7.8,
        notas_medicinales=6.5,
        notas_balsamicas=7.0,
        observaciones="Buen ataque, buena complejidad, ligero exceso de especias",
        defectos=["ligera_astringencia"],
    )

    piloto.registrar_evaluacion(eval_it2, iteracion_numero=2)
    sensory_analyzer.agregar_evaluacion(eval_it2)

    # Evaluar iteración 3 (ajuste múltiple)
    eval_it3 = EvaluacionSensorial(
        muestra_id=blend_it3.id,
        muestra_descripcion="Iteración 3 - Ajuste equilibrio",
        catador="Sistema Test",
        ataque=8.5,
        complejidad=8.3,
        equilibrio=8.6,
        persistencia=8.4,
        amargor=8.2,
        dulzor=7.8,
        astringencia=5.5,
        alcohol_sensacion=6.8,
        notas_herbaceas=8.2,
        notas_especiadas=7.2,
        notas_citricas=8.0,
        notas_medicinales=6.0,
        notas_balsamicas=6.8,
        observaciones="Excelente equilibrio, buen ataque, persistencia limpia",
        defectos=[],
    )

    piloto.registrar_evaluacion(eval_it3, iteracion_numero=3)
    sensory_analyzer.agregar_evaluacion(eval_it3)

    print("✅ Evaluaciones registradas")

    # Encontrar mejor iteración
    mejor = piloto.get_mejor_iteracion(criterio="puntaje_total")
    if mejor:
        print(
            f"\n🏆 Mejor iteración: {mejor.numero} (puntaje: {mejor.evaluacion.puntaje_total if mejor.evaluacion else 'N/A'})"
        )

    # =========================================================
    # PASO 8: PRUEBA A/B CONTRA REFERENCIA
    # =========================================================
    print("\n" + "-" * 50)
    print("⚖️ PASO 8: Prueba A/B contra referencia")
    print("-" * 50)

    # Preparar prueba A/B
    prueba_config = ab_testing.preparar_prueba_ab(
        muestra_a=blend_it3,
        muestra_b="REFERENCIA_BRANCA",
        desc_a="Nuestra fórmula (IT3)",
        desc_b="Fernet Branca",
    )

    print(f"\n📋 Prueba preparada: {prueba_config['prueba_id']}")
    print(f"   Códigos: {prueba_config['codigos']}")

    # Simular resultado (nuestra fórmula gana)
    resultado = ab_testing.registrar_resultado_ab(
        prueba_config=prueba_config,
        codigo_seleccionado=prueba_config["codigos"][0],  # Nuestra fórmula
        preferencia="A",
        atributos=["ataque", "equilibrio", "persistencia"],
        notas="Nuestra fórmula más equilibrada y con mejor ataque",
        catador="Panel Test",
    )

    print(f"\n✅ Resultado: Seleccionada {resultado.seleccionado}")
    print(f"   Atributos destacados: {resultado.atributos_destacados}")

    # =========================================================
    # PASO 9: ANÁLISIS COMPETITIVO
    # =========================================================
    print("\n" + "-" * 50)
    print("🏁 PASO 9: Análisis competitivo")
    print("-" * 50)

    competitive = CompetitiveAnalyzer()

    # Comparar con Branca
    comparativa = competitive.comparar_con_referencia(
        evaluacion_nuestra=eval_it3, referencia="branca"
    )

    print(f"\n📊 Comparativa vs {comparativa.referencia}:")
    print(f"   Diferencial: {comparativa.puntaje_diferencial:+.2f}")
    print(f"   Superioridad detectada: {comparativa.superioridad_detectada}")
    print(f"   Confianza: {comparativa.confianza:.1%}")
    print(f"   Atributos ganados: {comparativa.atributos_ganados}")
    print(f"   Atributos perdidos: {comparativa.atributos_perdidos}")

    # Recomendaciones
    if comparativa.atributos_perdidos:
        print("\n💡 Recomendaciones de ajuste:")
        for rec in competitive.recomendar_ajustes(comparativa):
            print(f"   • {rec}")

    # =========================================================
    # PASO 10: ESCALADO FINAL A 40L
    # =========================================================
    print("\n" + "-" * 50)
    print("📏 PASO 10: Escalado final a 40L")
    print("-" * 50)

    # Usar la mejor iteración
    blend_final = mejor.blend if mejor else blend_it3

    blend_40l = calculator.escalar_blend(blend_final, 40.0)

    print(f"\n📦 Blend escalado a 40L:")
    print(f"   ID: {blend_40l.id}")
    print(f"   Versión: {blend_40l.version}")
    print(f"   ABV: {blend_40l.abv_calculado:.2f}%")
    print(f"   Azúcar: {blend_40l.azucar_efectiva_gpl} g/L")
    print(f"   Volumen calculado: {blend_40l.volumen_real_ml/1000:.2f}L")

    print("\n   Composición para 40L:")
    for tid, ml in blend_40l.composicion.tinturas.items():
        nombre = (
            "Amargos"
            if "amargos" in tid.lower()
            else (
                "Aromática"
                if "aromatica" in tid.lower()
                else (
                    "Especias"
                    if "especias" in tid.lower()
                    else "Cítricos" if "citricos" in tid.lower() else tid[:8]
                )
            )
        )
        print(f"      {nombre}: {ml:.0f}ml")

    print(f"\n   Alcohol base: {blend_40l.composicion.alcohol_base_ml:.0f}ml")
    print(f"   Agua base: {blend_40l.composicion.agua_base_ml:.0f}ml")
    print(f"   Azúcar: {blend_40l.composicion.azucar_g/1000:.1f}kg")

    # =========================================================
    # RESUMEN FINAL
    # =========================================================
    print("\n" + "=" * 70)
    print("✅ PRUEBA COMPLETADA EXITOSAMENTE")
    print("=" * 70)

    print(
        f"""
    📊 ESTADÍSTICAS FINALES:
    
    Tinturas creadas: 4
    Registros de curva: {sum(len(t.registros_extraccion) for t in [amargos, aromatica, especias, citricos])}
    Iteraciones microblending: {len(piloto.iteraciones) - 1}
    Evaluaciones sensoriales: {len(sensory_analyzer.evaluaciones)}
    Pruebas A/B realizadas: 1
    Blend final: {blend_40l.version} (40L)
    
    🏆 RESULTADO COMPETITIVO:
    Diferencial vs Branca: {comparativa.puntaje_diferencial:+.2f}
    Superioridad: {'✅ SÍ' if comparativa.superioridad_detectada else '❌ NO'}
    
    📁 Archivos generados en: {temp_dir}
    """
    )

    return {
        "tinturas": [amargos.id, aromatica.id, especias.id, citricos.id],
        "blend_final": blend_40l,
        "mejor_iteracion": mejor.numero if mejor else None,
        "comparativa": comparativa,
        "temp_dir": temp_dir,
    }


if __name__ == "__main__":
    resultados = test_flujo_completo()
