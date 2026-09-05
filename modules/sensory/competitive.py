# -*- coding: utf-8 -*-
# Archivo en desarrollo
# M�dulo: competitive.py


class CompetitiveAnalyzer:
    def __init__(self, blend, referencia):
        self.blend = blend
        self.ref = referencia
        self.evaluaciones = []

    def analizar_ataque(self):
        """Evalúa impacto en primeros 3 segundos"""
        # Basado en inputs de usuario (1-10)
        # Algoritmo: ponderación de tinturas de alto impacto
        tinturas_alto_impacto = [
            t
            for t in self.blend.tinturas
            if t.grupo_funcional in ["citricos", "aromatica_alta"]
        ]
        ratio_impacto = (
            sum(t.volumen for t in tinturas_alto_impacto) / self.blend.volumen_total_ml
        )

        if ratio_impacto < 0.02:  # Menos de 2% del blend
            return "INSUFICIENTE - Bajo impacto inicial"
        elif ratio_impacto > 0.08:
            return "EXCESIVO - Puede saturar"
        else:
            return "OPTIMO"

    def analizar_curva_amargor(self):
        """Determina si amargor es lineal o dinámico"""
        # Input: evaluaciones secuenciales (entrada, medio, final)
        # Si diferencia entre fases < 1.5 puntos → lineal
        # Si diferencia > 3 puntos → dinámico
        pass

    def detectar_redundancias(self):
        """Identifica solapamiento aromático"""
        # Análisis de componentes botánicos
        redundancias = []
        # Ej: menta + cardamomo + romero = sobrecarga balsámica
        return redundancias

    def evaluar_superioridad(self):
        """Determina si blend supera referencia en atributos clave"""
        scores = {
            "ataque": self.comparar_atributo("ataque"),
            "complejidad": self.comparar_atributo("complejidad"),
            "persistencia": self.comparar_atributo("persistencia"),
            "equilibrio": self.comparar_atributo("equilibrio"),
        }

        superior = sum(1 for v in scores.values() if v > 0)
        if superior >= 3:
            return "SUPERIOR - Ganador en cata"
        elif superior >= 2:
            return "COMPETITIVO - Puede ganar con ajuste fino"
        else:
            return "INFERIOR - Requiere reformulación"
