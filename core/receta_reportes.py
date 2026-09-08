"""
Ficha tecnica exportable de un blend calculado (roadmap Fase 3, ultimo
item de "Salidas del modulo": "Exportacion de ficha tecnica de
receta, para eventual registro de marca o proveedor").

Opera sobre el `BlendResult` que ya devuelve `FernetCalculator` en la
UI de Ensamblaje - los blends no se persisten todavia (no hay
"receta guardada" que buscar despues), asi que la ficha se genera al
vuelo a partir del ultimo calculo, no de un lookup historico. No usa
el modelo generico `core.receta_models.Receta` (sin datos reales, sin
UI - ver spec de esta fase).
"""

from io import BytesIO
from typing import Dict, List, Tuple

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from core.tintura_models import Tintura
from families.fernet.calculator import BlendResult

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

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    contenido = [
        Paragraph(f"Ficha Técnica - Fernet (blend {resultado.id})", _ESTILOS["Title"]),
        Paragraph(
            f"Versión {resultado.version} · Calculado el "
            f"{resultado.fecha_calculo.strftime('%Y-%m-%d %H:%M')}",
            _ESTILOS["Normal"],
        ),
        Spacer(1, 0.5 * cm),
        Paragraph("Parámetros objetivo", _ESTILOS["Heading2"]),
    ]

    parametros = Table(
        [
            ["Volumen objetivo", f"{resultado.params.volumen_objetivo_litros:.2f} L"],
            ["ABV objetivo", f"{resultado.params.abv_objetivo:.1f}%"],
            ["Azúcar objetivo", f"{resultado.params.azucar_objetivo_gpl} g/L"],
            ["Alcohol base", f"{resultado.params.alcohol_base_abv:.1f}%"],
            ["pH objetivo", f"{resultado.params.ph_objetivo:.1f}"],
        ]
    )
    parametros.setStyle(_ESTILO_TABLA_CLAVE_VALOR)
    contenido.append(parametros)
    contenido.append(Spacer(1, 0.5 * cm))

    contenido.append(Paragraph("Composición", _ESTILOS["Heading2"]))
    encabezado = ["Componente", "Volumen (ml)", "% del blend"]
    datos_composicion = [encabezado] + [
        [nombre, f"{ml:.0f}", porcentaje] for nombre, ml, porcentaje in filas
    ]
    tabla_composicion = Table(datos_composicion, repeatRows=1)
    tabla_composicion.setStyle(_ESTILO_TABLA_COMPOSICION)
    contenido.append(tabla_composicion)
    contenido.append(Spacer(1, 0.5 * cm))

    contenido.append(Paragraph("Resultado calculado", _ESTILOS["Heading2"]))
    resultado_calculado = Table(
        [
            ["ABV calculado", f"{resultado.abv_calculado:.2f}%"],
            ["Azúcar efectiva", f"{resultado.azucar_efectiva_gpl} g/L"],
            ["pH estimado", f"{resultado.ph_estimado:.2f}"],
            ["Volumen real", f"{resultado.volumen_real_ml / 1000:.2f} L"],
            ["Margen de error", f"{resultado.margen_error_ml:.1f} ml"],
        ]
    )
    resultado_calculado.setStyle(_ESTILO_TABLA_CLAVE_VALOR)
    contenido.append(resultado_calculado)

    doc.build(contenido)
    return buffer.getvalue()
