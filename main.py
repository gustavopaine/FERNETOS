#!/usr/bin/env python3
"""
FernetOS - Sistema de gestión de formulación para amari competitivos
Punto de entrada principal con interfaz CLI
"""

import argparse
import sys
import os
from datetime import datetime
from typing import Dict, Any

# Asegurar que podemos importar módulos
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from modules.tinturas.models import (
    Tintura,
    GrupoFuncional,
    ComposicionBotanica,
    ParametrosExtraccion,
)
from modules.tinturas.repository import TinturaRepository  # Asumimos que existe
from modules.curvas.analyzer import CurveAnalyzer, CurveVisualizer
from modules.ensamblaje.calculator import FernetCalculator, BlendParams
from modules.microblending.pilot_batch import PilotBatch
from modules.microblending.ab_testing import ABTesting
from config.settings import load_settings, FernetOSConfig


class FernetOS:
    """Aplicación principal FernetOS"""

    def __init__(self):
        self.config = load_settings()
        self.tinturas_repo = TinturaRepository()
        self.calculator = FernetCalculator(self.tinturas_repo)
        self.curve_visualizer = CurveVisualizer()
        self.ab_testing = ABTesting()

        print(
            f"""
╔══════════════════════════════════════════════════════════╗
║                     FernetOS v{self.config.system.version}                       ║
║         Sistema de Formulación para Amari Competitivos    ║
╚══════════════════════════════════════════════════════════╝
        """
        )

    def cmd_crear_tintura(self, args):
        """Crea una nueva tintura"""
        print(f"\n🔬 Creando nueva tintura: {args.nombre}")

        # Crear composición desde argumentos
        composicion = []
        if args.composicion:
            # Formato: "genciana:60,ruibarbo:30,quina:10"
            for item in args.composicion.split(","):
                if ":" in item:
                    especie, pct = item.split(":")
                    composicion.append(
                        ComposicionBotanica(
                            especie=especie,
                            porcentaje=float(pct),
                            parte_utilizada=args.parte or "raiz",
                        )
                    )

        # Mapear grupo funcional
        grupo_map = {
            "amargos": GrupoFuncional.AMARGOS_ESTRUCTURALES,
            "aromatica": GrupoFuncional.AROMATICA_ALTA,
            "especias": GrupoFuncional.ESPECIAS_CALIDAS,
            "citricos": GrupoFuncional.CITRICOS,
        }

        grupo = grupo_map.get(args.grupo, GrupoFuncional.EXPERIMENTAL)

        # Parámetros de extracción
        parametros = ParametrosExtraccion(
            abv_objetivo=args.abv,
            ratio_planta_alcohol=1.0 / args.ratio,  # 5 → 0.2
            tiempo_estimado_dias=args.tiempo,
        )

        # Crear tintura
        tintura = Tintura(
            nombre=args.nombre,
            grupo_funcional=grupo,
            composicion=composicion,
            peso_total_materia_seca_g=args.peso_g,
            volumen_alcohol_ml=args.volumen_ml,
            parametros=parametros,
            observaciones_iniciales=args.observaciones,
        )

        # Guardar
        self.tinturas_repo.guardar(tintura)

        print(f"✅ Tintura creada con ID: {tintura.id}")
        print(f"   Grupo: {grupo.value}")
        print(f"   ABV: {args.abv}% | Ratio: 1:{args.ratio}")
        print(f"   Tiempo estimado: {args.tiempo} días")

        return tintura

    def cmd_registrar_cata(self, args):
        """Registra una cata para curva de extracción"""
        tintura = self.tinturas_repo.get_by_id(args.tintura_id)

        if not tintura:
            print(f"❌ Tintura {args.tintura_id} no encontrada")
            return

        from modules.tinturas.models import RegistroExtraccion

        registro = RegistroExtraccion(
            dia=args.dia,
            fecha=datetime.now(),
            intensidad_estimada=args.intensidad,
            notas_sensoriales=args.notas,
            compuestos_detectados=args.compuestos.split(",") if args.compuestos else [],
            color=args.color or "",
            turbidez=args.turbidez or "",
            aroma_descripcion=args.aroma or "",
        )

        tintura.agregar_registro_extraccion(registro)
        self.tinturas_repo.actualizar(tintura)

        print(f"✅ Registro día {args.dia} añadido a tintura {args.tintura_id}")

        # Analizar y sugerir
        analyzer = CurveAnalyzer(tintura)
        sugerencia = analyzer.sugerir_dia_corte()
        alertas = analyzer.alertar_sobreextraccion()

        if sugerencia:
            print(f"📊 Sugerencia de corte: día {sugerencia}")

        for alerta in alertas:
            print(f"⚠️ {alerta}")

    def cmd_analizar_curva(self, args):
        """Analiza y visualiza curva de extracción"""
        tintura = self.tinturas_repo.get_by_id(args.tintura_id)

        if not tintura:
            print(f"❌ Tintura {args.tintura_id} no encontrada")
            return

        analyzer = CurveAnalyzer(tintura)
        analisis = analyzer.analizar_completo()

        print(f"\n📈 Análisis de curva para {tintura.nombre}")
        print(f"   ID: {tintura.id}")
        print(f"   Registros: {len(tintura.registros_extraccion)}")
        print(f"   Día óptimo sugerido: {analisis.dia_optimo_sugerido}")
        print(f"   Área bajo curva: {analisis.area_bajo_curva:.1f}")

        if analisis.alertas:
            print("\n   ⚠️ ALERTAS:")
            for alerta in analisis.alertas:
                print(f"      • {alerta}")

        # Generar gráfico
        if args.grafico:
            filepath = self.curve_visualizer.generar_grafico(
                analyzer, titulo=f"{tintura.nombre} - {tintura.id}", guardar=True
            )
            print(f"\n📊 Gráfico guardado: {filepath}")

    def cmd_crear_blend(self, args):
        """Crea un blend base para ensamblaje"""
        params = BlendParams(
            volumen_objetivo_litros=args.volumen,
            abv_objetivo=args.abv,
            azucar_objetivo_gpl=args.azucar,
        )

        # Parsear tinturas: "T-001:250,T-002:150"
        tinturas_dict = {}
        if args.tinturas:
            for item in args.tinturas.split(","):
                if ":" in item:
                    tid, ml = item.split(":")
                    tinturas_dict[tid] = float(ml)

        # Obtener datos de tinturas
        tinturas_data = {}
        for tid in tinturas_dict.keys():
            t = self.tinturas_repo.get_by_id(tid)
            if t:
                tinturas_data[tid] = t

        resultado = self.calculator.calcular_blend_completo(
            params, tinturas_dict, tinturas_data
        )

        print(f"\n🧪 Blend calculado: {resultado.id}")
        print(f"   Versión: {resultado.version}")
        print(f"   ABV calculado: {resultado.abv_calculado:.2f}%")
        print(f"   Azúcar: {resultado.azucar_efectiva_gpl} g/L")
        print(f"   Volumen total: {resultado.volumen_real_ml/1000:.2f}L")
        print(f"   Margen error: {resultado.margen_error_ml:.1f}ml")

        print("\n   Composición:")
        print(f"      Alcohol base: {resultado.composicion.alcohol_base_ml:.0f}ml")
        print(f"      Agua base: {resultado.composicion.agua_base_ml:.0f}ml")
        for tid, ml in resultado.composicion.tinturas.items():
            nombre = (
                tinturas_data.get(tid, Tintura()).nombre
                if tid in tinturas_data
                else tid
            )
            print(f"      {nombre}: {ml:.1f}ml")

        return resultado

    def cmd_microblending(self, args):
        """Inicia proceso de microblending"""
        # Aquí se implementaría la lógica de microblending interactivo
        print("🔄 Módulo de microblending en desarrollo")

    def run(self):
        """Ejecuta CLI"""
        parser = argparse.ArgumentParser(
            description="FernetOS - Sistema de Formulación"
        )
        subparsers = parser.add_subparsers(dest="comando", help="Comandos disponibles")

        # Comando: crear-tintura
        parser_tintura = subparsers.add_parser(
            "crear-tintura", help="Crear nueva tintura"
        )
        parser_tintura.add_argument(
            "--nombre", required=True, help="Nombre de la tintura"
        )
        parser_tintura.add_argument(
            "--grupo",
            required=True,
            choices=["amargos", "aromatica", "especias", "citricos"],
            help="Grupo funcional",
        )
        parser_tintura.add_argument(
            "--composicion", help="Composición (ej: genciana:60,ruibarbo:30)"
        )
        parser_tintura.add_argument(
            "--parte", default="raiz", help="Parte de la planta"
        )
        parser_tintura.add_argument(
            "--abv", type=float, default=70.0, help="ABV objetivo"
        )
        parser_tintura.add_argument(
            "--ratio",
            type=float,
            default=5.0,
            help="Ratio alcohol:planta (ej: 5 = 1:5)",
        )
        parser_tintura.add_argument(
            "--tiempo", type=int, default=21, help="Tiempo estimado (días)"
        )
        parser_tintura.add_argument(
            "--peso-g", type=float, required=True, help="Peso materia seca (g)"
        )
        parser_tintura.add_argument(
            "--volumen-ml", type=float, required=True, help="Volumen alcohol (ml)"
        )
        parser_tintura.add_argument(
            "--observaciones", default="", help="Observaciones iniciales"
        )
        parser_tintura.set_defaults(func=self.cmd_crear_tintura)

        # Comando: registrar-cata
        parser_cata = subparsers.add_parser(
            "registrar-cata", help="Registrar cata para curva"
        )
        parser_cata.add_argument("--tintura-id", required=True, help="ID de la tintura")
        parser_cata.add_argument(
            "--dia", type=int, required=True, help="Día de maceración"
        )
        parser_cata.add_argument(
            "--intensidad",
            type=int,
            required=True,
            choices=range(0, 101),
            help="Intensidad estimada (0-100)",
        )
        parser_cata.add_argument("--notas", default="", help="Notas sensoriales")
        parser_cata.add_argument(
            "--compuestos", help="Compuestos detectados (separados por coma)"
        )
        parser_cata.add_argument("--color", help="Color observado")
        parser_cata.add_argument("--turbidez", help="Turbidez (claro/ligera/alta)")
        parser_cata.add_argument("--aroma", help="Descripción del aroma")
        parser_cata.set_defaults(func=self.cmd_registrar_cata)

        # Comando: analizar-curva
        parser_curva = subparsers.add_parser(
            "analizar-curva", help="Analizar curva de extracción"
        )
        parser_curva.add_argument(
            "--tintura-id", required=True, help="ID de la tintura"
        )
        parser_curva.add_argument(
            "--grafico", action="store_true", help="Generar gráfico"
        )
        parser_curva.set_defaults(func=self.cmd_analizar_curva)

        # Comando: crear-blend
        parser_blend = subparsers.add_parser("crear-blend", help="Crear blend base")
        parser_blend.add_argument(
            "--volumen", type=float, default=10.0, help="Volumen objetivo (L)"
        )
        parser_blend.add_argument(
            "--abv", type=float, default=40.0, help="ABV objetivo"
        )
        parser_blend.add_argument(
            "--azucar", type=int, default=195, help="Azúcar objetivo (g/L)"
        )
        parser_blend.add_argument(
            "--tinturas", help="Tinturas (ej: T-001:250,T-002:150)"
        )
        parser_blend.set_defaults(func=self.cmd_crear_blend)

        # Comando: microblending
        parser_micro = subparsers.add_parser(
            "microblending", help="Iniciar microblending"
        )
        parser_micro.add_argument("--blend-id", required=True, help="ID del blend base")
        parser_micro.set_defaults(func=self.cmd_microblending)

        # Parsear argumentos
        args = parser.parse_args()

        if hasattr(args, "func"):
            args.func(args)
        else:
            parser.print_help()


if __name__ == "__main__":
    app = FernetOS()
    app.run()
