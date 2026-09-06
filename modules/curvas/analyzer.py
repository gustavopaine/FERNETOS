"""
Analizador de curvas de extracción para tinturas.
Permite modelar, visualizar y optimizar tiempos de maceración.
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.dates import DateFormatter
from typing import List, Dict, Optional, Tuple, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, field
import json
import os
from scipy import signal

# Manejo compatible de interpolación
try:
    from scipy.interpolate import make_interp_spline
except ImportError:
    from scipy.interpolate import interp1d

    # Definir función wrapper para compatibilidad
    def make_interp_spline(x, y, k=3):
        """
        Wrapper para compatibilidad con versiones antiguas de scipy.
        """
        f = interp1d(
            x,
            y,
            kind="cubic" if k == 3 else "linear",
            fill_value="extrapolate",
            bounds_error=False,
        )

        # Crear una función que devuelva los valores evaluados
        def spline(x_new):
            return f(x_new)

        return spline


import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from modules.tinturas.models import Tintura, RegistroExtraccion, GrupoFuncional, Producto


@dataclass
class PuntoInflexion:
    """Representa un punto de inflexión detectado en la curva"""

    dia: int
    intensidad: float
    pendiente_antes: float
    pendiente_despues: float
    tipo: str  # "optimo", "sobreextraccion", "saturacion"
    confianza: float  # 0-1


@dataclass
class AnalisisCurva:
    """Resultado del análisis completo de una curva"""

    tintura_id: str
    puntos_inflexion: List[PuntoInflexion] = field(default_factory=list)
    dia_optimo_sugerido: Optional[int] = None
    intensidad_optima: Optional[float] = None
    alertas: List[str] = field(default_factory=list)
    compuestos_detectados: Dict[str, List[int]] = field(
        default_factory=dict
    )  # compuesto: [dias]
    pendiente_promedio: float = 0.0
    area_bajo_curva: float = 0.0
    tiempo_estabilizacion: Optional[int] = None


class CurveAnalyzer:
    """
    Analizador de curvas de extracción.
    Detecta puntos óptimos, alerta sobre sobreextracción y modela la evolución.
    """

    def __init__(self, tintura: Tintura):
        """
        Inicializa el analizador para una tintura específica.

        Args:
            tintura: Instancia de Tintura a analizar
        """
        self.tintura = tintura
        self.registros = tintura.registros_extraccion
        self._validate_registros()

    def _validate_registros(self):
        """Valida que los registros estén completos y ordenados"""
        if not self.registros:
            return

        # Ordenar por día
        self.registros.sort(key=lambda x: x.dia)

        # Verificar que no haya huecos grandes (>3 días)
        dias = [r.dia for r in self.registros]
        for i in range(1, len(dias)):
            if dias[i] - dias[i - 1] > 3:
                print(
                    f"Advertencia: Hueco de {dias[i] - dias[i-1]} días entre día {dias[i-1]} y {dias[i]}"
                )

    def get_arrays(self) -> Tuple[np.ndarray, np.ndarray]:
        """
        Convierte registros a arrays numpy para análisis.

        Returns:
            Tuple[np.ndarray, np.ndarray]: (dias, intensidades)
        """
        if not self.registros:
            return np.array([]), np.array([])

        dias = np.array([r.dia for r in self.registros])
        intensidades = np.array([r.intensidad_estimada for r in self.registros])

        return dias, intensidades

    def calcular_pendientes(self) -> Tuple[np.ndarray, np.ndarray]:
        """
        Calcula las pendientes entre puntos consecutivos.

        Returns:
            Tuple[np.ndarray, np.ndarray]: (dias_medios, pendientes)
        """
        dias, intensidades = self.get_arrays()

        if len(dias) < 2:
            return np.array([]), np.array([])

        pendientes = np.diff(intensidades) / np.diff(dias)
        dias_medios = (dias[:-1] + dias[1:]) / 2

        return dias_medios, pendientes

    def detectar_puntos_inflexion(
        self, umbral_pendiente: float = 2.0
    ) -> List[PuntoInflexion]:
        """
        Detecta puntos de inflexión en la curva de extracción.

        Args:
            umbral_pendiente: Pendiente mínima para considerar cambio significativo

        Returns:
            List[PuntoInflexion]: Puntos de inflexión detectados
        """
        dias, intensidades = self.get_arrays()
        if len(dias) < 3:
            return []

        puntos = []

        # Calcular pendientes en cada punto (usando diferencias finitas)
        for i in range(1, len(dias) - 1):
            pend_antes = (intensidades[i] - intensidades[i - 1]) / (
                dias[i] - dias[i - 1]
            )
            pend_despues = (intensidades[i + 1] - intensidades[i]) / (
                dias[i + 1] - dias[i]
            )

            # Detectar cambio de tendencia
            if pend_antes * pend_despues < 0:  # Cambio de signo
                tipo = "inflexion"
                confianza = min(abs(pend_antes - pend_despues) / 10, 1.0)

                puntos.append(
                    PuntoInflexion(
                        dia=int(dias[i]),
                        intensidad=float(intensidades[i]),
                        pendiente_antes=float(pend_antes),
                        pendiente_despues=float(pend_despues),
                        tipo=tipo,
                        confianza=confianza,
                    )
                )

            # Detectar aplanamiento (posible punto óptimo)
            elif (
                abs(pend_despues) < umbral_pendiente
                and abs(pend_antes) > umbral_pendiente * 1.5
            ):
                puntos.append(
                    PuntoInflexion(
                        dia=int(dias[i]),
                        intensidad=float(intensidades[i]),
                        pendiente_antes=float(pend_antes),
                        pendiente_despues=float(pend_despues),
                        tipo="optimo",
                        confianza=min(1.0, 1.0 - abs(pend_despues) / umbral_pendiente),
                    )
                )

        return puntos

    def sugerir_dia_corte(self) -> Optional[int]:
        """
        Sugiere el día óptimo para cortar la maceración.

        Returns:
            Optional[int]: Día sugerido o None si no hay datos suficientes
        """
        puntos = self.detectar_puntos_inflexion()

        # Buscar puntos óptimos
        optimos = [p for p in puntos if p.tipo == "optimo"]

        if optimos:
            # Elegir el de mayor confianza
            mejor_optimo = max(optimos, key=lambda p: p.confianza)
            return mejor_optimo.dia

        # Si no hay puntos óptimos, usar heurística por grupo funcional
        if not self.registros:
            return None

        ultimo_registro = max(self.registros, key=lambda r: r.dia)

        # Heurística según grupo
        grupo = self.tintura.grupo_funcional

        if grupo == GrupoFuncional.AMARGOS_ESTRUCTURALES:
            # Amargos: entre 16-21 días, preferible antes si ya hay intensidad suficiente
            if ultimo_registro.intensidad_estimada > 80 and ultimo_registro.dia >= 16:
                return ultimo_registro.dia
            return min(21, ultimo_registro.dia + 2)

        elif grupo == GrupoFuncional.AROMATICA_ALTA:
            # Aromáticos: máximo 7 días
            return min(7, ultimo_registro.dia)

        elif grupo == GrupoFuncional.ESPECIAS_CALIDAS:
            # Especias: 14-18 días
            if ultimo_registro.dia >= 14:
                return ultimo_registro.dia
            return 14

        elif grupo == GrupoFuncional.CITRICOS:
            # Cítricos: 5-7 días
            return min(7, ultimo_registro.dia + 1)

        elif self.tintura.producto == Producto.GANCIA:
            # Dato real de receta de Gancia casero (infusión directa de
            # cáscaras cítricas, romero y clavo en alcohol+agua): 40 días
            # de maceración, agitación cada 2 días. Se aplica igual a los
            # 4 grupos de Gancia porque en esta receta todo macera junto
            # en un solo lote, no por separado como en Fernet.
            if ultimo_registro.dia >= 40:
                return ultimo_registro.dia
            return 40

        return ultimo_registro.dia

    def alertar_sobreextraccion(self) -> List[str]:
        """
        Genera alertas si se detecta sobreextracción.

        Returns:
            List[str]: Lista de alertas
        """
        alertas = []

        if len(self.registros) < 2:
            return alertas

        dias, intensidades = self.get_arrays()

        # Detectar caída de intensidad (pico y luego descenso)
        pico_idx = np.argmax(intensidades)
        if pico_idx < len(intensidades) - 1:
            intensidad_pico = intensidades[pico_idx]
            intensidad_actual = intensidades[-1]

            if intensidad_actual < intensidad_pico * 0.9:  # Caída >10%
                alertas.append(
                    f"⚠️ Posible sobreextracción: intensidad cayó de {intensidad_pico:.0f} a {intensidad_actual:.0f}"
                )

        # Detectar aparición de compuestos no deseados
        for registro in self.registros[-3:]:  # Últimos 3 registros
            if "taninos_astringentes" in registro.compuestos_detectados:
                alertas.append(
                    f"⚠️ Día {registro.dia}: aparición de taninos astringentes"
                )
            if "clorofila" in registro.compuestos_detectados:
                alertas.append(f"⚠️ Día {registro.dia}: sabor a clorofila/pasto")

        return alertas

    def modelar_curva_suave(self, puntos: int = 100) -> Tuple[np.ndarray, np.ndarray]:
        """
        Genera una curva suavizada para visualización.

        Args:
            puntos: Número de puntos para la interpolación

        Returns:
            Tuple[np.ndarray, np.ndarray]: (dias_suave, intensidades_suave)
        """
        dias, intensidades = self.get_arrays()

        if len(dias) < 4:
            return dias, intensidades

        # Interpolación spline
        dias_suave = np.linspace(min(dias), max(dias), puntos)

        try:
            spline_func = make_interp_spline(dias, intensidades, k=3)
            intensidades_suave = spline_func(dias_suave)
        except Exception as e:
            # Fallback a interpolación lineal
            print(f"Error en interpolación spline: {e}. Usando interpolación lineal.")
            intensidades_suave = np.interp(dias_suave, dias, intensidades)

        return dias_suave, intensidades_suave

    def calcular_area_bajo_curva(self) -> float:
        """
        Calcula el área bajo la curva (integral aproximada).
        Útil para comparar rendimiento entre lotes.

        Returns:
            float: Área bajo la curva
        """
        dias, intensidades = self.get_arrays()

        if len(dias) < 2:
            return 0.0

        # Integral trapezoidal - usar trapezoid (nuevo) o trapz (antiguo)
        try:
            # Para versiones recientes de numpy (1.25+)
            area = np.trapezoid(intensidades, dias)
        except AttributeError:
            try:
                # Fallback para versiones intermedias
                area = np.trapz(intensidades, dias)
            except AttributeError:
                # Implementación manual si todo falla
                area = 0.0
                for i in range(len(dias) - 1):
                    area += (
                        (intensidades[i] + intensidades[i + 1])
                        * (dias[i + 1] - dias[i])
                        / 2
                    )

        return float(area)

    def analizar_completo(self) -> AnalisisCurva:
        """
        Ejecuta un análisis completo de la curva.

        Returns:
            AnalisisCurva: Resultado del análisis
        """
        analisis = AnalisisCurva(tintura_id=self.tintura.id)

        # Detectar puntos de inflexión
        analisis.puntos_inflexion = self.detectar_puntos_inflexion()

        # Sugerir día de corte
        analisis.dia_optimo_sugerido = self.sugerir_dia_corte()

        # Calcular intensidad en día óptimo
        if analisis.dia_optimo_sugerido:
            for r in self.registros:
                if r.dia == analisis.dia_optimo_sugerido:
                    analisis.intensidad_optima = r.intensidad_estimada
                    break

        # Alertas
        analisis.alertas = self.alertar_sobreextraccion()

        # Mapeo de compuestos por día
        for r in self.registros:
            for compuesto in r.compuestos_detectados:
                if compuesto not in analisis.compuestos_detectados:
                    analisis.compuestos_detectados[compuesto] = []
                analisis.compuestos_detectados[compuesto].append(r.dia)

        # Pendiente promedio
        dias_medios, pendientes = self.calcular_pendientes()
        if len(pendientes) > 0:
            analisis.pendiente_promedio = float(np.mean(pendientes))

        # Área bajo curva
        analisis.area_bajo_curva = self.calcular_area_bajo_curva()

        # Tiempo de estabilización estimado
        if analisis.dia_optimo_sugerido:
            # Regla general: estabilizar = óptimo + 15 días
            analisis.tiempo_estabilizacion = analisis.dia_optimo_sugerido + 15

        return analisis


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
            if analisis.dia_optimo_sugerido:
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
