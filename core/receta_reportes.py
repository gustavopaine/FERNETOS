"""
Ficha tecnica exportable de un blend calculado (roadmap Fase 3, ultimo
item de "Salidas del modulo": "Exportacion de ficha tecnica de
receta, para eventual registro de marca o proveedor").

Opera sobre el `BlendResult`/`GanciaBlendResult` que ya devuelven
`FernetCalculator`/`GanciaCalculator` en sus respectivas UI de
Ensamblaje - los blends no se persisten todavia (no hay "receta
guardada" que buscar despues), asi que la ficha se genera al vuelo a
partir del ultimo calculo, no de un lookup historico. No usa el
modelo generico `core.receta_models.Receta` (sin datos reales, sin
UI - ver spec de esta fase).
"""

from datetime import datetime
from io import BytesIO
from typing import Dict, List, Optional, Tuple

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from core.tintura_models import ComposicionBotanica, Tintura
from families.campari.campari_calculator import CampariBlendResult
from families.fernet.calculator import BlendResult
from families.gancia.americano_calculator import AmericanoCalculator, VarianteExperimental
from families.gancia.gancia_calculator import GanciaBlendResult

_ESTILOS = getSampleStyleSheet()

_ESTILO_TABLA_COMPOSICION = TableStyle(
    [
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0f3460")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f2f2f2")]),
    ]
)

_ESTILO_TABLA_CLAVE_VALOR = TableStyle(
    [
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]
)


def _generar_pdf_ficha_tecnica(
    titulo: str,
    fecha_calculo: datetime,
    filas_composicion: List[Tuple[str, float, str]],
    resultado_calculado: List[Tuple[str, str]],
    version: Optional[str] = None,
    parametros: Optional[List[Tuple[str, str]]] = None,
    secciones_extra: Optional[List[Tuple[str, List[Tuple[str, str]]]]] = None,
) -> bytes:
    """
    Renderer compartido: arma el PDF (titulo + parametros objetivo
    opcionales + composicion + secciones extra opcionales + resultado
    calculado) a partir de datos ya resueltos a texto - agnostico de
    si el blend es de Fernet, Gancia, Campari o cualquier familia
    futura. Las funciones publicas por familia
    (`generar_ficha_tecnica_blend_fernet`/`_gancia`/`_campari`) arman
    estas listas a partir de su propio `resultado` tipado y llaman a
    esta funcion - evita duplicar el boilerplate de reportlab entre
    familias (la duplicacion previa ya causo un bug real: la version
    Gancia se olvido de setear `azucar_efectiva_g_l`).

    `version` y `parametros` son opcionales porque no todas las
    familias tienen esos conceptos (Campari no versiona blends ni
    tiene una nocion de "objetivo" separada de la composicion en si -
    la composicion se ingresa directa, no se resuelve contra un
    target). `secciones_extra` reemplaza el antiguo parametro fijo
    "aditivos" (usado solo por Gancia) por N secciones nombradas
    arbitrarias, para que Campari pueda tener "Botánicos (maceración)"
    e "Incorporación tardía" como bloques separados.
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    subtitulo = f"Calculado el {fecha_calculo.strftime('%Y-%m-%d %H:%M')}"
    if version:
        subtitulo = f"Versión {version} · {subtitulo}"

    contenido = [
        Paragraph(titulo, _ESTILOS["Title"]),
        Paragraph(subtitulo, _ESTILOS["Normal"]),
        Spacer(1, 0.5 * cm),
    ]

    if parametros:
        contenido.append(Paragraph("Parámetros objetivo", _ESTILOS["Heading2"]))
        tabla_parametros = Table(parametros)
        tabla_parametros.setStyle(_ESTILO_TABLA_CLAVE_VALOR)
        contenido.append(tabla_parametros)
        contenido.append(Spacer(1, 0.5 * cm))

    contenido.append(Paragraph("Composición", _ESTILOS["Heading2"]))
    encabezado = ["Componente", "Volumen (ml)", "% del blend"]
    datos_composicion = [encabezado] + [
        [nombre, f"{ml:.0f}", porcentaje] for nombre, ml, porcentaje in filas_composicion
    ]
    tabla_composicion = Table(datos_composicion, repeatRows=1)
    tabla_composicion.setStyle(_ESTILO_TABLA_COMPOSICION)
    contenido.append(tabla_composicion)
    contenido.append(Spacer(1, 0.5 * cm))

    for encabezado_seccion, filas_seccion in secciones_extra or []:
        if not filas_seccion:
            # Table([]) lanza ValueError ("must have at least a row and
            # column"). Guardado acá (no en cada caller) para que
            # cualquier familia presente o futura quede protegida sin
            # tener que acordarse de pre-filtrar - Americano lo
            # necesitaba (ingredientes_base puede quedar vacio si el
            # usuario destilda los 9 checkboxes) y no lo tenia.
            continue
        contenido.append(Paragraph(encabezado_seccion, _ESTILOS["Heading2"]))
        tabla_seccion = Table(filas_seccion)
        tabla_seccion.setStyle(_ESTILO_TABLA_CLAVE_VALOR)
        contenido.append(tabla_seccion)
        contenido.append(Spacer(1, 0.5 * cm))

    contenido.append(Paragraph("Resultado calculado", _ESTILOS["Heading2"]))
    tabla_resultado = Table(resultado_calculado)
    tabla_resultado.setStyle(_ESTILO_TABLA_CLAVE_VALOR)
    contenido.append(tabla_resultado)

    doc.build(contenido)
    return buffer.getvalue()


def _filas_composicion_fernet(
    resultado: BlendResult, tinturas: Dict[str, Tintura]
) -> List[Tuple[str, float, str]]:
    """
    Una fila por componente del blend (tinturas + alcohol base + agua)
    con su volumen y porcentaje del total. Un `tintura_id` sin
    `Tintura` correspondiente se omite - mismo criterio que ya usa la
    UI de Ensamblaje (`if t:` antes de mostrarla), no es un error de
    esta funcion sino un dato incompleto en `tinturas`.
    """
    total = resultado.composicion.volumen_total_ml
    if total <= 0:
        raise ValueError("No se puede generar la ficha de un blend con volumen total 0")

    filas = []
    for tintura_id, ml in resultado.composicion.tinturas.items():
        tintura = tinturas.get(tintura_id)
        if tintura is None:
            continue
        filas.append((tintura.nombre, ml, f"{(ml / total) * 100:.1f}%"))

    alcohol_ml = resultado.composicion.alcohol_base_ml
    agua_ml = resultado.composicion.agua_base_ml
    filas.append(("Alcohol base", alcohol_ml, f"{(alcohol_ml / total) * 100:.1f}%"))
    filas.append(("Agua", agua_ml, f"{(agua_ml / total) * 100:.1f}%"))
    return filas


def generar_ficha_tecnica_blend_fernet(
    resultado: BlendResult, tinturas: Dict[str, Tintura]
) -> bytes:
    """Ficha tecnica de un blend de Fernet ya calculado: parametros
    objetivo, composicion (tinturas resueltas a nombre) y resultado
    calculado. Devuelve los bytes del PDF."""
    filas = _filas_composicion_fernet(resultado, tinturas)

    parametros = [
        ("Volumen objetivo", f"{resultado.params.volumen_objetivo_litros:.2f} L"),
        ("ABV objetivo", f"{resultado.params.abv_objetivo:.1f}%"),
        ("Azúcar objetivo", f"{resultado.params.azucar_objetivo_gpl} g/L"),
        ("Alcohol base", f"{resultado.params.alcohol_base_abv:.1f}%"),
        ("pH objetivo", f"{resultado.params.ph_objetivo:.1f}"),
    ]
    resultado_calculado = [
        ("ABV calculado", f"{resultado.abv_calculado:.2f}%"),
        ("Azúcar efectiva", f"{resultado.azucar_efectiva_gpl} g/L"),
        ("pH estimado", f"{resultado.ph_estimado:.2f}"),
        ("Volumen real", f"{resultado.volumen_real_ml / 1000:.2f} L"),
        ("Margen de error", f"{resultado.margen_error_ml:.1f} ml"),
    ]

    return _generar_pdf_ficha_tecnica(
        f"Ficha Técnica - Fernet (blend {resultado.id})",
        resultado.fecha_calculo,
        filas,
        resultado_calculado,
        version=resultado.version,
        parametros=parametros,
    )


def _filas_composicion_gancia(
    resultado: GanciaBlendResult, tinturas: Dict[str, Tintura]
) -> List[Tuple[str, float, str]]:
    """
    Igual criterio que `_filas_composicion_fernet`: una fila por
    tintura (resuelta a nombre, omitiendo `tintura_id` desconocidos) +
    vino/alcohol de fortificacion/agua, con volumen y porcentaje sobre
    `volumen_total_ml`. Azucar/acido citrico/caramelo no son volumen
    de la base (van en la ficha como aditivos, no como % del blend) -
    mismo criterio que Fernet no mete el azucar en esta tabla.
    """
    total = resultado.composicion.volumen_total_ml
    if total <= 0:
        raise ValueError("No se puede generar la ficha de un blend con volumen total 0")

    filas = []
    for tintura_id, ml in resultado.composicion.tinturas.items():
        tintura = tinturas.get(tintura_id)
        if tintura is None:
            continue
        filas.append((tintura.nombre, ml, f"{(ml / total) * 100:.1f}%"))

    vino_ml = resultado.composicion.vino_ml
    fortificacion_ml = resultado.composicion.alcohol_fortificacion_ml
    agua_ml = resultado.composicion.agua_ml
    filas.append(("Vino base", vino_ml, f"{(vino_ml / total) * 100:.1f}%"))
    filas.append(
        ("Alcohol de fortificación", fortificacion_ml, f"{(fortificacion_ml / total) * 100:.1f}%")
    )
    filas.append(("Agua", agua_ml, f"{(agua_ml / total) * 100:.1f}%"))
    return filas


def generar_ficha_tecnica_blend_gancia(
    resultado: GanciaBlendResult, tinturas: Dict[str, Tintura]
) -> bytes:
    """Ficha tecnica de un blend de Gancia ya calculado: parametros
    objetivo, composicion (tinturas resueltas a nombre), aditivos
    (azucar/acido citrico/caramelo) y resultado calculado. Devuelve
    los bytes del PDF."""
    filas = _filas_composicion_gancia(resultado, tinturas)

    parametros = [
        ("Volumen objetivo", f"{resultado.params.volumen_objetivo_litros:.2f} L"),
        ("ABV objetivo", f"{resultado.params.abv_objetivo:.1f}%"),
        ("% Vino sobre el volumen", f"{resultado.params.vino_pct * 100:.1f}%"),
        ("Grado del vino base", f"{resultado.params.vino_abv:.1f}%"),
        ("Grado del alcohol de fortificación", f"{resultado.params.alcohol_fortificacion_abv:.1f}%"),
        ("Azúcar objetivo", f"{resultado.params.azucar_pct_wv:.1f}% p/v"),
    ]
    aditivos = [
        ("Azúcar", f"{resultado.composicion.azucar_g:.0f} g"),
        ("Ácido cítrico", f"{resultado.composicion.acido_citrico_g:.1f} g"),
        ("Caramelo E150", f"{resultado.composicion.caramelo_ml:.1f} ml"),
    ]
    resultado_calculado = [
        ("ABV calculado", f"{resultado.abv_calculado:.2f}%"),
        ("Azúcar efectiva", f"{resultado.azucar_efectiva_g_l:.1f} g/L"),
        ("Volumen real", f"{resultado.volumen_real_ml / 1000:.2f} L"),
    ]

    return _generar_pdf_ficha_tecnica(
        f"Ficha Técnica - Gancia (blend {resultado.id})",
        resultado.fecha_calculo,
        filas,
        resultado_calculado,
        version=resultado.version,
        parametros=parametros,
        secciones_extra=[("Aditivos", aditivos)],
    )


def _filas_botanicos(ingredientes: List[ComposicionBotanica]) -> List[Tuple[str, str]]:
    """Una fila por botanico: nombre + parte utilizada -> cantidad (en
    gramos si la receta usa cantidades absolutas, como Campari; en %
    de materia seca si no). `parte_utilizada == "cascara"` se muestra en
    "unidad" en vez de "g" - en la receta real de Campari las cascaras
    de citricos se cuentan como piezas enteras, no como peso (ver
    docstring de `ComposicionBotanica.gramos` y
    `tests/test_calculator_campari.py`)."""
    filas = []
    for ingrediente in ingredientes:
        nombre = f"{ingrediente.especie.replace('_', ' ').title()} ({ingrediente.parte_utilizada})"
        if ingrediente.gramos is not None:
            unidad = "unidad" if ingrediente.parte_utilizada == "cascara" else "g"
            cantidad = f"{ingrediente.gramos:.0f} {unidad}"
        else:
            cantidad = f"{ingrediente.porcentaje:.1f}%"
        filas.append((nombre, cantidad))
    return filas


def _filas_composicion_campari(resultado: CampariBlendResult) -> List[Tuple[str, float, str]]:
    """
    A diferencia de Fernet/Gancia, Campari no tiene tinturas de stock
    ni una lista abierta de componentes volumetricos - solo alcohol y
    agua aportan volumen (`volumen_final_ml`); los botanicos se miden
    en gramos y van aparte (`_filas_botanicos`), no en esta tabla de
    porcentaje de volumen.
    """
    total = resultado.composicion.volumen_final_ml
    if total <= 0:
        raise ValueError("No se puede generar la ficha de un blend con volumen total 0")

    alcohol_ml = resultado.composicion.alcohol_ml
    agua_ml = resultado.composicion.agua_ml
    return [
        (
            f"Alcohol {resultado.composicion.alcohol_abv:.0f}°",
            alcohol_ml,
            f"{(alcohol_ml / total) * 100:.1f}%",
        ),
        ("Agua", agua_ml, f"{(agua_ml / total) * 100:.1f}%"),
    ]


def generar_ficha_tecnica_blend_campari(resultado: CampariBlendResult) -> bytes:
    """
    Ficha tecnica de un blend de Campari ya calculado: base liquida
    (alcohol/agua), botanicos de maceracion e incorporacion tardia por
    separado, y resultado calculado (incluye densidad medida si se
    paso `control_calidad`). Sin `tinturas` ni `parametros objetivo`:
    Campari no usa tinturas de stock (los botanicos son nombres
    directos) ni resuelve la composicion contra un target - la
    composicion ingresada ES la receta, no un objetivo a alcanzar.
    Devuelve los bytes del PDF.
    """
    filas = _filas_composicion_campari(resultado)

    secciones_extra = []
    if resultado.composicion.ingredientes_maceracion:
        secciones_extra.append(
            ("Botánicos (maceración)", _filas_botanicos(resultado.composicion.ingredientes_maceracion))
        )
    if resultado.composicion.ingredientes_incorporacion_tardia:
        secciones_extra.append(
            (
                "Incorporación tardía",
                _filas_botanicos(resultado.composicion.ingredientes_incorporacion_tardia),
            )
        )

    resultado_calculado = [
        ("ABV calculado", f"{resultado.abv_calculado:.2f}%"),
        ("Azúcar efectiva", f"{resultado.azucar_efectiva_gpl:.1f} g/L"),
    ]
    if resultado.control_calidad is not None and resultado.control_calidad.densidad is not None:
        resultado_calculado.append(("Densidad (densímetro)", f"{resultado.control_calidad.densidad:.0f}"))

    return _generar_pdf_ficha_tecnica(
        "Ficha Técnica - Campari",
        resultado.fecha_calculo,
        filas,
        resultado_calculado,
        secciones_extra=secciones_extra,
    )


def _filas_ingredientes_americano(
    ingredientes: List[ComposicionBotanica],
) -> List[Tuple[str, str]]:
    """
    Una fila por ingrediente: nombre -> parte utilizada. A diferencia de
    `_filas_botanicos` (Campari), Americano no tiene cantidades reales
    por botanico todavia (`ComposicionBotanica.gramos`/`porcentaje`
    quedan sin usar en este modelo - ver docs/specs/
    2026-09-06-americano-variantes-experimentales.md) - la receta solo
    trackea que ingredientes estan presentes, no cuanto de cada uno.
    """
    return [
        (ingrediente.especie.replace("_", " ").title(), ingrediente.parte_utilizada)
        for ingrediente in ingredientes
    ]


def generar_ficha_tecnica_variante_americano(variante: VarianteExperimental) -> bytes:
    """
    Ficha tecnica de una VarianteExperimental de Americano ya calculada:
    base liquida (alcohol/agua), ingredientes base e ingredientes de
    variante (si hay) por separado, notas contra referencias
    comerciales (si hay), y resultado calculado (ABV, azucar efectiva).
    Sin `tinturas` (los ingredientes son nombres directos, sin stock) ni
    `parametros objetivo`/version (mismo criterio que Campari: la
    composicion ingresada ES la receta). Devuelve los bytes del PDF.
    """
    composicion = variante.composicion
    total = composicion.volumen_total_ml
    if total <= 0:
        raise ValueError("No se puede generar la ficha de una variante con volumen total 0")

    alcohol_ml = composicion.alcohol_ml
    agua_ml = composicion.agua_ml
    filas_composicion = [
        (
            f"Alcohol {composicion.alcohol_abv:.0f}°",
            alcohol_ml,
            f"{(alcohol_ml / total) * 100:.1f}%",
        ),
        ("Agua", agua_ml, f"{(agua_ml / total) * 100:.1f}%"),
    ]

    secciones_extra = [("Ingredientes base", _filas_ingredientes_americano(composicion.ingredientes_base))]
    if composicion.ingredientes_variante:
        secciones_extra.append(
            ("Ingredientes de la variante", _filas_ingredientes_americano(composicion.ingredientes_variante))
        )
    if variante.referencia_comercial:
        secciones_extra.append(("Notas vs. referencia comercial", [("Nota", variante.referencia_comercial)]))

    azucar_efectiva_g_l = AmericanoCalculator.calcular_azucar_efectiva_gpl(
        composicion.azucar_g, total
    )
    resultado_calculado = [
        ("ABV calculado", f"{variante.abv_calculado:.2f}%"),
        ("Azúcar efectiva", f"{azucar_efectiva_g_l:.0f} g/L"),
    ]

    return _generar_pdf_ficha_tecnica(
        f"Ficha Técnica - Americano (batch {variante.batch_id})",
        variante.fecha_creacion,
        filas_composicion,
        resultado_calculado,
        secciones_extra=secciones_extra,
    )
