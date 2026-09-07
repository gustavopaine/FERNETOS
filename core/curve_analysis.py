"""
Analizador de curvas de extracción para tinturas.
Permite modelar y optimizar tiempos de maceración.
"""

import numpy as np
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field

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


from core.tintura_models import Tintura, Producto


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

        # Si no hay puntos óptimos, usar heurística por grupo funcional -
        # la heurística concreta se despacha por familia de producto (ver
        # families/<producto>/curve_rules.py). Si el producto no tiene
        # heurística registrada (ej. Campari todavía), cae al día del
        # último registro sin inventar un timing que no fue confirmado.
        if not self.registros:
            return None

        ultimo_registro = max(self.registros, key=lambda r: r.dia)
        grupo = self.tintura.grupo_funcional

        # Import perezoso: evita import circular entre core/ (genérico) y
        # families/ (específico de producto), que a su vez pueden importar
        # de core/.
        from families.fernet.curve_rules import sugerir_dia_corte_fernet
        from families.gancia.curve_rules import sugerir_dia_corte_gancia

        estrategias_dia_corte = {
            Producto.FERNET: sugerir_dia_corte_fernet,
            Producto.GANCIA: sugerir_dia_corte_gancia,
        }

        estrategia = estrategias_dia_corte.get(self.tintura.producto)
        if estrategia is not None:
            resultado = estrategia(grupo, ultimo_registro)
            if resultado is not None:
                return resultado

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
        # dia_optimo_sugerido puede ser 0 (día de corte legítimo) - un chequeo
        # truthy lo trataba como "sin día sugerido" y saltaba este bloque.
        if analisis.dia_optimo_sugerido is not None:
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
        if analisis.dia_optimo_sugerido is not None:
            # Regla general: estabilizar = óptimo + 15 días
            analisis.tiempo_estabilizacion = analisis.dia_optimo_sugerido + 15

        return analisis
