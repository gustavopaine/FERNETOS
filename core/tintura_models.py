"""
Módulo de modelos para el sistema de gestión de tinturas.
Define las estructuras de datos fundamentales para el registro y control de tinturas.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, List, Any
from enum import Enum
import uuid
import json


class Producto(Enum):
    """Producto que se está formulando con el sistema"""

    FERNET = "fernet"
    GANCIA = "gancia"
    CAMPARI = "campari"


class GrupoFuncional(Enum):
    """Grupos funcionales de tinturas según su rol en el producto"""

    # Fernet
    AMARGOS_ESTRUCTURALES = "amargos_estructurales"  # compartido con Campari
    AROMATICA_ALTA = "aromatica_alta"
    ESPECIAS_CALIDAS = "especias_calidas"
    CITRICOS = "citricos"
    CORRECTIVOS = "correctivos"  # Regaliz, clavo controlado, etc.

    # Gancia
    QUINADOS = "quinados"  # Quina/genciana - sin receta propia todavía, definido para uso futuro
    BOTANICOS_AROMATICOS = "botanicos_aromaticos"  # ej. romero
    CITRICOS_AMARGOS = "citricos_amargos"  # cáscaras: pomelo, limón, naranja - aportan amargor, compartido con Campari
    ESPECIADO_SUAVE = "especiado_suave"  # ej. clavo de olor

    # Campari
    RAICES_AROMATICAS = "raices_aromaticas"  # ej. raíz de angélica
    AMADERADOS = "amaderados"  # ej. chips de roble
    COLORANTES_NATURALES = "colorantes_naturales"  # ej. flor de hibisco

    # Compartido
    EXPERIMENTAL = "experimental"


GRUPOS_POR_PRODUCTO: Dict[Producto, List[GrupoFuncional]] = {
    Producto.FERNET: [
        GrupoFuncional.AMARGOS_ESTRUCTURALES,
        GrupoFuncional.AROMATICA_ALTA,
        GrupoFuncional.ESPECIAS_CALIDAS,
        GrupoFuncional.CITRICOS,
        GrupoFuncional.CORRECTIVOS,
        GrupoFuncional.EXPERIMENTAL,
    ],
    Producto.GANCIA: [
        GrupoFuncional.QUINADOS,
        GrupoFuncional.BOTANICOS_AROMATICOS,
        GrupoFuncional.CITRICOS_AMARGOS,
        GrupoFuncional.ESPECIADO_SUAVE,
        GrupoFuncional.EXPERIMENTAL,
    ],
    Producto.CAMPARI: [
        GrupoFuncional.AMARGOS_ESTRUCTURALES,  # ajenjo, quina, genciana, ruibarbo
        GrupoFuncional.RAICES_AROMATICAS,  # raíz de angélica
        GrupoFuncional.AMADERADOS,  # chips de roble
        GrupoFuncional.COLORANTES_NATURALES,  # flor de hibisco
        GrupoFuncional.CITRICOS_AMARGOS,  # naranja, pomelo, limón
        GrupoFuncional.EXPERIMENTAL,
    ],
}


def grupos_disponibles_para(producto_valor: Optional[str]) -> List[str]:
    """
    Valores de GrupoFuncional válidos para un producto, como strings listos
    para un dropdown de UI. `None` o "Todos" devuelve la unión de todos los
    productos, sin duplicar EXPERIMENTAL (compartido por ambos).

    Único lugar donde se calcula esta lista, para que un filtro por
    Producto que cambia las opciones de Grupo (Listado de Tinturas, Stock)
    se comporte igual en todos lados.
    """
    if not producto_valor or producto_valor == "Todos":
        grupos = [g for grupos in GRUPOS_POR_PRODUCTO.values() for g in grupos]
    else:
        grupos = GRUPOS_POR_PRODUCTO[Producto(producto_valor)]
    return list(dict.fromkeys(g.value for g in grupos))


class EstadoTintura(Enum):
    """Estados del ciclo de vida de una tintura"""

    EN_MACERACION = "en_maceracion"
    EN_ESTABILIZACION = "en_estabilizacion"
    LISTA = "lista"
    AGOTADA = "agotada"
    DESCARTADA = "descartada"


@dataclass
class ComposicionBotanica:
    """Composición de hierbas en una tintura"""

    especie: str  # Nombre científico o común estandarizado
    porcentaje: float  # Porcentaje sobre el total de materia seca (0-100)
    parte_utilizada: str  # "raiz", "corteza", "hoja", "flor", "semilla", "cascara"
    lote_origen: Optional[str] = None  # Para trazabilidad
    # Recetas que se definen en cantidades absolutas (ej. Campari: "10g de
    # ajenjo") en vez de porcentaje relativo del total - usar gramos y
    # dejar porcentaje=0.0 en ese caso, para no mezclar las dos unidades
    # en el mismo campo.
    gramos: Optional[float] = None

    def to_dict(self) -> Dict:
        return {
            "especie": self.especie,
            "porcentaje": self.porcentaje,
            "parte_utilizada": self.parte_utilizada,
            "lote_origen": self.lote_origen,
            "gramos": self.gramos,
        }


@dataclass
class ParametrosExtraccion:
    """Parámetros técnicos de la extracción"""

    abv_objetivo: float = 70.0  # % ABV del alcohol utilizado
    ratio_planta_alcohol: float = 0.2  # Ej: 0.2 para 1:5 (1kg/5L)
    temperatura_maceracion: float = 20.0  # °C
    agitacion_diaria: bool = True
    tiempo_estimado_dias: int = 21
    proteccion_luz: bool = True
    recipiente_material: str = (
        "vidrio"  # "vidrio", "acero_inox", "plastico_grado_alimenticio"
    )

    def to_dict(self) -> Dict:
        return {
            "abv_objetivo": self.abv_objetivo,
            "ratio_planta_alcohol": self.ratio_planta_alcohol,
            "temperatura_maceracion": self.temperatura_maceracion,
            "agitacion_diaria": self.agitacion_diaria,
            "tiempo_estimado_dias": self.tiempo_estimado_dias,
            "proteccion_luz": self.proteccion_luz,
            "recipiente_material": self.recipiente_material,
        }


@dataclass
class RegistroExtraccion:
    """
    Registro puntual de una cata durante la maceración.
    Permite construir la curva de extracción.
    """

    dia: int
    fecha: datetime
    intensidad_estimada: int  # 0-100 (escala sensorial)
    notas_sensoriales: str
    compuestos_detectados: List[
        str
    ]  # ["glucosidos", "taninos", "terpenos", "eugenol", etc.]
    color: str = ""  # Descripción del color
    turbidez: str = ""  # "claro", "ligera", "alta"
    aroma_descripcion: str = ""
    momento_optimo_candidato: bool = False

    def to_dict(self) -> Dict:
        return {
            "dia": self.dia,
            "fecha": self.fecha.isoformat(),
            "intensidad": self.intensidad_estimada,
            "notas": self.notas_sensoriales,
            "compuestos": self.compuestos_detectados,
            "color": self.color,
            "turbidez": self.turbidez,
            "aroma": self.aroma_descripcion,
            "optimo_candidato": self.momento_optimo_candidato,
        }


@dataclass
class ControlCalidad:
    """Resultados de controles de calidad post-maceración"""

    ph: Optional[float] = None
    densidad: Optional[float] = None  # g/ml
    turbidez_ntu: Optional[float] = None  # Unidades Nefelométricas de Turbidez
    alcohol_medido: Optional[float] = None  # % ABV real
    observaciones_filtrado: str = ""
    rendimiento_volumen_ml: Optional[float] = None  # Volumen obtenido post-filtrado

    def to_dict(self) -> Dict:
        return {
            "ph": self.ph,
            "densidad": self.densidad,
            "turbidez_ntu": self.turbidez_ntu,
            "alcohol_medido": self.alcohol_medido,
            "observaciones_filtrado": self.observaciones_filtrado,
            "rendimiento_ml": self.rendimiento_volumen_ml,
        }


@dataclass
class CompatibilidadFamilia:
    """
    Compatibilidad de una tintura con una familia de producto (fernet,
    americano, campari, etc.) y el rango de dosis recomendado para esa
    familia. Una misma tintura puede servir a varias familias, cada una
    con su propio rango - por eso vive en una lista aparte de `producto`
    (que es la familia "nativa"/original de la tintura).
    """

    familia: str
    dosis_min_ml_l: Optional[float] = None  # ml de tintura por litro de blend
    dosis_max_ml_l: Optional[float] = None
    notas: str = ""

    def to_dict(self) -> Dict:
        return {
            "familia": self.familia,
            "dosis_min_ml_l": self.dosis_min_ml_l,
            "dosis_max_ml_l": self.dosis_max_ml_l,
            "notas": self.notas,
        }


@dataclass
class Tintura:
    """
    Modelo principal de tintura.
    Representa una extracción completa con todo su ciclo de vida.
    """

    # Identificación
    id: str = field(
        default_factory=lambda: f"T-{datetime.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:4].upper()}"
    )
    nombre: str = ""
    producto: Producto = Producto.FERNET
    grupo_funcional: Optional[GrupoFuncional] = None
    version: str = "1.0.0"

    # Composición
    composicion: List[ComposicionBotanica] = field(default_factory=list)
    peso_total_materia_seca_g: float = 0.0
    volumen_alcohol_ml: float = 0.0

    # Parámetros de extracción
    parametros: Optional[ParametrosExtraccion] = None

    # Fechas y tiempos
    fecha_inicio: Optional[datetime] = None
    fecha_corte_estimada: Optional[datetime] = None
    fecha_corte_real: Optional[datetime] = None
    fecha_estabilizacion_fin: Optional[datetime] = None

    # Registros de evolución
    registros_extraccion: List[RegistroExtraccion] = field(default_factory=list)
    control_calidad: Optional[ControlCalidad] = None

    # Estado y observaciones
    estado: EstadoTintura = EstadoTintura.EN_MACERACION
    observaciones_iniciales: str = ""
    observaciones_finales: str = ""

    # Stock
    volumen_disponible_ml: float = 0.0
    ubicacion_almacen: str = ""
    notas_internas: str = ""

    # Compatibilidad con otras familias de producto (además de `producto`,
    # que es la familia nativa)
    compatibilidad_familias: List[CompatibilidadFamilia] = field(default_factory=list)

    # Metadatos
    creado_por: str = "sistema"
    tags: List[str] = field(default_factory=list)

    def __post_init__(self):
        """Validaciones y cálculos automáticos"""
        from core.validators import (
            validar_composicion_botanica,
            validar_familias_compatibles,
            validar_grupo_funcional_para_producto,
            validar_parametros_extraccion,
        )

        validar_composicion_botanica(self.composicion)
        if self.parametros is not None:
            validar_parametros_extraccion(self.parametros)
        validar_grupo_funcional_para_producto(self.producto, self.grupo_funcional)
        validar_familias_compatibles(self.compatibilidad_familias)

        if self.fecha_inicio is None:
            self.fecha_inicio = datetime.now()

        if (
            not self.fecha_corte_estimada
            and self.parametros
            and self.parametros.tiempo_estimado_dias
        ):
            from datetime import timedelta

            self.fecha_corte_estimada = self.fecha_inicio + timedelta(
                days=self.parametros.tiempo_estimado_dias
            )

    @property
    def dias_transcurridos(self) -> int:
        """Días desde inicio de maceración"""
        if not self.fecha_inicio:
            return 0

        if self.estado == EstadoTintura.EN_MACERACION:
            return max(0, (datetime.now() - self.fecha_inicio).days)
        elif self.fecha_corte_real:
            return max(0, (self.fecha_corte_real - self.fecha_inicio).days)
        return 0

    @property
    def ratio_efectivo(self) -> float:
        """Ratio planta/alcohol real (g/ml)"""
        if self.volumen_alcohol_ml > 0:
            return self.peso_total_materia_seca_g / self.volumen_alcohol_ml
        return 0.0

    def agregar_registro_extraccion(self, registro: RegistroExtraccion) -> None:
        """Añade un registro de cata a la curva de extracción"""
        self.registros_extraccion.append(registro)
        # Ordenar por día
        self.registros_extraccion.sort(key=lambda x: x.dia)

    def finalizar_maceracion(self, fecha_corte: Optional[datetime] = None) -> None:
        """Marca la tintura como lista para filtrado/estabilización"""
        self.fecha_corte_real = fecha_corte or datetime.now()
        self.estado = EstadoTintura.EN_ESTABILIZACION

    def estabilizar(
        self, dias_estabilizacion: int = 15, temperatura: float = 5.0
    ) -> None:
        """Inicia proceso de estabilización en frío"""
        from datetime import timedelta

        self.fecha_estabilizacion_fin = datetime.now() + timedelta(
            days=dias_estabilizacion
        )
        self.observaciones_finales += (
            f"\nEstabilización: {dias_estabilizacion} días a {temperatura}°C"
        )

    def marcar_como_lista(self, volumen_final_ml: float) -> None:
        """Marca la tintura como disponible para uso"""
        self.volumen_disponible_ml = volumen_final_ml
        self.estado = EstadoTintura.LISTA
        self.fecha_estabilizacion_fin = datetime.now()

    def to_dict(self) -> Dict:
        """Exporta a diccionario para serialización JSON/YAML"""
        return {
            "id": self.id,
            "nombre": self.nombre,
            "producto": self.producto.value if self.producto else None,
            "grupo_funcional": (
                self.grupo_funcional.value if self.grupo_funcional else None
            ),
            "version": self.version,
            "composicion": [c.to_dict() for c in self.composicion],
            "peso_materia_seca_g": self.peso_total_materia_seca_g,
            "volumen_alcohol_ml": self.volumen_alcohol_ml,
            "parametros": self.parametros.to_dict() if self.parametros else None,
            "fecha_inicio": (
                self.fecha_inicio.isoformat() if self.fecha_inicio else None
            ),
            "fecha_corte_estimada": (
                self.fecha_corte_estimada.isoformat()
                if self.fecha_corte_estimada
                else None
            ),
            "fecha_corte_real": (
                self.fecha_corte_real.isoformat() if self.fecha_corte_real else None
            ),
            "fecha_estabilizacion_fin": (
                self.fecha_estabilizacion_fin.isoformat()
                if self.fecha_estabilizacion_fin
                else None
            ),
            "registros": [r.to_dict() for r in self.registros_extraccion],
            "control_calidad": (
                self.control_calidad.to_dict() if self.control_calidad else None
            ),
            "estado": self.estado.value,
            "observaciones": self.observaciones_iniciales,
            "volumen_disponible_ml": self.volumen_disponible_ml,
            "ubicacion": self.ubicacion_almacen,
            "compatibilidad_familias": [
                c.to_dict() for c in self.compatibilidad_familias
            ],
            "tags": self.tags,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "Tintura":
        """Crea una instancia desde diccionario"""
        # Esta implementación requeriría mapeo más complejo
        # Versión simplificada:
        tintura = cls()
        for key, value in data.items():
            if hasattr(tintura, key):
                setattr(tintura, key, value)
        return tintura


@dataclass
class LoteTintura:
    """Lote de producción de una tintura (para trazabilidad)"""

    id: str = field(
        default_factory=lambda: f"LT-{datetime.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:4]}"
    )
    tintura_id: str = ""
    fecha_produccion: datetime = field(default_factory=datetime.now)
    volumen_producido_ml: float = 0.0
    proveedor_materia_prima: str = ""
    certificado_calidad: Optional[str] = None  # Ruta a archivo
    notas_produccion: str = ""
