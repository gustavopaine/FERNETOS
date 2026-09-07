"""
Visualizador y base histórica de curvas de extracción para tinturas.
"""

import numpy as np
import matplotlib.pyplot as plt
from typing import List, Dict
from datetime import datetime
import json
import os

from core.curve_analysis import CurveAnalyzer


class CurveVisualizer:
    """
    Visualizador de curvas de extracción.
    Genera gráficos profesionales para análisis y documentación.
    """

    def __init__(self, output_dir: str = "outputs/curves"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    def generar_grafico(
        self,
        analyzer: CurveAnalyzer,
        titulo: str = None,
        guardar: bool = True,
        mostrar: bool = False,
    ) -> str:
        """
        Genera un gráfico completo de la curva de extracción.

        Args:
            analyzer: CurveAnalyzer con los datos
            titulo: Título personalizado
            guardar: Si debe guardar el archivo
            mostrar: Si debe mostrar la figura

        Returns:
            str: Ruta del archivo guardado (si guardar=True)
        """
        tintura = analyzer.tintura

        # Configurar figura
        fig, (ax1, ax2) = plt.subplots(
            2, 1, figsize=(12, 10), gridspec_kw={"height_ratios": [3, 1]}
        )

        # ---- GRÁFICO PRINCIPAL ----
        dias, intensidades = analyzer.get_arrays()

        if len(dias) > 0:
            # Puntos reales
            ax1.scatter(
                dias,
                intensidades,
                color="blue",
                s=50,
                zorder=5,
                label="Catas registradas",
            )

            # Curva suavizada
            if len(dias) >= 3:
                dias_suave, int_suave = analyzer.modelar_curva_suave()
                ax1.plot(
                    dias_suave,
                    int_suave,
                    color="darkblue",
                    linewidth=2,
                    linestyle="-",
                    alpha=0.7,
                    label="Curva estimada",
                )

            # Línea de conexión
            ax1.plot(
                dias,
                intensidades,
                color="lightblue",
                linewidth=1.5,
                linestyle="--",
                alpha=0.5,
            )

            # Punto óptimo sugerido
            analisis = analyzer.analizar_completo()
            if analisis.dia_optimo_sugerido is not None:
                ax1.axvline(
                    x=analisis.dia_optimo_sugerido,
                    color="green",
                    linestyle="--",
                    linewidth=2,
                    alpha=0.7,
                    label=f"Corte óptimo: día {analisis.dia_optimo_sugerido}",
                )

                # Marcar intensidad en óptimo
                if analisis.intensidad_optima:
                    ax1.scatter(
                        analisis.dia_optimo_sugerido,
                        analisis.intensidad_optima,
                        color="green",
                        s=200,
                        marker="*",
                        zorder=10,
                        label="Punto óptimo",
                    )

            # Alertas de sobreextracción
            for alerta in analisis.alertas:
                if "cayó" in alerta:
                    ax1.axvspan(
                        analisis.dia_optimo_sugerido or 0,
                        max(dias),
                        alpha=0.2,
                        color="red",
                        label="Zona riesgo sobreextracción",
                    )

        # Configurar eje principal
        ax1.set_xlabel("Días de maceración", fontsize=12)
        ax1.set_ylabel("Intensidad estimada (0-100)", fontsize=12)
        ax1.set_title(
            titulo or f"Curva de Extracción: {tintura.nombre} ({tintura.id})",
            fontsize=14,
            fontweight="bold",
        )
        ax1.set_ylim(0, 105)
        ax1.set_xlim(0, max(dias) + 2 if len(dias) > 0 else 30)
        ax1.grid(True, alpha=0.3)
        ax1.legend(loc="lower right")

        # Añadir anotaciones de compuestos
        analisis = analyzer.analizar_completo()
        y_pos = 95
        for compuesto, dias_presencia in analisis.compuestos_detectados.items():
            if dias_presencia:
                dia_inicio = min(dias_presencia)
                ax1.annotate(
                    compuesto,
                    xy=(dia_inicio, y_pos),
                    xytext=(dia_inicio, y_pos),
                    fontsize=8,
                    alpha=0.7,
                    bbox=dict(boxstyle="round,pad=0.3", facecolor="yellow", alpha=0.3),
                )
                y_pos -= 5
                if y_pos < 60:
                    y_pos = 95

        # ---- GRÁFICO DE PENDIENTES ----
        dias_medios, pendientes = analyzer.calcular_pendientes()

        if len(pendientes) > 0:
            ax2.bar(dias_medios, pendientes, width=1.5, color="orange", alpha=0.7)
            ax2.axhline(y=0, color="black", linewidth=0.5)
            ax2.axhline(
                y=2, color="green", linestyle="--", alpha=0.5, label="Umbral óptimo"
            )
            ax2.axhline(y=-2, color="red", linestyle="--", alpha=0.5)

            # Zonas de riesgo
            ax2.fill_between(
                [0, max(dias_medios) if len(dias_medios) > 0 else 30],
                2,
                10,
                alpha=0.1,
                color="green",
                label="Extracción activa",
            )
            ax2.fill_between(
                [0, max(dias_medios) if len(dias_medios) > 0 else 30],
                -10,
                -2,
                alpha=0.1,
                color="red",
                label="Riesgo sobreextracción",
            )

        ax2.set_xlabel("Días de maceración", fontsize=12)
        ax2.set_ylabel("Pendiente (intensidad/día)", fontsize=12)
        ax2.set_title("Velocidad de extracción", fontsize=12)
        ax2.grid(True, alpha=0.3)
        ax2.legend(loc="upper right")
        ax2.set_xlim(0, max(dias) + 2 if len(dias) > 0 else 30)

        plt.tight_layout()

        # Guardar
        filepath = None
        if guardar:
            filename = f"{tintura.id}_{tintura.nombre.replace(' ', '_')}_curve.png"
            filepath = os.path.join(self.output_dir, filename)
            plt.savefig(filepath, dpi=150, bbox_inches="tight")

        if mostrar:
            plt.show()
        else:
            plt.close()

        return filepath if guardar else None

    def generar_comparativa(
        self,
        analyzers: List[CurveAnalyzer],
        nombres: List[str] = None,
        titulo: str = "Comparativa de Curvas",
    ) -> str:
        """
        Genera gráfico comparativo de múltiples curvas.

        Args:
            analyzers: Lista de analyzers a comparar
            nombres: Nombres personalizados para cada curva
            titulo: Título del gráfico

        Returns:
            str: Ruta del archivo guardado
        """
        fig, ax = plt.subplots(figsize=(12, 8))

        colores = ["blue", "red", "green", "orange", "purple", "brown"]

        for i, analyzer in enumerate(analyzers):
            color = colores[i % len(colores)]
            nombre = (
                nombres[i] if nombres and i < len(nombres) else analyzer.tintura.nombre
            )

            dias, intensidades = analyzer.get_arrays()
            if len(dias) > 0:
                # Puntos
                ax.scatter(dias, intensidades, color=color, s=30, alpha=0.7)

                # Curva suave
                if len(dias) >= 3:
                    dias_suave, int_suave = analyzer.modelar_curva_suave()
                    ax.plot(
                        dias_suave,
                        int_suave,
                        color=color,
                        linewidth=2,
                        label=f"{nombre}",
                        alpha=0.8,
                    )

        ax.set_xlabel("Días de maceración", fontsize=12)
        ax.set_ylabel("Intensidad estimada (0-100)", fontsize=12)
        ax.set_title(titulo, fontsize=14, fontweight="bold")
        ax.set_ylim(0, 105)
        ax.grid(True, alpha=0.3)
        ax.legend(loc="best")

        plt.tight_layout()

        # Guardar
        filename = f"comparativa_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        filepath = os.path.join(self.output_dir, filename)
        plt.savefig(filepath, dpi=150, bbox_inches="tight")
        plt.close()

        return filepath


class HistoricalCurveDB:
    """
    Base de datos de curvas históricas para comparación y referencia.
    """

    def __init__(self, db_path: str = "data/curves/historical.json"):
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.curvas = self._cargar()

    def _cargar(self) -> Dict:
        """Carga curvas históricas desde archivo"""
        if os.path.exists(self.db_path):
            try:
                with open(self.db_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error cargando base histórica: {e}")
                return {}
        return {}

    def _guardar(self):
        """Guarda curvas en archivo"""
        try:
            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
            with open(self.db_path, "w", encoding="utf-8") as f:
                json.dump(self.curvas, f, indent=2)
        except Exception as e:
            print(f"Error guardando base histórica: {e}")

    def registrar_curva(self, analyzer: CurveAnalyzer):
        """
        Registra una curva completada en la base histórica.

        Args:
            analyzer: CurveAnalyzer con la curva completada
        """
        try:
            analisis = analyzer.analizar_completo()

            self.curvas[analyzer.tintura.id] = {
                "nombre": analyzer.tintura.nombre,
                "grupo": analyzer.tintura.grupo_funcional.value,
                "fecha_inicio": (
                    analyzer.tintura.fecha_inicio.isoformat()
                    if analyzer.tintura.fecha_inicio
                    else None
                ),
                "composicion": (
                    [c.to_dict() for c in analyzer.tintura.composicion]
                    if analyzer.tintura.composicion
                    else []
                ),
                "dias_totales": analyzer.tintura.dias_transcurridos,
                "dia_optimo": analisis.dia_optimo_sugerido,
                "intensidad_max": (
                    max([r.intensidad_estimada for r in analyzer.registros])
                    if analyzer.registros
                    else 0
                ),
                "area_bajo_curva": analisis.area_bajo_curva,
                "parametros": {
                    "abv": (
                        analyzer.tintura.parametros.abv_objetivo
                        if analyzer.tintura.parametros
                        else None
                    ),
                    "ratio": (
                        analyzer.tintura.parametros.ratio_planta_alcohol
                        if analyzer.tintura.parametros
                        else None
                    ),
                },
            }

            self._guardar()
        except Exception as e:
            print(f"Error registrando curva: {e}")

    def comparar_con_historicos(self, analyzer: CurveAnalyzer) -> Dict:
        """
        Compara una curva actual con históricos similares.

        Args:
            analyzer: CurveAnalyzer actual

        Returns:
            Dict: Estadísticas comparativas
        """
        grupo = (
            analyzer.tintura.grupo_funcional.value
            if analyzer.tintura.grupo_funcional
            else None
        )

        # Filtrar curvas del mismo grupo
        similares = [
            data for data in self.curvas.values() if data.get("grupo") == grupo
        ]

        if not similares:
            return {"mensaje": f"No hay datos históricos de este grupo: {grupo}"}

        # Calcular estadísticas
        dias_optimos = [
            s["dia_optimo"] for s in similares if s.get("dia_optimo") is not None
        ]
        areas = [
            s["area_bajo_curva"]
            for s in similares
            if s.get("area_bajo_curva") is not None
        ]

        analisis_actual = analyzer.analizar_completo()

        resultado = {
            "grupo": grupo,
            "muestras_historicas": len(similares),
            "dias_optimo": {"actual": analisis_actual.dia_optimo_sugerido},
            "rendimiento": {"area_actual": analisis_actual.area_bajo_curva},
        }

        if dias_optimos:
            resultado["dias_optimo"]["promedio_historico"] = float(
                np.mean(dias_optimos)
            )
            resultado["dias_optimo"]["desviacion"] = (
                float(np.std(dias_optimos)) if len(dias_optimos) > 1 else 0.0
            )

        if areas:
            resultado["rendimiento"]["area_promedio_historica"] = float(np.mean(areas))
            if analisis_actual.area_bajo_curva > 0 and np.mean(areas) > 0:
                resultado["rendimiento"]["diferencia_percentual"] = float(
                    (
                        (analisis_actual.area_bajo_curva - np.mean(areas))
                        / np.mean(areas)
                        * 100
                    )
                )

        return resultado
