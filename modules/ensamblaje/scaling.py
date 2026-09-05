class IndustrialScaling:
    def __init__(self):
        self.tinturas_stock = {}

    def proyectar_consumo(self, formula, lotes_anuales, volumen_por_lote):
        """Proyecta consumo anual de tinturas"""
        consumo = {}
        for lote in range(lotes_anuales):
            for tid, ml in formula.tinturas.items():
                consumo[tid] = consumo.get(tid, 0) + (
                    ml * volumen_por_lote / 10
                )  # escala desde 10L

        return consumo

    def simular_variacion_botanica(self, formula, año, variacion_porcentual):
        """Simula impacto de cosecha variable en perfil"""
        formula_ajustada = copy.deepcopy(formula)
        # Ajusta proporciones según data histórica de variación
        return formula_ajustada

    def calcular_costo_lote(self, formula):
        """Estima costo por lote de 10L"""
        costo = 0
        for tid, ml in formula.tinturas.items():
            t = TinturaRepository.get_by_id(tid)
            # costo_por_ml basado en materia prima y alcohol
            costo += ml * t.costo_por_ml
        return costo
